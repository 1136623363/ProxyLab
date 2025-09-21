import requests
import base64
import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class SubscriptionFetcher:
    """订阅链接获取器"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # 配置SSL和重试
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # 禁用SSL验证警告
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _normalize_url(self, url: str) -> str:
        """标准化URL格式"""
        url = url.strip()
        
        # 如果URL不包含协议，添加https://
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def fetch_subscription(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """
        获取订阅内容
        
        Args:
            url: 订阅链接
            
        Returns:
            Tuple[成功标志, 内容, 错误信息]
        """
        try:
            # 标准化URL
            url = self._normalize_url(url)
            
            # 验证URL格式
            if not self._is_valid_url(url):
                return False, "", "无效的URL格式"
            
            # 发送请求，添加SSL容错处理
            try:
                response = self.session.get(url, timeout=self.timeout, verify=True)
                response.raise_for_status()
            except requests.exceptions.SSLError as ssl_error:
                # 如果SSL验证失败，尝试禁用SSL验证
                print(f"SSL验证失败，尝试禁用SSL验证: {ssl_error}")
                response = self.session.get(url, timeout=self.timeout, verify=False)
                response.raise_for_status()
            
            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            
            # 如果是base64编码的内容，尝试解码
            content = response.text
            if self._is_base64_content(content):
                try:
                    # 尝试解码base64
                    decoded_bytes = base64.b64decode(content)
                    # 尝试多种编码解码
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'gbk', 'gb2312']:
                        try:
                            content = decoded_bytes.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # 如果所有编码都失败，使用错误替换模式
                        content = decoded_bytes.decode('utf-8', errors='replace')
                except Exception as e:
                    # 如果base64解码失败，使用原始内容
                    pass
            
            return True, content, None
            
        except requests.exceptions.Timeout:
            return False, "", "请求超时"
        except requests.exceptions.ConnectionError:
            return False, "", "连接错误"
        except requests.exceptions.HTTPError as e:
            return False, "", f"HTTP错误: {e.response.status_code}"
        except Exception as e:
            error_msg = f"获取订阅失败: {str(e)}"
            print(f"订阅获取错误 - URL: {url}, 错误: {error_msg}")
            return False, "", error_msg
    
    def _is_base64_content(self, content: str) -> bool:
        """检查内容是否为base64编码"""
        if not content:
            return False
        
        # 移除空白字符
        content = content.strip()
        
        # 检查长度是否为4的倍数
        if len(content) % 4 != 0:
            return False
        
        # 检查是否只包含base64字符
        try:
            base64.b64decode(content)
            return True
        except Exception:
            return False
    
    def close(self):
        """关闭会话"""
        self.session.close()
