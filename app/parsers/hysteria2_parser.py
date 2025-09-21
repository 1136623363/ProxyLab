import base64
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, unquote
from app.parsers.base import BaseParser
from app.models import NodeType


class Hysteria2Parser(BaseParser):
    """Hysteria2协议解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [NodeType.HYSTERIA2]
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析Hysteria2协议内容"""
        nodes = []
        
        try:
            # 尝试解析为hy2://链接
            nodes.extend(self._parse_hysteria2_links(content))
        except Exception as e:
            print(f"Hysteria2解析失败: {e}")
        
        return nodes
    
    def _parse_hysteria2_links(self, content: str) -> List[Dict[str, Any]]:
        """解析hy2://链接"""
        nodes = []
        
        # 查找所有hy2://链接
        hy2_pattern = r'hy2://([^@]+)@([^:]+):(\d+)(\?[^#]*)?(#[^\\s]*)?'
        matches = re.findall(hy2_pattern, content)
        
        for match in matches:
            try:
                password = match[0]
                address = match[1]
                port = int(match[2])
                query_string = match[3] if match[3] else ''
                fragment = match[4] if match[4] else ''
                
                # 解析查询参数
                query_params = {}
                if query_string.startswith('?'):
                    query_string = query_string[1:]
                    for param in query_string.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            query_params[key] = unquote(value)
                
                # 构建节点数据
                node = {
                    'name': fragment[1:] if fragment.startswith('#') else f"Hysteria2-{address}",
                    'type': 'hysteria2',
                    'address': address,
                    'port': port,
                    'password': password,
                    'country': self._extract_country_from_name(fragment[1:] if fragment.startswith('#') else ''),
                    'region': self._extract_region_from_name(fragment[1:] if fragment.startswith('#') else '')
                }
                
                # 解析Hysteria2特定参数
                if 'sni' in query_params:
                    node['sni'] = query_params['sni']
                
                if 'insecure' in query_params:
                    node['insecure'] = query_params['insecure'].lower() == 'true'
                
                if 'pinSHA256' in query_params:
                    node['pin_sha256'] = query_params['pinSHA256']
                
                if 'obfs' in query_params:
                    node['obfs'] = query_params['obfs']
                
                if 'obfs-password' in query_params:
                    node['obfs_password'] = query_params['obfs-password']
                
                if 'auth' in query_params:
                    node['auth'] = query_params['auth']
                
                if 'up' in query_params:
                    node['up'] = query_params['up']
                
                if 'down' in query_params:
                    node['down'] = query_params['down']
                
                if 'fastOpen' in query_params:
                    node['fast_open'] = query_params['fastOpen'].lower() == 'true'
                
                if 'lazy' in query_params:
                    node['lazy'] = query_params['lazy'].lower() == 'true'
                
                # 验证节点数据
                if self.validate_node(node):
                    nodes.append(node)
            except Exception as e:
                print(f"hysteria2链接解析失败: {e}")
                continue
        
        return nodes
