from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import qrcode
import io
import base64
from app.database import get_db, User, Node, InputRecord
from app.models import SubscriptionOutput, OutputFormat, NodeFilter
from app.auth import get_current_active_user, get_current_user_optional
from app.output.output_factory import OutputFactory
from app.output.enhanced_clash_generator import EnhancedClashGenerator
from app.cache import cached, invalidate_cache_pattern

router = APIRouter()
output_factory = OutputFactory()

def detect_client_format(user_agent: str) -> str:
    """根据User-Agent检测客户端类型"""
    if not user_agent:
        return "clash"  # 默认返回Clash格式
    
    user_agent = user_agent.lower()
    
    # Clash客户端检测
    if any(keyword in user_agent for keyword in [
        "clash", "clashx", "clashx pro", "clash for windows", 
        "clash verge", "clash meta", "stash", "mihomo"
    ]):
        return "clash"
    
    # V2Ray客户端检测
    if any(keyword in user_agent for keyword in [
        "v2ray", "v2rayn", "v2rayu", "v2rayng", "v2rayx",
        "qv2ray", "v2ray-core", "v2fly"
    ]):
        return "v2rayn"
    
    # Shadowrocket客户端检测
    if any(keyword in user_agent for keyword in [
        "shadowrocket", "shadowrocket/ios", "shadowrocket/mac"
    ]):
        return "clash"  # Shadowrocket也支持Clash格式
    
    # Quantumult X客户端检测
    if any(keyword in user_agent for keyword in [
        "quantumult", "quantumult x", "quantumultx"
    ]):
        return "clash"  # Quantumult X也支持Clash格式
    
    # Surge客户端检测
    if any(keyword in user_agent for keyword in [
        "surge", "surge ios", "surge mac"
    ]):
        return "clash"  # Surge也支持Clash格式
    
    # 默认返回Clash格式（兼容性最好）
    return "clash"

def apply_filters(nodes, countries: Optional[str], node_types: Optional[str], max_latency: Optional[float]):
    """应用查询参数过滤器"""
    if countries:
        country_list = [c.strip() for c in countries.split(',')]
        nodes = [n for n in nodes if n.country in country_list]
    
    if node_types:
        type_list = [t.strip() for t in node_types.split(',')]
        nodes = [n for n in nodes if n.node_type in type_list]
    
    if max_latency is not None:
        nodes = [n for n in nodes if n.ping_latency is None or n.ping_latency <= max_latency]
    
    return nodes

def convert_nodes_to_dict(nodes):
    """将节点对象转换为字典格式"""
    nodes_data = []
    for node in nodes:
        node_data = {
            'name': node.name,
            'type': node.node_type,  # 用于其他生成器
            'node_type': node.node_type,  # 用于 enhanced_clash 生成器
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
    return nodes_data

def generate_subscription_content(nodes_data, format_type: str) -> str:
    """生成订阅内容"""
    if format_type == 'clash_enhanced':
        generator = EnhancedClashGenerator()
        return generator.generate(nodes_data)
    else:
        # 将字符串格式转换为枚举
        format_enum = OutputFormat(format_type) if format_type in ['clash', 'v2rayn', 'raw'] else OutputFormat.CLASH
        generator = output_factory.get_generator(format_enum)
        if not generator:
            return "# 不支持的输出格式"
        return generator.generate(nodes_data)

def get_empty_config(format_type: str) -> PlainTextResponse:
    """获取空配置"""
    if format_type == 'clash' or format_type == 'clash_enhanced':
        empty_config = {
            'proxies': [],
            'proxy-groups': [],
            'rules': []
        }
        import yaml
        content = yaml.dump(empty_config, default_flow_style=False, allow_unicode=True)
        return PlainTextResponse(content, media_type="text/plain; charset=utf-8")
    else:
        content = "# 暂无可用节点"
        return PlainTextResponse(content, media_type="text/plain; charset=utf-8")

def get_content_type(format_type: str) -> str:
    """获取相应的Content-Type"""
    if format_type in ['clash', 'clash_enhanced']:
        return "text/plain; charset=utf-8"
    elif format_type == 'v2rayn':
        return "text/plain; charset=utf-8"
    else:
        return "text/plain; charset=utf-8"

@router.get("/formats")
async def get_output_formats():
    """获取支持的输出格式列表"""
    return {
        "formats": [
            {
                "value": "universal",
                "label": "万能订阅链接",
                "description": "自动检测客户端类型，支持 Clash、V2Ray、Shadowrocket 等",
                "is_universal": True
            },
            {
                "value": "clash",
                "label": "Clash",
                "description": "Clash 配置文件格式"
            },
            {
                "value": "clash_enhanced",
                "label": "Clash Enhanced",
                "description": "增强版 Clash 配置文件格式（包含高级规则和DNS配置）"
            },
            {
                "value": "v2rayn",
                "label": "V2rayN",
                "description": "V2rayN 配置文件格式"
            },
            {
                "value": "raw",
                "label": "原始格式",
                "description": "原始订阅链接格式"
            }
        ]
    }

@router.post("/subscription")
async def generate_subscription(
    output_config: SubscriptionOutput,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成订阅内容"""
    # 获取用户所有节点（移除分组相关逻辑）
    nodes = db.query(Node).join(InputRecord).filter(
        InputRecord.user_id == current_user.id,
        InputRecord.is_active == True
    ).all()
    
    # 应用过滤器
    if output_config.filter:
        nodes = apply_node_filter(nodes, output_config.filter)
    
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
    generator = output_factory.get_generator(output_config.format)
    if not generator:
        raise HTTPException(status_code=400, detail="不支持的输出格式")
    
    content = generator.generate(nodes_data)
    
    # 生成配置链接
    import base64
    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    # 生成完整的配置链接，包含域名和端口
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    config_url = f"{base_url}/api/output/subscription/{output_config.format}?token={encoded_content}"
    
    return {
        "content": content, 
        "format": output_config.format, 
        "node_count": len(nodes_data),
        "config_url": config_url
    }

@router.get("/subscription")
async def get_universal_subscription(
    request: Request,
    user_id: Optional[int] = None,
    countries: Optional[str] = None,
    node_types: Optional[str] = None,
    max_latency: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """万能订阅链接 - 自动检测客户端类型并返回相应格式"""
    try:
        # 检测客户端类型
        user_agent = request.headers.get("user-agent", "").lower()
        format_type = detect_client_format(user_agent)
        
        # 获取节点数据
        if user_id:
            # 根据用户ID获取节点
            nodes = db.query(Node).join(InputRecord).filter(
                InputRecord.user_id == user_id,
                InputRecord.is_active == True
            ).all()
        else:
            # 获取所有公开的节点
            nodes = db.query(Node).join(InputRecord).filter(
                InputRecord.is_active == True
            ).all()
        
        # 如果没有节点，返回空的配置
        if not nodes:
            return get_empty_config(format_type)
        
        # 应用查询参数过滤器
        nodes = apply_filters(nodes, countries, node_types, max_latency)
        
        # 转换为字典格式
        nodes_data = convert_nodes_to_dict(nodes)
        
        # 生成订阅内容
        content = generate_subscription_content(nodes_data, format_type)
        
        # 设置相应的Content-Type
        content_type = get_content_type(format_type)
        
        return PlainTextResponse(content, media_type=content_type)
        
    except Exception as e:
        # 捕获所有异常并返回错误信息
        return PlainTextResponse(f"服务器错误: {str(e)}", media_type="text/plain")

@router.get("/subscription/{format}")
async def get_subscription(
    format: OutputFormat,
    user_id: Optional[int] = None,
    countries: Optional[str] = None,
    node_types: Optional[str] = None,
    max_latency: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """获取订阅内容（公开访问，根据user_id获取节点）"""
    try:
        # 获取节点数据
        if user_id:
            # 根据用户ID获取节点
            nodes = db.query(Node).join(InputRecord).filter(
                InputRecord.user_id == user_id,
                InputRecord.is_active == True
            ).all()
        else:
            # 获取所有公开的节点
            nodes = db.query(Node).join(InputRecord).filter(
                InputRecord.is_active == True
            ).all()
        
        # 如果没有节点，返回空的配置
        if not nodes:
            empty_config = {
                'proxies': [],
                'proxy-groups': [],
                'rules': []
            }
            if format == 'clash':
                import yaml
                content = yaml.dump(empty_config, default_flow_style=False, allow_unicode=True)
            else:
                content = "# 暂无可用节点"
            
            return PlainTextResponse(content, media_type="text/plain")
        
        # 应用查询参数过滤器
        if countries:
            country_list = [c.strip() for c in countries.split(',')]
            nodes = [n for n in nodes if n.country in country_list]
        
        if node_types:
            type_list = [t.strip() for t in node_types.split(',')]
            nodes = [n for n in nodes if n.node_type in type_list]
        
        if max_latency is not None:
            nodes = [n for n in nodes if n.ping_latency is None or n.ping_latency <= max_latency]
        
        # 转换为字典格式
        nodes_data = []
        for node in nodes:
            node_data = {
                'name': node.name,
                'type': node.node_type,  # 用于其他生成器
                'node_type': node.node_type,  # 用于 enhanced_clash 生成器
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
        if format == 'clash_enhanced':
            generator = EnhancedClashGenerator()
            content = generator.generate(nodes_data)
        else:
            generator = output_factory.get_generator(format)
            if not generator:
                return PlainTextResponse("# 不支持的输出格式", media_type="text/plain")
            content = generator.generate(nodes_data)
        
        return PlainTextResponse(content, media_type="text/plain")
        
    except Exception as e:
        # 捕获所有异常并返回错误信息
        return PlainTextResponse(f"服务器错误: {str(e)}", media_type="text/plain")

@router.get("/qrcode/{format}")
async def get_qrcode(
    format: OutputFormat,
    countries: Optional[str] = None,
    node_types: Optional[str] = None,
    max_latency: Optional[float] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """生成二维码"""
    # 获取订阅内容
    subscription_response = await get_subscription(
        format, countries, node_types, max_latency, current_user, db
    )
    
    content = subscription_response.body.decode('utf-8')
    
    # 生成二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(content)
    qr.make(fit=True)
    
    # 创建二维码图片
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 转换为base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {"qrcode": f"data:image/png;base64,{img_base64}"}

@router.get("/formats")
async def get_supported_formats():
    """获取支持的输出格式"""
    return {
        "formats": [
            {"name": "Clash", "value": "clash", "description": "Clash配置文件格式"},
            {"name": "V2RayN", "value": "v2rayn", "description": "V2RayN订阅格式"},
            {"name": "原始格式", "value": "raw", "description": "原始协议链接格式"}
        ]
    }

def apply_node_filter(nodes: List[Node], filter: NodeFilter) -> List[Node]:
    """应用节点过滤器"""
    filtered_nodes = nodes
    
    if filter.countries:
        filtered_nodes = [n for n in filtered_nodes if n.country in filter.countries]
    
    if filter.regions:
        filtered_nodes = [n for n in filtered_nodes if n.region in filter.regions]
    
    if filter.node_types:
        filtered_nodes = [n for n in filtered_nodes if n.node_type in filter.node_types]
    
    
    if filter.max_latency is not None:
        filtered_nodes = [n for n in filtered_nodes if n.ping_latency is None or n.ping_latency <= filter.max_latency]
    
    if filter.include_keywords:
        filtered_nodes = [
            n for n in filtered_nodes
            if any(keyword.lower() in n.name.lower() for keyword in filter.include_keywords)
        ]
    
    if filter.exclude_keywords:
        filtered_nodes = [
            n for n in filtered_nodes
            if not any(keyword.lower() in n.name.lower() for keyword in filter.exclude_keywords)
        ]
    
    return filtered_nodes