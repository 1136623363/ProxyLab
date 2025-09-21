from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db, ShortUrl

router = APIRouter()

@router.get("/s/{short_code}")
async def redirect_short_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """重定向短链接"""
    # 查找短链接
    short_url = db.query(ShortUrl).filter(
        ShortUrl.short_code == short_code,
        ShortUrl.is_active == True
    ).first()
    
    if not short_url:
        raise HTTPException(status_code=404, detail="短链接不存在或已失效")
    
    # 检查是否过期
    if short_url.expires_at and short_url.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="短链接已过期")
    
    # 更新访问统计
    short_url.access_count += 1
    short_url.last_accessed = datetime.utcnow()
    db.commit()
    
    # 重定向到原始URL
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=short_url.original_url, status_code=302)
