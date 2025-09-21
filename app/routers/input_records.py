from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import requests
import os
import hashlib

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)
from app.database import get_db, User, InputRecord, Node
from app.models import InputRecordCreate, InputRecordUpdate, InputRecord as InputRecordModel, Node as NodeModel
from app.auth import get_current_active_user
from app.parsers.parser_factory import ParserFactory
from app.models import InputType

router = APIRouter()
parser_factory = ParserFactory()

# 确保data目录存在
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def save_content_to_file(content: str, record_id: int) -> str:
    """将内容保存到文件并返回文件路径"""
    # 生成文件名：record_id + 内容hash的前8位
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()[:8]
    filename = f"record_{record_id}_{content_hash}.txt"
    filepath = os.path.join(DATA_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

def load_content_from_file(filepath: str) -> str:
    """从文件加载内容"""
    if not filepath or not os.path.exists(filepath):
        return ""
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def delete_content_file(filepath: str):
    """删除内容文件"""
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except Exception as e:
            print(f"删除文件失败: {e}")

@router.post("/", response_model=InputRecordModel)
async def create_input_record(
    input_record: InputRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建订阅记录"""
    content = input_record.content
    
    # 如果是URL类型，先获取内容
    if input_record.input_type == "url" and input_record.source_url:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(input_record.source_url, headers=headers, timeout=30)
            response.raise_for_status()
            content = response.text
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"无法获取URL内容: {str(e)}"
            )
    
    # 如果用户提供数据，使用URL内容
    if not content and input_record.source_url:
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(input_record.source_url, headers=headers, timeout=30)
            response.raise_for_status()
            content = response.text
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"无法获取URL内容: {str(e)}"
            )
    
    if not content:
        raise HTTPException(
            status_code=400,
            detail="请提供内容或有效的URL"
        )
    
    # 自动生成订阅名称
    def generate_subscription_name(input_type, source_url, content):
        """根据输入类型和内容自动生成订阅名称"""
        if input_type == "url" and source_url:
            # URL类型：使用域名作为名称
            try:
                from urllib.parse import urlparse
                parsed_url = urlparse(source_url)
                domain = parsed_url.netloc
                if domain:
                    return f"订阅_{domain}"
            except:
                pass
            return f"订阅_{beijing_now().strftime('%Y%m%d_%H%M%S')}"
        elif input_type in ["text", "yaml", "json"] and content:
            # 文本类型：尝试从内容中提取名称
            try:
                # 尝试从YAML中提取名称
                if input_type == "yaml" and "proxies:" in content:
                    lines = content.split('\n')
                    for line in lines[:20]:  # 只检查前20行
                        if line.strip().startswith('name:') or line.strip().startswith('- name:'):
                            name = line.split(':', 1)[1].strip().strip('"\'')
                            if name and len(name) < 50:
                                return f"订阅_{name}"
                # 尝试从JSON中提取名称
                elif input_type == "json":
                    import json
                    data = json.loads(content)
                    if isinstance(data, dict) and 'name' in data:
                        return f"订阅_{data['name']}"
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and 'name' in data[0]:
                        return f"订阅_{data[0]['name']}"
            except:
                pass
        # 默认名称
        return f"订阅_{input_type}_{beijing_now().strftime('%Y%m%d_%H%M%S')}"
    
    # 创建订阅记录（先不存储内容）
    subscription_name = generate_subscription_name(input_record.input_type, input_record.source_url, content)
    db_record = InputRecord(
        user_id=current_user.id,
        name=subscription_name,
        source_url=input_record.source_url,
        input_type=input_record.input_type,
        content=None,  # 不存储大文件内容
        content_file_path=None,  # 稍后设置
        notes=input_record.notes,
        is_active=True,
        auto_refresh=True if input_record.input_type == "url" else False,
        refresh_interval=3600,
        node_count=0,
        created_at=beijing_now(),
        updated_at=beijing_now()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    # 保存内容到文件
    content_file_path = save_content_to_file(content, db_record.id)
    db_record.content_file_path = content_file_path
    db.commit()
    
    # 解析内容并创建节点
    try:
        from app.models import InputType
        # 如果已经获取了URL内容，应该使用TEXT类型进行解析，而不是URL类型
        if input_record.input_type == "url" and content:
            input_type_enum = InputType.TEXT
        else:
            input_type_enum = InputType(input_record.input_type) if hasattr(InputType, input_record.input_type.upper()) else InputType.TEXT
        nodes_data = parser_factory.parse_content(content, input_type_enum)
        
        # 检查是否有有效节点
        if not nodes_data or len(nodes_data) == 0:
            # 删除已创建的记录
            db.delete(db_record)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="订阅内容中没有找到有效的节点，请检查订阅链接或内容是否正确"
            )
        
        # 验证节点数据的基本有效性
        valid_nodes = []
        for node_data in nodes_data:
            # 检查必要字段
            if not node_data.get('name') or not node_data.get('address') or not node_data.get('port'):
                continue
            valid_nodes.append(node_data)
        
        if not valid_nodes:
            # 删除已创建的记录
            db.delete(db_record)
            db.commit()
            raise HTTPException(
                status_code=400,
                detail="订阅内容中的节点数据不完整，缺少必要字段（名称、地址、端口）"
            )
        
        # 创建有效节点
        for node_data in valid_nodes:
            node = Node(
                input_record_id=db_record.id,
                name=node_data.get('name', ''),
                node_type=node_data.get('type', ''),
                address=node_data.get('address', ''),
                port=node_data.get('port', 0),
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
                status='unknown',
                ignore_updates=False,
                created_at=beijing_now(),
                updated_at=beijing_now()
            )
            db.add(node)
        
        # 更新节点计数
        db_record.node_count = len(valid_nodes)
        db.commit()
        
        # 更新统计数据
        from app.services.stats_service import StatsService
        StatsService.update_node_stats(db, current_user.id, db_record.id)
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 删除已创建的记录
        db.delete(db_record)
        db.commit()
        raise HTTPException(
            status_code=400,
            detail=f"解析订阅内容时出错: {str(e)}"
        )
    
    return db_record

@router.get("/", response_model=List[InputRecordModel])
async def get_input_records(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取订阅记录列表"""
    records = db.query(InputRecord).filter(
        InputRecord.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    return records

@router.get("/{record_id}", response_model=InputRecordModel)
async def get_input_record(
    record_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取特定订阅记录"""
    record = db.query(InputRecord).filter(
        InputRecord.id == record_id,
        InputRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="订阅记录不存在")
    
    return record

@router.put("/{record_id}", response_model=InputRecordModel)
async def update_input_record(
    record_id: int,
    input_record: InputRecordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新订阅记录"""
    record = db.query(InputRecord).filter(
        InputRecord.id == record_id,
        InputRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="订阅记录不存在")
    
    # 更新记录 - 只更新提供的字段
    update_data = input_record.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    # 如果订阅被禁用，其所有节点也设置为禁用状态
    if 'is_active' in update_data and not update_data['is_active']:
        # 订阅被禁用，禁用所有相关节点
        db.query(Node).filter(Node.input_record_id == record_id).update({
            'status': 'disabled',
            'updated_at': beijing_now()
        })
    elif 'is_active' in update_data and update_data['is_active']:
        # 订阅被启用，将禁用的节点状态重置为unknown
        db.query(Node).filter(
            Node.input_record_id == record_id,
            Node.status == 'disabled'
        ).update({
            'status': 'unknown',
            'updated_at': beijing_now()
        })
    
    # 更新时间戳
    record.updated_at = beijing_now()
    
    db.commit()
    db.refresh(record)
    
    return record

@router.delete("/{record_id}")
async def delete_input_record(
    record_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除订阅记录"""
    record = db.query(InputRecord).filter(
        InputRecord.id == record_id,
        InputRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="订阅记录不存在")
    
    # 删除内容文件
    if record.content_file_path:
        delete_content_file(record.content_file_path)
    
    # 删除相关节点
    db.query(Node).filter(Node.input_record_id == record_id).delete()
    
    # 删除记录
    db.delete(record)
    db.commit()
    
    return {"message": "订阅记录删除成功"}

@router.post("/{record_id}/refresh")
async def refresh_input_record(
    record_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """刷新订阅记录"""
    record = db.query(InputRecord).filter(
        InputRecord.id == record_id,
        InputRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="订阅记录不存在")
    
    if record.input_type != "url" or not record.source_url:
        raise HTTPException(status_code=400, detail="只有URL类型的订阅记录可以刷新")
    
    try:
        # 获取最新内容
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/plain,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(record.source_url, headers=headers, timeout=30)
        response.raise_for_status()
        content = response.text
        
        # 删除旧内容文件
        if record.content_file_path:
            delete_content_file(record.content_file_path)
        
        # 保存新内容到文件
        content_file_path = save_content_to_file(content, record_id)
        record.content_file_path = content_file_path
        record.content = None  # 不存储大文件内容
        record.updated_at = beijing_now()
        
        # 删除旧节点
        db.query(Node).filter(Node.input_record_id == record_id).delete()
        
        # 解析新内容并创建节点
        try:
            from app.models import InputType
            # 如果已经获取了URL内容，应该使用TEXT类型进行解析，而不是URL类型
            if record.input_type == "url" and content:
                input_type_enum = InputType.TEXT
            else:
                input_type_enum = InputType(record.input_type) if hasattr(InputType, record.input_type.upper()) else InputType.TEXT
            nodes_data = parser_factory.parse_content(content, input_type_enum)
            if nodes_data:
                for node_data in nodes_data:
                    node = Node(
                        input_record_id=record.id,
                        name=node_data.get('name', ''),
                        node_type=node_data.get('type', ''),
                        address=node_data.get('address', ''),
                        port=node_data.get('port', 0),
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
                        status='unknown',
                        ignore_updates=False,
                        created_at=beijing_now(),
                        updated_at=beijing_now()
                    )
                    db.add(node)
                
                # 更新节点计数和刷新时间
                record.node_count = len(nodes_data)
                record.last_refresh = beijing_now()
                record.last_error = None
                
                # 更新统计数据
                from app.services.stats_service import StatsService
                StatsService.update_node_stats(db, current_user.id, record.id)
        except Exception as e:
            error_msg = f"解析内容时出错: {e}"
            print(error_msg)
            record.last_error = error_msg
            # 记录错误但不阻止更新
        
        db.commit()
        db.refresh(record)
        
        return {"message": "订阅记录刷新成功", "record": record}
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"刷新订阅记录失败: {str(e)}"
        )

@router.get("/{record_id}/content")
async def get_input_record_content(
    record_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取订阅记录的内容"""
    record = db.query(InputRecord).filter(
        InputRecord.id == record_id,
        InputRecord.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="订阅记录不存在")
    
    # 从文件加载内容
    content = ""
    if record.content_file_path:
        content = load_content_from_file(record.content_file_path)
    elif record.content:
        content = record.content
    
    return {"content": content}