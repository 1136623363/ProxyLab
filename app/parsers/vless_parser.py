import base64
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, unquote
from app.parsers.base import BaseParser
from app.models import NodeType


class VLESSParser(BaseParser):
    """VLESS协议解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [NodeType.VLESS]
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析VLESS协议内容"""
        nodes = []
        
        try:
            # 尝试解析为vless://链接
            nodes.extend(self._parse_vless_links(content))
        except Exception as e:
            print(f"VLESS解析失败: {e}")
        
        return nodes
    
    def _parse_vless_links(self, content: str) -> List[Dict[str, Any]]:
        """解析vless://链接"""
        nodes = []
        
        # 查找所有vless://链接
        vless_pattern = r'vless://([^@]+)@([^:]+):(\d+)(\?[^#]*)?(#[^\\s]*)?'
        matches = re.findall(vless_pattern, content)
        
        for match in matches:
            try:
                uuid = match[0]
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
                    'name': fragment[1:] if fragment.startswith('#') else f"VLESS-{address}",
                    'type': 'vless',
                    'address': address,
                    'port': port,
                    'uuid': uuid,
                    'country': self._extract_country_from_name(fragment[1:] if fragment.startswith('#') else ''),
                    'region': self._extract_region_from_name(fragment[1:] if fragment.startswith('#') else '')
                }
                
                # 解析VLESS特定参数
                if 'security' in query_params:
                    node['security'] = query_params['security']
                
                if 'sni' in query_params:
                    node['sni'] = query_params['sni']
                
                if 'fp' in query_params:
                    node['fingerprint'] = query_params['fp']
                
                if 'pbk' in query_params:
                    node['public_key'] = query_params['pbk']
                
                if 'sid' in query_params:
                    node['short_id'] = query_params['sid']
                
                if 'type' in query_params:
                    node['network'] = query_params['type']
                
                if 'flow' in query_params:
                    node['flow'] = query_params['flow']
                
                if 'encryption' in query_params:
                    node['encryption'] = query_params['encryption']
                
                if 'path' in query_params:
                    node['path'] = query_params['path']
                
                if 'host' in query_params:
                    node['host'] = query_params['host']
                
                # 设置TLS状态
                node['tls'] = query_params.get('security') in ['tls', 'reality']
                
                # 验证节点数据
                if self.validate_node(node):
                    nodes.append(node)
            except Exception as e:
                print(f"vless链接解析失败: {e}")
                continue
        
        return nodes
