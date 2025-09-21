import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
from app.parsers.base import BaseParser
from app.models import NodeType

class TrojanParser(BaseParser):
    """Trojan协议解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [NodeType.TROJAN]
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析Trojan协议内容"""
        nodes = []
        
        try:
            # 尝试解析为trojan://链接
            nodes.extend(self._parse_trojan_links(content))
        except Exception as e:
            print(f"Trojan解析失败: {e}")
        
        return nodes
    
    def _parse_trojan_links(self, content: str) -> List[Dict[str, Any]]:
        """解析trojan://链接"""
        nodes = []
        
        # 查找所有trojan://链接
        trojan_pattern = r'trojan://([^@]+)@([^:]+):(\d+)(\?[^#]*)?(#[^\\s]*)?'
        matches = re.findall(trojan_pattern, content)
        
        for match in matches:
            try:
                password = match[0]
                address = match[1]
                port = int(match[2])
                query = match[3] if match[3] else ''
                fragment = match[4] if match[4] else ''
                
                # 解析查询参数
                params = {}
                if query.startswith('?'):
                    query_params = parse_qs(query[1:])
                    for key, value in query_params.items():
                        params[key] = value[0] if value else ''
                
                node = {
                    'name': fragment[1:] if fragment.startswith('#') else f"Trojan-{address}",
                    'type': 'trojan',
                    'address': address,
                    'port': port,
                    'password': password,
                    'tls': True,
                    'sni': params.get('sni', ''),
                    'country': self._extract_country_from_name(fragment[1:] if fragment.startswith('#') else ''),
                    'region': self._extract_region_from_name(fragment[1:] if fragment.startswith('#') else '')
                }
                
                # 验证节点数据
                if self.validate_node(node):
                    nodes.append(node)
            except Exception as e:
                print(f"trojan链接解析失败: {e}")
                continue
        
        return nodes