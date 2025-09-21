import base64
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, unquote
from app.parsers.base import BaseParser
from app.models import NodeType

class SSParser(BaseParser):
    """Shadowsocks协议解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [NodeType.SS]
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析Shadowsocks协议内容"""
        nodes = []
        
        try:
            # 尝试解析为ss://链接
            nodes.extend(self._parse_ss_links(content))
        except Exception as e:
            print(f"Shadowsocks解析失败: {e}")
        
        return nodes
    
    def _parse_ss_links(self, content: str) -> List[Dict[str, Any]]:
        """解析ss://链接"""
        nodes = []
        
        # 查找所有ss://链接
        ss_pattern = r'ss://([A-Za-z0-9+/=]+)(#[^\\s]*)?'
        matches = re.findall(ss_pattern, content)
        
        for match in matches:
            try:
                encoded = match[0]
                fragment = match[1] if match[1] else ''
                
                # 使用安全解码方法
                decoded = self.safe_decode_base64(encoded)
                
                # 解析格式: method:password@address:port
                if '@' in decoded:
                    method_password, address_port = decoded.split('@', 1)
                    method, password = method_password.split(':', 1)
                    address, port = address_port.split(':', 1)
                    
                    node = {
                        'name': fragment[1:] if fragment.startswith('#') else f"SS-{address}",
                        'type': 'ss',
                        'address': address,
                        'port': int(port),
                        'encryption': method,
                        'password': password,
                        'country': self._extract_country_from_name(fragment[1:] if fragment.startswith('#') else ''),
                        'region': self._extract_region_from_name(fragment[1:] if fragment.startswith('#') else '')
                    }
                    
                    # 验证节点数据
                    if self.validate_node(node):
                        nodes.append(node)
            except Exception as e:
                print(f"ss链接解析失败: {e}")
                continue
        
        return nodes