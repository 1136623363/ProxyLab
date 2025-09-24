from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timezone, timedelta
import os
import hashlib
import uuid
from config import config

# 北京时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

DATABASE_URL = config.DATABASE_URL

# 优化数据库连接配置
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,
        "isolation_level": None
    }

# 根据数据库类型优化连接池配置
if "sqlite" in DATABASE_URL:
    # SQLite 使用较小的连接池
    pool_size = 5
    max_overflow = 10
else:
    # PostgreSQL/MySQL 使用较大的连接池
    pool_size = 20
    max_overflow = 30

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_timeout=30,
    echo=False,
    future=True  # 使用SQLAlchemy 2.0风格
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=beijing_now, nullable=False)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, nullable=False)
    
    # 关系
    input_records = relationship("InputRecord", back_populates="user", cascade="all, delete-orphan")
    system_logs = relationship("SystemLog", back_populates="user", cascade="all, delete-orphan")
    subscription_links = relationship("SubscriptionLink", back_populates="user", cascade="all, delete-orphan")
    node_stats = relationship("NodeStats", back_populates="user", cascade="all, delete-orphan")
    short_urls = relationship("ShortUrl", back_populates="user", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_active', 'is_active'),
    )

class InputRecord(Base):
    """订阅记录表"""
    __tablename__ = "input_records"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=True)  # 订阅名称
    source_url = Column(String(500), nullable=True)  # 订阅源URL
    input_type = Column(String(20), nullable=False)  # url, yaml, json, text
    content = Column(Text, nullable=True)  # 订阅内容（已废弃，使用content_file_path）
    content_file_path = Column(String(500), nullable=True)  # 内容文件路径
    notes = Column(Text, nullable=True)  # 备注
    is_active = Column(Boolean, default=True, nullable=False)
    auto_refresh = Column(Boolean, default=True, nullable=False)  # 自动刷新
    refresh_interval = Column(Integer, default=3600, nullable=False)  # 刷新间隔（秒）
    node_count = Column(Integer, default=0, nullable=False)  # 节点数量
    last_refresh = Column(DateTime, nullable=True)  # 最后刷新时间
    last_error = Column(Text, nullable=True)  # 最后错误信息
    created_at = Column(DateTime, default=beijing_now, nullable=False)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="input_records")
    nodes = relationship("Node", back_populates="input_record", cascade="all, delete-orphan")
    node_stats = relationship("NodeStats", back_populates="input_record", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_input_user_id', 'user_id'),
        Index('idx_input_type', 'input_type'),
        Index('idx_input_active', 'is_active'),
        Index('idx_input_auto_refresh', 'auto_refresh'),
        Index('idx_input_created', 'created_at'),
        Index('idx_input_user_active', 'user_id', 'is_active'),
        Index('idx_input_user_type', 'user_id', 'input_type'),
        Index('idx_input_refresh_time', 'last_refresh'),
        Index('idx_input_node_count', 'node_count'),
    )

class Node(Base):
    """节点表"""
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    input_record_id = Column(Integer, ForeignKey("input_records.id"), nullable=False)
    name = Column(String(200), nullable=False)  # 节点名称
    node_type = Column(String(20), nullable=False)  # v2ray, trojan, ssr, ss
    address = Column(String(100), nullable=False)  # 服务器地址
    port = Column(Integer, nullable=False)  # 端口
    encryption = Column(String(50), nullable=True)  # 加密方式
    password = Column(String(200), nullable=True)  # 密码
    uuid = Column(String(100), nullable=True)  # UUID (for v2ray)
    alter_id = Column(Integer, nullable=True)  # Alter ID (for v2ray)
    network = Column(String(20), nullable=True)  # 传输协议 (tcp, ws, h2, grpc)
    path = Column(String(200), nullable=True)  # 路径 (for ws, h2, grpc)
    host = Column(String(100), nullable=True)  # 主机头 (for ws, h2, grpc)
    tls = Column(Boolean, default=False, nullable=False)  # 是否启用TLS
    sni = Column(String(100), nullable=True)  # SNI
    last_check = Column(DateTime, nullable=True)  # 最后检查时间
    status = Column(String(20), default="unknown", nullable=False)  # 状态: active, inactive, error, unknown, disabled
    ping_latency = Column(Float, nullable=True)  # 延迟 (ms)
    packet_loss = Column(Float, nullable=True)  # 丢包率 (%)
    availability = Column(Float, nullable=True)  # 可用性 (%)
    speed_test = Column(Float, nullable=True)  # 速度测试结果 (Mbps)
    country = Column(String(50), nullable=True)  # 国家
    region = Column(String(50), nullable=True)  # 地区
    ignore_updates = Column(Boolean, default=False, nullable=False)  # 忽略更新
    created_at = Column(DateTime, default=beijing_now, nullable=False)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, nullable=False)
    
    # 关系
    input_record = relationship("InputRecord", back_populates="nodes")
    
    # 索引
    __table_args__ = (
        Index('idx_node_input_record', 'input_record_id'),
        Index('idx_node_type', 'node_type'),
        Index('idx_node_status', 'status'),
        Index('idx_node_address_port', 'address', 'port'),
        Index('idx_node_country', 'country'),
        Index('idx_node_region', 'region'),
        Index('idx_node_created', 'created_at'),
        Index('idx_node_latency', 'ping_latency'),
        Index('idx_node_last_check', 'last_check'),
        Index('idx_node_user_status', 'input_record_id', 'status'),
        Index('idx_node_user_type', 'input_record_id', 'node_type'),
        Index('idx_node_user_country', 'input_record_id', 'country'),
        Index('idx_node_status_created', 'status', 'created_at'),
        Index('idx_node_latency_status', 'ping_latency', 'status'),
        UniqueConstraint('input_record_id', 'address', 'port', name='uq_node_input_address_port'),
    )


class SubscriptionLink(Base):
    """订阅链接表 - 每个用户生成的订阅链接唯一且不变"""
    __tablename__ = "subscription_links"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    link_id = Column(String(32), unique=True, nullable=False, index=True)  # 唯一链接ID
    name = Column(String(200), nullable=False)  # 订阅链接名称
    description = Column(Text, nullable=True)  # 描述
    output_format = Column(String(20), nullable=False)  # 输出格式: clash, v2rayn, raw
    filter_config = Column(Text, nullable=True)  # 过滤配置(JSON)
    is_active = Column(Boolean, default=True, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)  # 访问次数
    last_accessed = Column(DateTime, nullable=True)  # 最后访问时间
    created_at = Column(DateTime, default=beijing_now, nullable=False)
    updated_at = Column(DateTime, default=beijing_now, onupdate=beijing_now, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="subscription_links")
    
    # 索引
    __table_args__ = (
        Index('idx_sub_link_user_id', 'user_id'),
        Index('idx_sub_link_format', 'output_format'),
        Index('idx_sub_link_active', 'is_active'),
        Index('idx_sub_link_created', 'created_at'),
        Index('idx_sub_link_user_active', 'user_id', 'is_active'),
        Index('idx_sub_link_user_format', 'user_id', 'output_format'),
    )

class NodeStats(Base):
    """节点统计表 - 预计算的统计数据"""
    __tablename__ = "node_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    input_record_id = Column(Integer, ForeignKey("input_records.id"), nullable=True)
    total_nodes = Column(Integer, default=0, nullable=False)
    active_nodes = Column(Integer, default=0, nullable=False)
    inactive_nodes = Column(Integer, default=0, nullable=False)
    error_nodes = Column(Integer, default=0, nullable=False)
    unknown_nodes = Column(Integer, default=0, nullable=False)
    avg_latency = Column(Float, nullable=True)  # 平均延迟
    min_latency = Column(Float, nullable=True)  # 最小延迟
    max_latency = Column(Float, nullable=True)  # 最大延迟
    country_distribution = Column(Text, nullable=True)  # 国家分布(JSON)
    type_distribution = Column(Text, nullable=True)  # 类型分布(JSON)
    last_updated = Column(DateTime, default=beijing_now, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="node_stats")
    input_record = relationship("InputRecord", back_populates="node_stats")
    
    # 索引
    __table_args__ = (
        Index('idx_node_stats_user_id', 'user_id'),
        Index('idx_node_stats_input_record', 'input_record_id'),
        Index('idx_node_stats_updated', 'last_updated'),
        Index('idx_node_stats_user_updated', 'user_id', 'last_updated'),
    )

class SystemLog(Base):
    """系统日志表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可为空，系统日志
    log_type = Column(String(50), nullable=False)  # 日志类型: user_action, system_event, error
    level = Column(String(20), default="INFO", nullable=False)  # 日志级别: DEBUG, INFO, WARN, ERROR
    message = Column(Text, nullable=False)  # 日志消息
    details = Column(Text, nullable=True)  # 详细信息
    ip_address = Column(String(45), nullable=True)  # IP地址
    user_agent = Column(String(500), nullable=True)  # 用户代理
    created_at = Column(DateTime, default=beijing_now, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="system_logs")
    
    # 索引
    __table_args__ = (
        Index('idx_log_type', 'log_type'),
        Index('idx_log_level', 'level'),
        Index('idx_log_user_id', 'user_id'),
        Index('idx_log_created', 'created_at'),
        Index('idx_log_user_type', 'user_id', 'log_type'),
        Index('idx_log_level_created', 'level', 'created_at'),
        Index('idx_log_type_created', 'log_type', 'created_at'),
    )

class ShortUrl(Base):
    """短链接表"""
    __tablename__ = "short_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    short_code = Column(String(20), unique=True, nullable=False, index=True)  # 短链接代码
    original_url = Column(Text, nullable=False)  # 原始URL
    title = Column(String(200), nullable=True)  # 标题
    access_count = Column(Integer, default=0, nullable=False)  # 访问次数
    last_accessed = Column(DateTime, nullable=True)  # 最后访问时间
    expires_at = Column(DateTime, nullable=True)  # 过期时间
    is_active = Column(Boolean, default=True, nullable=False)  # 是否激活
    created_at = Column(DateTime, default=beijing_now, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="short_urls")
    
    # 索引
    __table_args__ = (
        Index('idx_short_user_id', 'user_id'),
        Index('idx_short_code', 'short_code'),
        Index('idx_short_active', 'is_active'),
        Index('idx_short_created', 'created_at'),
        Index('idx_short_user_active', 'user_id', 'is_active'),
    )

# 数据库操作函数
def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

def generate_unique_link_id():
    """生成唯一的订阅链接ID"""
    return hashlib.md5(str(uuid.uuid4()).encode()).hexdigest()[:16]

def init_database():
    """初始化数据库并创建默认admin用户"""
    # 创建表
    create_tables()
    print("✅ 数据库表创建成功")
    
    # 创建默认admin用户
    db = SessionLocal()
    try:
        # 检查是否已有admin用户
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("ℹ️ 管理员用户已存在，跳过创建默认用户")
            return
        
        # 创建默认管理员用户
        admin_password = "admin123"
        # 使用bcrypt加密密码
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(admin_password)
        
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=hashed_password,
            is_active=True,
            is_admin=True,
            created_at=beijing_now(),
            updated_at=beijing_now()
        )
        
        db.add(admin_user)
        db.commit()
        
        print("✅ 默认管理员用户创建成功")
        print("   用户名: admin")
        print("   密码: admin123")
        
    except Exception as e:
        print(f"❌ 创建默认用户失败: {e}")
        db.rollback()
        # 如果是唯一约束错误，说明用户已存在，这是正常的
        if "UNIQUE constraint failed" in str(e) or "IntegrityError" in str(e):
            print("ℹ️ 用户已存在，跳过创建默认用户")
        else:
            # 其他错误才抛出
            raise
    finally:
        db.close()