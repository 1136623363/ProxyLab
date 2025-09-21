from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class NodeType(str, Enum):
    V2RAY = "v2ray"
    TROJAN = "trojan"
    SSR = "ssr"
    SS = "ss"
    VLESS = "vless"
    HYSTERIA2 = "hysteria2"

class InputType(str, Enum):
    URL = "url"
    YAML = "yaml"
    JSON = "json"
    TEXT = "text"

class NodeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UNKNOWN = "unknown"
    DISABLED = "disabled"

class GroupType(str, Enum):
    CUSTOM = "custom"
    AUTO = "auto"

class LogType(str, Enum):
    SUBSCRIPTION_UPDATE = "subscription_update"
    NODE_CHECK = "node_check"
    ERROR = "error"

# 用户相关模型
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# 订阅记录模型
class InputRecordBase(BaseModel):
    source_url: Optional[str] = None
    input_type: str
    content: Optional[str] = None
    notes: Optional[str] = None

class InputRecordCreate(InputRecordBase):
    pass

class InputRecordUpdate(BaseModel):
    source_url: Optional[str] = None
    input_type: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class InputRecord(InputRecordBase):
    id: int
    user_id: int
    name: Optional[str] = None
    is_active: bool
    auto_refresh: bool
    refresh_interval: int
    node_count: int
    last_refresh: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 节点相关模型
class NodeBase(BaseModel):
    name: str
    node_type: NodeType
    address: str
    port: int
    encryption: Optional[str] = None
    password: Optional[str] = None
    uuid: Optional[str] = None
    alter_id: Optional[int] = None
    network: Optional[str] = None
    path: Optional[str] = None
    host: Optional[str] = None
    tls: bool = False
    sni: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None

class NodeCreate(NodeBase):
    input_record_id: int

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    ignore_updates: Optional[bool] = None
    country: Optional[str] = None
    region: Optional[str] = None
    status: Optional[str] = None

class Node(NodeBase):
    id: int
    input_record_id: int
    last_check: Optional[datetime] = None
    status: NodeStatus
    ping_latency: Optional[float] = None
    packet_loss: Optional[float] = None
    ignore_updates: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 节点分组模型
class NodeGroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    group_type: GroupType

class NodeGroupCreate(NodeGroupBase):
    pass

class NodeGroup(NodeGroupBase):
    id: int
    user_id: int
    color: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class NodeGroupMembershipCreate(BaseModel):
    node_id: int
    group_id: int

class NodeGroupMembership(NodeGroupMembershipCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 系统日志模型
class SystemLogBase(BaseModel):
    log_type: LogType
    message: str
    details: Optional[str] = None

class SystemLog(SystemLogBase):
    id: int
    user_id: Optional[int] = None
    level: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# 输出格式相关模型
class OutputFormat(str, Enum):
    CLASH = "clash"
    CLASH_ENHANCED = "clash_enhanced"
    V2RAYN = "v2rayn"
    RAW = "raw"

class NodeFilter(BaseModel):
    countries: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    node_types: Optional[List[NodeType]] = None
    max_latency: Optional[float] = None
    exclude_keywords: Optional[List[str]] = None
    include_keywords: Optional[List[str]] = None
    skip: int = 0
    limit: int = 100
    sort_by: Optional[str] = None

class SubscriptionOutput(BaseModel):
    format: OutputFormat
    filter: Optional[NodeFilter] = None
    group_id: Optional[int] = None

# 节点检测模型
class NodeCheckResult(BaseModel):
    node_id: int
    status: NodeStatus
    ping_latency: Optional[float] = None
    packet_loss: Optional[float] = None
    error_message: Optional[str] = None

class BulkNodeCheck(BaseModel):
    node_ids: List[int]
    force_check: bool = False