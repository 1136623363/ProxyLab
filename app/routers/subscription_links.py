from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import json

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)
from app.database import get_db, User, SubscriptionLink, Node, InputRecord
from app.database import generate_unique_link_id
from app.auth import get_current_active_user
from app.output.output_factory import OutputFactory
from app.models import SubscriptionOutput, OutputFormat, NodeFilter

router = APIRouter()
output_factory = OutputFactory()

@router.post("/", response_model=dict)
async def create_subscription_link(
    link_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建订阅链接"""
    try:
        # 生成唯一链接ID
        link_id = generate_unique_link_id()
        
        # 创建订阅链接记录
        subscription_link = SubscriptionLink(
            user_id=current_user.id,
            link_id=link_id,
            name=link_data.get('name', f'订阅链接_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
            description=link_data.get('description', ''),
            output_format=link_data.get('output_format', 'clash'),
            filter_config=json.dumps(link_data.get('filter_config', {})) if link_data.get('filter_config') else None,
            is_active=True,
            created_at=beijing_now(),
            updated_at=beijing_now()
        )
        
        db.add(subscription_link)
        db.commit()
        db.refresh(subscription_link)
        
        # 生成访问URL
        base_url = "http://localhost:8001"  # 可以从配置中获取
        access_url = f"{base_url}/api/subscription/{link_id}"
        
        return {
            "id": subscription_link.id,
            "link_id": subscription_link.link_id,
            "name": subscription_link.name,
            "description": subscription_link.description,
            "output_format": subscription_link.output_format,
            "access_url": access_url,
            "created_at": subscription_link.created_at
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建订阅链接失败: {str(e)}")

@router.get("/", response_model=List[dict])
async def get_subscription_links(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的订阅链接列表"""
    links = db.query(SubscriptionLink).filter(
        SubscriptionLink.user_id == current_user.id
    ).order_by(SubscriptionLink.created_at.desc()).all()
    
    result = []
    for link in links:
        base_url = "http://localhost:8001"  # 可以从配置中获取
        access_url = f"{base_url}/api/subscription/{link.link_id}"
        
        result.append({
            "id": link.id,
            "link_id": link.link_id,
            "name": link.name,
            "description": link.description,
            "output_format": link.output_format,
            "is_active": link.is_active,
            "access_count": link.access_count,
            "last_accessed": link.last_accessed,
            "access_url": access_url,
            "created_at": link.created_at,
            "updated_at": link.updated_at
        })
    
    return result

@router.get("/{link_id}", response_model=dict)
async def get_subscription_link(
    link_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定订阅链接"""
    link = db.query(SubscriptionLink).filter(
        SubscriptionLink.link_id == link_id,
        SubscriptionLink.user_id == current_user.id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="订阅链接不存在")
    
    base_url = "http://localhost:8001"  # 可以从配置中获取
    access_url = f"{base_url}/api/subscription/{link.link_id}"
    
    return {
        "id": link.id,
        "link_id": link.link_id,
        "name": link.name,
        "description": link.description,
        "output_format": link.output_format,
        "filter_config": json.loads(link.filter_config) if link.filter_config else {},
        "is_active": link.is_active,
        "access_count": link.access_count,
        "last_accessed": link.last_accessed,
        "access_url": access_url,
        "created_at": link.created_at,
        "updated_at": link.updated_at
    }

@router.put("/{link_id}", response_model=dict)
async def update_subscription_link(
    link_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新订阅链接"""
    link = db.query(SubscriptionLink).filter(
        SubscriptionLink.link_id == link_id,
        SubscriptionLink.user_id == current_user.id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="订阅链接不存在")
    
    # 更新字段
    if 'name' in update_data:
        link.name = update_data['name']
    if 'description' in update_data:
        link.description = update_data['description']
    if 'output_format' in update_data:
        link.output_format = update_data['output_format']
    if 'filter_config' in update_data:
        link.filter_config = json.dumps(update_data['filter_config']) if update_data['filter_config'] else None
    if 'is_active' in update_data:
        link.is_active = update_data['is_active']
    
    link.updated_at = beijing_now()
    
    db.commit()
    db.refresh(link)
    
    base_url = "http://localhost:8001"  # 可以从配置中获取
    access_url = f"{base_url}/api/subscription/{link.link_id}"
    
    return {
        "id": link.id,
        "link_id": link.link_id,
        "name": link.name,
        "description": link.description,
        "output_format": link.output_format,
        "filter_config": json.loads(link.filter_config) if link.filter_config else {},
        "is_active": link.is_active,
        "access_count": link.access_count,
        "last_accessed": link.last_accessed,
        "access_url": access_url,
        "created_at": link.created_at,
        "updated_at": link.updated_at
    }

@router.delete("/{link_id}")
async def delete_subscription_link(
    link_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除订阅链接"""
    link = db.query(SubscriptionLink).filter(
        SubscriptionLink.link_id == link_id,
        SubscriptionLink.user_id == current_user.id
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="订阅链接不存在")
    
    db.delete(link)
    db.commit()
    
    return {"message": "订阅链接删除成功"}

@router.get("/{link_id}/content")
async def get_subscription_content(
    link_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """获取订阅内容（公开访问，无需认证）"""
    link = db.query(SubscriptionLink).filter(
        SubscriptionLink.link_id == link_id,
        SubscriptionLink.is_active == True
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="订阅链接不存在或已禁用")
    
    # 更新访问统计
    link.access_count += 1
    link.last_accessed = beijing_now()
    db.commit()
    
    # 获取用户的所有节点
    nodes = db.query(Node).join(InputRecord).filter(
        InputRecord.user_id == link.user_id,
        InputRecord.is_active == True
    ).all()
    
    # 应用过滤器
    if link.filter_config:
        filter_config = json.loads(link.filter_config)
        nodes = apply_node_filter(nodes, filter_config)
    
    # 转换为字典格式
    nodes_data = []
    for node in nodes:
        node_data = {
            'name': node.name,
            'type': node.node_type,
            'address': node.address,
            'port': node.port,
            'encryption': node.encryption,
            'password': node.password,
            'uuid': node.uuid,
            'alter_id': node.alter_id,
            'network': node.network,
            'path': node.path,
            'host': node.host,
            'tls': node.tls,
            'sni': node.sni,
            'country': node.country,
            'region': node.region
        }
        nodes_data.append(node_data)
    
    # 生成订阅内容
    generator = output_factory.get_generator(link.output_format)
    if not generator:
        raise HTTPException(status_code=400, detail="不支持的输出格式")
    
    content = generator.generate(nodes_data)
    
    return content

def apply_node_filter(nodes: List[Node], filter_config: dict) -> List[Node]:
    """应用节点过滤器"""
    filtered_nodes = nodes
    
    if filter_config.get('countries'):
        filtered_nodes = [n for n in filtered_nodes if n.country in filter_config['countries']]
    
    if filter_config.get('regions'):
        filtered_nodes = [n for n in filtered_nodes if n.region in filter_config['regions']]
    
    if filter_config.get('node_types'):
        filtered_nodes = [n for n in filtered_nodes if n.node_type in filter_config['node_types']]
    
    if filter_config.get('max_latency') is not None:
        filtered_nodes = [n for n in filtered_nodes if n.ping_latency is None or n.ping_latency <= filter_config['max_latency']]
    
    if filter_config.get('include_keywords'):
        filtered_nodes = [
            n for n in filtered_nodes
            if any(keyword.lower() in n.name.lower() for keyword in filter_config['include_keywords'])
        ]
    
    if filter_config.get('exclude_keywords'):
        filtered_nodes = [
            n for n in filtered_nodes
            if not any(keyword.lower() in n.name.lower() for keyword in filter_config['exclude_keywords'])
        ]
    
    return filtered_nodes
