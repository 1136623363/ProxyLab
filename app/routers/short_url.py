from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import secrets
import string
from app.database import get_db, User, ShortUrl
from app.auth import get_current_active_user
from pydantic import BaseModel, HttpUrl

router = APIRouter()

class ShortUrlCreate(BaseModel):
    original_url: str
    title: Optional[str] = None
    expires_in_days: Optional[int] = 30

class ShortUrlResponse(BaseModel):
    id: int
    short_code: str
    original_url: str
    title: Optional[str]
    short_url: str
    access_count: int
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool

def generate_short_code(length: int = 8) -> str:
    """生成短链接代码"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

@router.post("/create", response_model=ShortUrlResponse)
async def create_short_url(
    url_data: ShortUrlCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """创建短链接"""
    try:
        # 检查是否已存在相同的原始URL
        existing_url = db.query(ShortUrl).filter(
            ShortUrl.user_id == current_user.id,
            ShortUrl.original_url == url_data.original_url,
            ShortUrl.is_active == True
        ).first()
        
        if existing_url:
            # 如果存在，返回现有的短链接
            base_url = "http://localhost:8001"  # 可以从配置中获取
            return ShortUrlResponse(
                id=existing_url.id,
                short_code=existing_url.short_code,
                original_url=existing_url.original_url,
                title=existing_url.title,
                short_url=f"{base_url}/s/{existing_url.short_code}",
                access_count=existing_url.access_count,
                expires_at=existing_url.expires_at,
                created_at=existing_url.created_at,
                is_active=existing_url.is_active
            )
        
        # 生成唯一的短代码
        while True:
            short_code = generate_short_code()
            if not db.query(ShortUrl).filter(ShortUrl.short_code == short_code).first():
                break
        
        # 计算过期时间
        expires_at = None
        if url_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=url_data.expires_in_days)
        
        # 创建短链接记录
        short_url = ShortUrl(
            user_id=current_user.id,
            short_code=short_code,
            original_url=url_data.original_url,
            title=url_data.title,
            expires_at=expires_at,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(short_url)
        db.commit()
        db.refresh(short_url)
        
        # 生成完整的短链接
        base_url = "http://localhost:8001"  # 可以从配置中获取
        full_short_url = f"{base_url}/s/{short_code}"
        
        return ShortUrlResponse(
            id=short_url.id,
            short_code=short_url.short_code,
            original_url=short_url.original_url,
            title=short_url.title,
            short_url=full_short_url,
            access_count=short_url.access_count,
            expires_at=short_url.expires_at,
            created_at=short_url.created_at,
            is_active=short_url.is_active
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建短链接失败: {str(e)}")

@router.get("/", response_model=List[ShortUrlResponse])
async def get_short_urls(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取用户的短链接列表"""
    short_urls = db.query(ShortUrl).filter(
        ShortUrl.user_id == current_user.id,
        ShortUrl.is_active == True
    ).order_by(ShortUrl.created_at.desc()).all()
    
    base_url = "http://localhost:8001"
    return [
        ShortUrlResponse(
            id=url.id,
            short_code=url.short_code,
            original_url=url.original_url,
            title=url.title,
            short_url=f"{base_url}/s/{url.short_code}",
            access_count=url.access_count,
            expires_at=url.expires_at,
            created_at=url.created_at,
            is_active=url.is_active
        )
        for url in short_urls
    ]

@router.delete("/{short_code}")
async def delete_short_url(
    short_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """删除短链接"""
    short_url = db.query(ShortUrl).filter(
        ShortUrl.short_code == short_code,
        ShortUrl.user_id == current_user.id
    ).first()
    
    if not short_url:
        raise HTTPException(status_code=404, detail="短链接不存在")
    
    short_url.is_active = False
    db.commit()
    
    return {"message": "短链接已删除"}

@router.get("/{short_code}/stats")
async def get_short_url_stats(
    short_code: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """获取短链接统计信息"""
    short_url = db.query(ShortUrl).filter(
        ShortUrl.short_code == short_code,
        ShortUrl.user_id == current_user.id
    ).first()
    
    if not short_url:
        raise HTTPException(status_code=404, detail="短链接不存在")
    
    return {
        "short_code": short_url.short_code,
        "original_url": short_url.original_url,
        "title": short_url.title,
        "access_count": short_url.access_count,
        "created_at": short_url.created_at,
        "last_accessed": short_url.last_accessed,
        "expires_at": short_url.expires_at,
        "is_active": short_url.is_active
    }
