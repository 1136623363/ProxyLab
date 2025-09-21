import yaml
import json
from typing import List, Dict, Any
from app.parsers.base import BaseParser
from app.models import NodeType

class ClashParser(BaseParser):
    """Clash协议解析器"""
    
    def __init__(self):
        super().__init__()
        self.supported_types = [NodeType.V2RAY, NodeType.TROJAN, NodeType.SS]
    
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """解析Clash协议内容"""
        nodes = []
        
        try:
            # 尝试解析为YAML格式
            if 'proxies:' in content:
                nodes.extend(self._parse_yaml(content))
            # 尝试解析为JSON格式
            elif content.strip().startswith('{'):
                nodes.extend(self._parse_json(content))
        except Exception as e:
            print(f"Clash解析失败: {e}")
        
        return nodes
    
    def _parse_yaml(self, content: str) -> List[Dict[str, Any]]:
        """解析YAML格式的Clash配置"""
        nodes = []
        try:
            data = yaml.safe_load(content)
            proxies = data.get('proxies', [])
            
            for proxy in proxies:
                node = self._parse_proxy(proxy)
                if node:
                    nodes.append(node)
        except Exception as e:
            print(f"YAML解析失败: {e}")
            # 尝试解析内联格式
            try:
                nodes.extend(self._parse_inline_yaml(content))
            except Exception as e2:
                print(f"内联YAML解析也失败: {e2}")
        
        # 如果标准YAML解析没有找到节点，尝试内联解析
        if not nodes:
            try:
                nodes.extend(self._parse_inline_yaml(content))
            except Exception as e:
                print(f"内联YAML解析失败: {e}")
        
        return nodes
    
    def _parse_inline_yaml(self, content: str) -> List[Dict[str, Any]]:
        """解析内联格式的YAML配置"""
        nodes = []
        import re
        
        # 查找所有代理配置行
        proxy_pattern = r'^\s*-\s*\{([^}]+)\}'
        lines = content.split('\n')
        
        for line in lines:
            match = re.match(proxy_pattern, line)
            if match:
                proxy_str = match.group(1)
                # 解析内联配置
                proxy_dict = self._parse_inline_proxy(proxy_str)
                if proxy_dict:
                    node = self._parse_proxy(proxy_dict)
                    if node:
                        nodes.append(node)
        
        return nodes
    
    def _parse_inline_proxy(self, proxy_str: str) -> Dict[str, Any]:
        """解析内联代理配置字符串"""
        proxy_dict = {}
        
        # 简单的键值对解析
        # 处理带引号的字符串
        import re
        
        # 匹配 key: value 模式
        pattern = r'(\w+):\s*([^,}]+)'
        matches = re.findall(pattern, proxy_str)
        
        for key, value in matches:
            value = value.strip()
            # 移除引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # 转换数据类型
            if key in ['port', 'alterId']:
                try:
                    proxy_dict[key] = int(value)
                except ValueError:
                    proxy_dict[key] = value
            elif key in ['udp', 'tls']:
                proxy_dict[key] = value.lower() in ['true', '1', 'yes']
            else:
                proxy_dict[key] = value
        
        return proxy_dict
    
    def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """解析JSON格式的Clash配置"""
        nodes = []
        try:
            data = json.loads(content)
            proxies = data.get('proxies', [])
            
            for proxy in proxies:
                node = self._parse_proxy(proxy)
                if node:
                    nodes.append(node)
        except Exception as e:
            print(f"JSON解析失败: {e}")
        
        return nodes
    
    def _parse_proxy(self, proxy: Dict[str, Any]) -> Dict[str, Any]:
        """解析单个代理配置"""
        try:
            proxy_type = proxy.get('type', '').lower()
            name = proxy.get('name', '')
            
            if proxy_type == 'vmess':
                return {
                    'name': name,
                    'type': 'v2ray',
                    'address': proxy.get('server', ''),
                    'port': int(proxy.get('port', 0)),
                    'uuid': proxy.get('uuid', ''),
                    'alter_id': int(proxy.get('alterId', 0)),
                    'network': proxy.get('network', 'tcp'),
                    'path': proxy.get('ws-path', ''),
                    'host': proxy.get('ws-headers', {}).get('Host', ''),
                    'tls': proxy.get('tls', False),
                    'sni': proxy.get('servername', ''),
                    'country': self._extract_country_from_name(name),
                    'region': self._extract_region_from_name(name)
                }
            elif proxy_type == 'trojan':
                return {
                    'name': name,
                    'type': 'trojan',
                    'address': proxy.get('server', ''),
                    'port': int(proxy.get('port', 0)),
                    'password': proxy.get('password', ''),
                    'tls': proxy.get('tls', True),
                    'sni': proxy.get('sni', ''),
                    'country': self._extract_country_from_name(name),
                    'region': self._extract_region_from_name(name)
                }
            elif proxy_type == 'ss':
                return {
                    'name': name,
                    'type': 'ss',
                    'address': proxy.get('server', ''),
                    'port': int(proxy.get('port', 0)),
                    'encryption': proxy.get('cipher', ''),
                    'password': proxy.get('password', ''),
                    'country': self._extract_country_from_name(name),
                    'region': self._extract_region_from_name(name)
                }
        except Exception as e:
            print(f"代理配置解析失败: {e}")
        
        return None