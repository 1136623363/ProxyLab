from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from app.database import get_db, User, Node, InputRecord
from app.models import Node as NodeModel, NodeUpdate, NodeStatus, NodeType, NodeFilter
from app.auth import get_current_active_user
from app.cache import cached, invalidate_cache_pattern

router = APIRouter()

@router.get("/")
async def get_nodes(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=1000, description="每页数量"),
    node_type: Optional[str] = Query(None, description="节点类型"),
    country: Optional[str] = Query(None, description="国家"),
    region: Optional[str] = Query(None, description="地区"),
    status: Optional[str] = Query(None, description="状态"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的节点列表"""
    query = db.query(Node).join(InputRecord).filter(
        InputRecord.user_id == current_user.id
        # 移除 is_active == True 过滤，显示所有节点包括禁用订阅的节点
    )
    
    # 应用过滤器
    if node_type and node_type.strip():
        query = query.filter(Node.node_type == node_type)
    
    if country and country.strip():
        query = query.filter(Node.country == country)
    
    if region and region.strip():
        query = query.filter(Node.region == region)
    
    if status and status.strip():
        query = query.filter(Node.status == status)
    
    if search and search.strip():
        query = query.filter(
            or_(
                Node.name.contains(search),
                Node.address.contains(search),
                Node.country.contains(search),
                Node.region.contains(search)
            )
        )
    
    # 获取总数
    total = query.count()
    
    # 分页 - 将page和pageSize转换为skip和limit
    skip = (page - 1) * pageSize
    limit = pageSize
    
    # 优化查询：预加载关联数据，减少N+1查询
    nodes = query.options(
        # 预加载关联的InputRecord数据
    ).offset(skip).limit(limit).all()
    
    return {
        "data": nodes,
        "total": total,
        "page": page,
        "pageSize": pageSize,
        "totalPages": (total + pageSize - 1) // pageSize
    }

@router.get("/{node_id}", response_model=NodeModel)
async def get_node(
    node_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定节点"""
    node = db.query(Node).join(InputRecord).filter(
        Node.id == node_id,
        InputRecord.user_id == current_user.id
        # 移除 is_active == True 过滤，允许访问禁用订阅的节点
    ).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    
    return node

@router.put("/{node_id}", response_model=NodeModel)
async def update_node(
    node_id: int,
    node_update: NodeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新节点信息"""
    node = db.query(Node).join(InputRecord).filter(
        Node.id == node_id,
        InputRecord.user_id == current_user.id
        # 移除 is_active == True 过滤，允许更新禁用订阅的节点
    ).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    
    # 更新节点信息
    update_data = node_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(node, field, value)
    
    db.commit()
    db.refresh(node)
    
    # 清除相关缓存
    invalidate_cache_pattern("node_stats")
    invalidate_cache_pattern("nodes_list")
    
    return node

@router.delete("/{node_id}")
async def delete_node(
    node_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除节点"""
    node = db.query(Node).join(InputRecord).filter(
        Node.id == node_id,
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True
    ).first()
    
    if not node:
        raise HTTPException(status_code=404, detail="节点不存在")
    
    db.delete(node)
    db.commit()
    
    return {"message": "节点删除成功"}

@router.get("/stats/summary")
async def get_node_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取节点统计信息（使用预计算数据）"""
    from app.services.stats_service import StatsService
    
    # 获取缓存的统计数据
    stats = StatsService.get_cached_stats(db, current_user.id)
    
    return {
        "total_nodes": stats['total_nodes'],
        "active_nodes": stats['active_nodes'],
        "inactive_nodes": stats['inactive_nodes'],
        "error_nodes": stats['error_nodes'],
        "unknown_nodes": stats['unknown_nodes'],
        "avg_latency": stats['avg_latency'],
        "min_latency": stats['min_latency'],
        "max_latency": stats['max_latency'],
        "type_distribution": stats['type_distribution'],
        "country_distribution": stats['country_distribution'],
        "last_updated": stats['last_updated']
    }

@router.post("/filter", response_model=List[NodeModel])
async def filter_nodes(
    node_filter: NodeFilter,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """根据条件过滤节点"""
    query = db.query(Node).join(InputRecord).filter(
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True
    )
    
    # 应用过滤条件
    if node_filter.node_types:
        query = query.filter(Node.node_type.in_(node_filter.node_types))
    
    if node_filter.countries:
        query = query.filter(Node.country.in_(node_filter.countries))
    
    if node_filter.regions:
        query = query.filter(Node.region.in_(node_filter.regions))
    
    if node_filter.status:
        query = query.filter(Node.status == node_filter.status)
    
    
    if node_filter.max_latency is not None:
        query = query.filter(Node.ping_latency <= node_filter.max_latency)
    
    if node_filter.include_keywords:
        keyword_conditions = []
        for keyword in node_filter.include_keywords:
            keyword_conditions.append(
                or_(
                    Node.name.contains(keyword),
                    Node.address.contains(keyword),
                    Node.country.contains(keyword),
                    Node.region.contains(keyword)
                )
            )
        query = query.filter(and_(*keyword_conditions))
    
    if node_filter.exclude_keywords:
        for keyword in node_filter.exclude_keywords:
            query = query.filter(
                and_(
                    ~Node.name.contains(keyword),
                    ~Node.address.contains(keyword),
                    ~Node.country.contains(keyword),
                    ~Node.region.contains(keyword)
                )
            )
    
    # 排序
    if hasattr(node_filter, 'sort_by'):
        if node_filter.sort_by == "latency":
            query = query.order_by(Node.ping_latency.asc())
        elif node_filter.sort_by == "name":
            query = query.order_by(Node.name.asc())
        elif node_filter.sort_by == "created_at":
            query = query.order_by(Node.created_at.desc())
        else:
            query = query.order_by(Node.created_at.desc())
    else:
        query = query.order_by(Node.created_at.desc())
    
    # 分页
    nodes = query.offset(node_filter.skip).limit(node_filter.limit).all()
    return nodes

@router.get("/countries/list")
async def get_countries(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取国家列表"""
    countries = db.query(Node.country).join(InputRecord).filter(
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True,
        Node.country.isnot(None)
    ).distinct().all()
    
    return [country[0] for country in countries if country[0]]

@router.get("/regions/list")
async def get_regions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取地区列表"""
    regions = db.query(Node.region).join(InputRecord).filter(
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True,
        Node.region.isnot(None)
    ).distinct().all()
    
    return [region[0] for region in regions if region[0]]

@router.post("/", response_model=NodeModel)
async def create_node(
    node_data: dict,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """手动添加节点"""
    # 首先创建一个输入记录
    input_record = InputRecord(
        user_id=current_user.id,
        input_type="manual",
        content="手动添加的节点",
        notes=node_data.get('notes', '')
    )
    db.add(input_record)
    db.commit()
    db.refresh(input_record)
    
    # 创建节点
    node = Node(
        input_record_id=input_record.id,
        name=node_data.get('name', ''),
        node_type=node_data.get('node_type', 'v2ray'),
        address=node_data.get('address', ''),
        port=node_data.get('port', 443),
        encryption=node_data.get('encryption', ''),
        password=node_data.get('password', ''),
        uuid=node_data.get('uuid', ''),
        alter_id=node_data.get('alter_id', 0),
        network=node_data.get('network', ''),
        path=node_data.get('path', ''),
        host=node_data.get('host', ''),
        tls=node_data.get('tls', False),
        sni=node_data.get('sni', ''),
        country=node_data.get('country', ''),
        region=node_data.get('region', ''),
        status='unknown'
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    
    return node