from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db, User, Node, InputRecord, SystemLog, beijing_now
from app.models import NodeCheckResult, BulkNodeCheck, NodeStatus, LogType
from app.auth import get_current_active_user
from app.monitoring.node_checker import NodeChecker

router = APIRouter()
node_checker = NodeChecker()

@router.post("/check", response_model=List[NodeCheckResult])
async def check_nodes(
    check_request: BulkNodeCheck,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检测节点状态"""
    # 获取要检测的节点（跳过禁用节点）
    if check_request.node_ids:
        nodes = db.query(Node).join(InputRecord).filter(
            Node.id.in_(check_request.node_ids),
            InputRecord.user_id == current_user.id,
            InputRecord.is_active == True,
            Node.status != 'disabled'  # 跳过禁用节点
        ).all()
    else:
        # 检测所有节点（跳过禁用节点）
        nodes = db.query(Node).join(InputRecord).filter(
            InputRecord.user_id == current_user.id,
            InputRecord.is_active == True,
            Node.status != 'disabled'  # 跳过禁用节点
        ).all()
    
    if not nodes:
        return []
    
    # 执行检测
    results = []
    for node in nodes:
        try:
            result = await node_checker.check_node(node)
            results.append(result)
            
            # 更新节点状态和延迟
            node.status = result.status
            if result.ping_latency is not None:
                node.ping_latency = result.ping_latency
            if result.packet_loss is not None:
                node.packet_loss = result.packet_loss
            node.last_check = beijing_now()
            
            print(f"节点 {node.id} 检测结果: 状态={result.status}, 延迟={result.ping_latency}ms")
            
        except Exception as e:
            # 记录错误结果
            result = NodeCheckResult(
                node_id=node.id,
                status=NodeStatus.ERROR,
                error_message=str(e)
            )
            results.append(result)
            
            # 更新错误状态
            node.status = NodeStatus.ERROR
            node.last_check = beijing_now()
    
    # 保存更新
    db.commit()
    
    # 记录检测日志
    log = SystemLog(
        log_type=LogType.NODE_CHECK,
        message=f"用户 {current_user.username} 检测了 {len(nodes)} 个节点",
        details=f"检测结果: {len([r for r in results if r.status == NodeStatus.ACTIVE])} 个活跃, {len([r for r in results if r.status == NodeStatus.INACTIVE])} 个不活跃"
    )
    db.add(log)
    db.commit()
    
    return results

@router.post("/check/all")
async def check_all_nodes(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """检测所有节点"""
    # 获取用户所有节点（跳过禁用节点）
    nodes = db.query(Node).join(InputRecord).filter(
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True,
        Node.status != 'disabled'  # 跳过禁用节点
    ).all()
    
    if not nodes:
        return {"message": "没有节点需要检测"}
    
    # 异步执行检测
    background_tasks.add_task(check_all_nodes_background, [node.id for node in nodes], current_user.id)
    
    return {"message": f"已开始检测 {len(nodes)} 个节点"}

async def check_all_nodes_background(node_ids: List[int], user_id: int):
    """后台检测所有节点"""
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        nodes = db.query(Node).join(InputRecord).filter(
            Node.id.in_(node_ids),
            InputRecord.user_id == user_id,
            InputRecord.is_active == True,
            Node.status != 'disabled'  # 跳过禁用节点
        ).all()
        
        for node in nodes:
            try:
                result = await node_checker.check_node(node)
                
                # 更新节点状态
                node.status = result.status
                node.ping_latency = result.ping_latency
                node.packet_loss = result.packet_loss
                node.last_check = beijing_now()
                
            except Exception as e:
                node.status = NodeStatus.ERROR
                node.last_check = beijing_now()
        
        db.commit()
        
        # 记录检测日志
        log = SystemLog(
            log_type=LogType.NODE_CHECK,
            message=f"后台检测了 {len(nodes)} 个节点",
            details=f"检测完成时间: {datetime.utcnow()}"
        )
        db.add(log)
        db.commit()
        
    finally:
        db.close()

@router.get("/status/{node_id}")
async def get_node_status(
    node_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取节点状态"""
    node = db.query(Node).join(InputRecord).filter(
        Node.id == node_id,
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True
    ).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    
    return {
        "node_id": node.id,
        "name": node.name,
        "status": node.status,
        "ping_latency": node.ping_latency,
        "packet_loss": node.packet_loss,
        "last_check": node.last_check
    }

@router.get("/stats")
async def get_monitoring_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取监控统计"""
    # 获取用户所有节点
    nodes = db.query(Node).join(InputRecord).filter(
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True
    ).all()
    
    total_nodes = len(nodes)
    active_nodes = len([n for n in nodes if n.status == NodeStatus.ACTIVE])
    inactive_nodes = len([n for n in nodes if n.status == NodeStatus.INACTIVE])
    error_nodes = len([n for n in nodes if n.status == NodeStatus.ERROR])
    disabled_nodes = len([n for n in nodes if n.status == 'disabled'])
    unknown_nodes = len([n for n in nodes if n.status == NodeStatus.UNKNOWN])
    
    # 计算平均延迟（只计算非禁用节点）
    latencies = [n.ping_latency for n in nodes if n.ping_latency is not None and n.status != 'disabled']
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
    return {
        "total_nodes": total_nodes,
        "active_nodes": active_nodes,
        "inactive_nodes": inactive_nodes,
        "error_nodes": error_nodes,
        "disabled_nodes": disabled_nodes,
        "unknown_nodes": unknown_nodes,
        "avg_latency": round(avg_latency, 2),
        "last_updated": beijing_now()
    }

@router.get("/logs")
async def get_monitoring_logs(
    skip: int = 0,
    limit: int = 100,
    log_type: Optional[LogType] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取监控日志"""
    query = db.query(SystemLog)
    
    if log_type:
        query = query.filter(SystemLog.log_type == log_type)
    
    logs = query.order_by(SystemLog.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "log_type": log.log_type,
            "message": log.message,
            "details": log.details,
            "created_at": log.created_at
        }
        for log in logs
    ]