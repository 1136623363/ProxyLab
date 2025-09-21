import json
import base64
from typing import List, Dict, Any
from app.output.base import BaseOutputGenerator
from app.models import Node, NodeType

class V2RayNGenerator(BaseOutputGenerator):
    """V2RayN configuration generator"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ["v2rayn"]
    
    def generate(self, nodes: List[Dict], filter_config=None) -> str:
        """Generate V2RayN configuration"""
        filtered_nodes = self.filter_nodes(nodes, filter_config)
        
        v2ray_configs = []
        
        for node in filtered_nodes:
            if node['type'] == NodeType.V2RAY:
                config = self._convert_v2ray_to_v2rayn(node)
                if config:
                    v2ray_configs.append(config)
            elif node['type'] == NodeType.TROJAN:
                config = self._convert_trojan_to_v2rayn(node)
                if config:
                    v2ray_configs.append(config)
            elif node['type'] == NodeType.SS:
                config = self._convert_ss_to_v2rayn(node)
                if config:
                    v2ray_configs.append(config)
        
        # Generate V2RayN configuration
        if v2ray_configs:
            # Encode configuration as base64
            config_json = json.dumps(v2ray_configs, ensure_ascii=False)
            encoded_config = base64.b64encode(config_json.encode('utf-8')).decode('utf-8')
            return encoded_config
        
        return ""
    
    def _convert_v2ray_to_v2rayn(self, node: Dict) -> Dict[str, Any]:
        """Convert V2Ray node to V2RayN format"""
        config = {
            'v': '2',
            'ps': node['name'],
            'add': node['address'],
            'port': str(node['port']),
            'id': node['uuid'],
            'aid': str(node['alter_id'] or 0),
            'net': node['network'] or 'tcp',
            'type': 'none',
            'host': node['host'] or '',
            'path': node['path'] or '',
            'tls': 'tls' if node['tls'] else ''
        }
        
        if node['sni']:
            config['sni'] = node['sni']
        
        return config
    
    def _convert_trojan_to_v2rayn(self, node: Dict) -> Dict[str, Any]:
        """Convert Trojan node to V2RayN format"""
        # V2RayN has limited Trojan support, so we create a basic configuration
        config = {
            'v': '2',
            'ps': node['name'],
            'add': node['address'],
            'port': str(node['port']),
            'id': node['password'],
            'aid': '0',
            'net': 'tcp',
            'type': 'none',
            'host': '',
            'path': '',
            'tls': 'tls'
        }
        
        if node['sni']:
            config['sni'] = node['sni']
        
        return config
    
    def _convert_ss_to_v2rayn(self, node: Dict) -> Dict[str, Any]:
        """Convert Shadowsocks node to V2RayN format"""
        # V2RayN has limited SS support, so we create a basic configuration
        config = {
            'v': '2',
            'ps': node['name'],
            'add': node['address'],
            'port': str(node['port']),
            'id': node['password'],
            'aid': '0',
            'net': 'tcp',
            'type': 'none',
            'host': '',
            'path': '',
            'tls': ''
        }
        
        return config