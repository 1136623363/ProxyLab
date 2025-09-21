import base64
from typing import List, Dict, Any
from app.output.base import BaseOutputGenerator
from app.models import Node, NodeType

class RawGenerator(BaseOutputGenerator):
    """Raw configuration generator"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ["raw"]
    
    def generate(self, nodes: List[Dict], filter_config=None) -> str:
        """Generate raw configuration"""
        filtered_nodes = self.filter_nodes(nodes, filter_config)
        
        links = []
        
        for node in filtered_nodes:
            if node['type'] == NodeType.V2RAY:
                link = self._convert_v2ray_to_raw(node)
                if link:
                    links.append(link)
            elif node['type'] == NodeType.TROJAN:
                link = self._convert_trojan_to_raw(node)
                if link:
                    links.append(link)
            elif node['type'] == NodeType.SS:
                link = self._convert_ss_to_raw(node)
                if link:
                    links.append(link)
            elif node['type'] == NodeType.SSR:
                link = self._convert_ssr_to_raw(node)
                if link:
                    links.append(link)
            elif node['type'] == NodeType.VLESS:
                link = self._convert_vless_to_raw(node)
                if link:
                    links.append(link)
            elif node['type'] == NodeType.HYSTERIA2:
                link = self._convert_hysteria2_to_raw(node)
                if link:
                    links.append(link)
        
        return '\n'.join(links)
    
    def _convert_v2ray_to_raw(self, node: Dict) -> str:
        """Convert V2Ray node to raw format"""
        import json
        
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
        
        # Encode as base64
        config_json = json.dumps(config, ensure_ascii=False)
        encoded_config = base64.b64encode(config_json.encode('utf-8')).decode('utf-8')
        
        return f"vmess://{encoded_config}"
    
    def _convert_trojan_to_raw(self, node: Dict) -> str:
        """Convert Trojan node to raw format"""
        from urllib.parse import quote
        
        # Build trojan link
        password = quote(node['password'] or '')
        hostname = node['address']
        port = node['port']
        name = quote(node['name'])
        
        # Build query parameters
        params = []
        if node['sni']:
            params.append(f'sni={node["sni"]}')
        
        query_string = '&'.join(params) if params else ''
        fragment = f'#{name}' if name else ''
        
        if query_string:
            return f"trojan://{password}@{hostname}:{port}?{query_string}{fragment}"
        else:
            return f"trojan://{password}@{hostname}:{port}{fragment}"
    
    def _convert_ss_to_raw(self, node: Dict) -> str:
        """Convert Shadowsocks node to raw format"""
        import base64
        from urllib.parse import quote
        
        # Build SS link
        method = node['encryption'] or 'aes-256-gcm'
        password = node['password'] or ''
        hostname = node['address']
        port = node['port']
        name = quote(node['name'])
        
        # Build authentication info
        auth = f"{method}:{password}"
        encoded_auth = base64.b64encode(auth.encode('utf-8')).decode('utf-8')
        
        fragment = f'#{name}' if name else ''
        
        return f"ss://{encoded_auth}@{hostname}:{port}{fragment}"
    
    def _convert_ssr_to_raw(self, node: Dict) -> str:
        """Convert ShadowsocksR node to raw format"""
        import base64
        from urllib.parse import quote
        
        # Build SSR link
        hostname = node['address']
        port = node['port']
        protocol = 'origin'  # SSR protocol
        method = node['encryption'] or 'aes-256-cfb'
        obfs = 'plain'  # SSR obfuscation
        password = node['password'] or ''
        name = quote(node['name'])
        
        # Build authentication info
        auth = f"{hostname}:{port}:{protocol}:{method}:{obfs}:{base64.b64encode(password.encode('utf-8')).decode('utf-8')}"
        encoded_auth = base64.b64encode(auth.encode('utf-8')).decode('utf-8')
        
        fragment = f'#{name}' if name else ''
        
        return f"ssr://{encoded_auth}{fragment}"
    
    def _convert_vless_to_raw(self, node: Dict) -> str:
        """Convert VLESS node to raw format"""
        from urllib.parse import quote, urlencode
        
        # Build VLESS link
        uuid = node['uuid'] or ''
        hostname = node['address']
        port = node['port']
        name = quote(node['name'])
        
        # Build query parameters
        query_params = {}
        
        if 'security' in node:
            query_params['security'] = node['security']
        
        if 'sni' in node:
            query_params['sni'] = node['sni']
        
        if 'fingerprint' in node:
            query_params['fp'] = node['fingerprint']
        
        if 'public_key' in node:
            query_params['pbk'] = node['public_key']
        
        if 'short_id' in node:
            query_params['sid'] = node['short_id']
        
        if 'network' in node:
            query_params['type'] = node['network']
        
        if 'flow' in node:
            query_params['flow'] = node['flow']
        
        if 'encryption' in node:
            query_params['encryption'] = node['encryption']
        
        if 'path' in node:
            query_params['path'] = node['path']
        
        if 'host' in node:
            query_params['host'] = node['host']
        
        query_string = urlencode(query_params) if query_params else ''
        fragment = f'#{name}' if name else ''
        
        return f"vless://{uuid}@{hostname}:{port}{'?' + query_string if query_string else ''}{fragment}"
    
    def _convert_hysteria2_to_raw(self, node: Dict) -> str:
        """Convert Hysteria2 node to raw format"""
        from urllib.parse import quote, urlencode
        
        # Build Hysteria2 link
        password = node['password'] or ''
        hostname = node['address']
        port = node['port']
        name = quote(node['name'])
        
        # Build query parameters
        query_params = {}
        
        if 'sni' in node:
            query_params['sni'] = node['sni']
        
        if 'insecure' in node:
            query_params['insecure'] = str(node['insecure']).lower()
        
        if 'pin_sha256' in node:
            query_params['pinSHA256'] = node['pin_sha256']
        
        if 'obfs' in node:
            query_params['obfs'] = node['obfs']
        
        if 'obfs_password' in node:
            query_params['obfs-password'] = node['obfs_password']
        
        if 'auth' in node:
            query_params['auth'] = node['auth']
        
        if 'up' in node:
            query_params['up'] = node['up']
        
        if 'down' in node:
            query_params['down'] = node['down']
        
        if 'fast_open' in node:
            query_params['fastOpen'] = str(node['fast_open']).lower()
        
        if 'lazy' in node:
            query_params['lazy'] = str(node['lazy']).lower()
        
        query_string = urlencode(query_params) if query_params else ''
        fragment = f'#{name}' if name else ''
        
        return f"hy2://{password}@{hostname}:{port}{'?' + query_string if query_string else ''}{fragment}"