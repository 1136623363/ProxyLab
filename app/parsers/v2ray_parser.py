import json
import base64
import re
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
from app.parsers.base import BaseParser
from app.models import NodeType

class V2RayParser(BaseParser):
    """V2Ray协议解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [NodeType.V2RAY]
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析V2Ray协议内容"""
        nodes = []
        
        try:
            # 尝试解析为JSON格式
            if content.strip().startswith('{') or content.strip().startswith('['):
                nodes.extend(self._parse_json(content))
            else:
                # 尝试解析为base64编码的vmess链接
                try:
                    # 使用安全解码方法
                    decoded = self.safe_decode_base64(content)
                    
                    nodes.extend(self._parse_vmess_links(decoded))
                except:
                    # 尝试解析为vmess://链接
                    nodes.extend(self._parse_vmess_links(content))
        except Exception as e:
            print(f"V2Ray解析失败: {e}")
        
        return nodes
    
    def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """解析JSON格式的V2Ray配置"""
        nodes = []
        try:
            data = json.loads(content)
            
            # 处理单个配置对象
            if isinstance(data, dict):
                if 'outbounds' in data:
                    # 标准V2Ray配置格式
                    for outbound in data.get('outbounds', []):
                        if outbound.get('protocol') == 'vmess':
                            node = self._parse_vmess_config(outbound)
                            if node:
                                nodes.append(node)
                elif 'v' in data and 'ps' in data:
                    # 单个vmess配置
                    node = self._parse_vmess_config(data)
                    if node:
                        nodes.append(node)
            
            # 处理配置数组
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'v' in item and 'ps' in item:
                        node = self._parse_vmess_config(item)
                        if node:
                            nodes.append(node)
        except Exception as e:
            print(f"JSON解析失败: {e}")
        
        return nodes
    
    def _parse_vmess_links(self, content: str) -> List[Dict[str, Any]]:
        """解析vmess://链接"""
        nodes = []
        
        # 查找所有vmess://链接
        vmess_pattern = r'vmess://([A-Za-z0-9+/=]+)'
        matches = re.findall(vmess_pattern, content)
        
        for match in matches:
            try:
                # 使用安全解码方法
                decoded = self.safe_decode_base64(match)
                config = json.loads(decoded)
                
                node = self._parse_vmess_config(config)
                if node:
                    nodes.append(node)
            except Exception as e:
                print(f"vmess链接解析失败: {e}")
                continue
        
        return nodes
    
    def _parse_vmess_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析vmess配置"""
        try:
            node = {
                'name': config.get('ps', ''),
                'type': 'v2ray',
                'address': config.get('add', ''),
                'port': int(config.get('port', 0)),
                'uuid': config.get('id', ''),
                'alter_id': int(config.get('aid', 0)),
                'network': config.get('net', 'tcp'),
                'path': config.get('path', ''),
                'host': config.get('host', ''),
                'tls': config.get('tls') == 'tls',
                'sni': config.get('sni', ''),
                'country': self._extract_country_from_name(config.get('ps', '')),
                'region': self._extract_region_from_name(config.get('ps', ''))
            }
            
            # 验证节点数据
            if self.validate_node(node):
                return node
        except Exception as e:
            print(f"vmess配置解析失败: {e}")
        
        return None