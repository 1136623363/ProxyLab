import yaml
from typing import List, Dict, Any
from app.output.base import BaseOutputGenerator
from app.models import Node, NodeType

class ClashGenerator(BaseOutputGenerator):
    """Clash configuration generator"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ["clash"]
    
    def generate(self, nodes: List[Dict], filter_config=None) -> str:
        """Generate Clash configuration"""
        filtered_nodes = self.filter_nodes(nodes, filter_config)
        
        proxies = []
        proxy_names = []
        
        for node in filtered_nodes:
            proxy = self._convert_node_to_clash_proxy(node)
            if proxy:
                proxies.append(proxy)
                proxy_names.append(node['name'])
        
        # Generate Clash configuration
        config = {
            'port': 7890,
            'socks-port': 7891,
            'allow-lan': False,
            'mode': 'rule',
            'log-level': 'info',
            'external-controller': '127.0.0.1:9090',
            'proxies': proxies,
            'proxy-groups': [
                {
                    'name': 'Auto Select',
                    'type': 'url-test',
                    'proxies': proxy_names,
                    'url': 'http://www.gstatic.com/generate_204',
                    'interval': 300
                },
                {
                    'name': 'Manual Select',
                    'type': 'select',
                    'proxies': ['Auto Select'] + proxy_names
                }
            ],
            'rules': [
                'DOMAIN-SUFFIX,local,DIRECT',
                'IP-CIDR,127.0.0.0/8,DIRECT',
                'IP-CIDR,172.16.0.0/12,DIRECT',
                'IP-CIDR,192.168.0.0/16,DIRECT',
                'IP-CIDR,10.0.0.0/8,DIRECT',
                'IP-CIDR,17.0.0.0/8,DIRECT',
                'IP-CIDR,100.64.0.0/10,DIRECT',
                'GEOIP,CN,DIRECT',
                'MATCH,Manual Select'
            ]
        }
        
        return yaml.dump(config, default_flow_style=False, allow_unicode=True)
    
    def _convert_node_to_clash_proxy(self, node: Dict) -> Dict[str, Any]:
        """Convert node to Clash proxy configuration"""
        if node['type'] == NodeType.V2RAY:
            return self._convert_v2ray_to_clash(node)
        elif node['type'] == NodeType.TROJAN:
            return self._convert_trojan_to_clash(node)
        elif node['type'] == NodeType.SS:
            return self._convert_ss_to_clash(node)
        elif node['type'] == NodeType.SSR:
            return self._convert_ssr_to_clash(node)
        elif node['type'] == NodeType.VLESS:
            return self._convert_vless_to_clash(node)
        elif node['type'] == NodeType.HYSTERIA2:
            return self._convert_hysteria2_to_clash(node)
        
        return None
    
    def _convert_v2ray_to_clash(self, node: Dict) -> Dict[str, Any]:
        """Convert V2Ray node to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'vmess',
            'server': node['address'],
            'port': node['port'],
            'uuid': node['uuid'],
            'alterId': node['alter_id'] or 0,
            'cipher': 'auto',
            'network': node['network'] or 'tcp'
        }
        
        if node['tls']:
            proxy['tls'] = True
            if node['sni']:
                proxy['servername'] = node['sni']
        
        if node['network'] == 'ws':
            if node['path']:
                proxy['ws-path'] = node['path']
            if node['host']:
                proxy['ws-headers'] = {'Host': node['host']}
        elif node['network'] == 'h2':
            if node['path']:
                proxy['h2-opts'] = {'path': node['path']}
            if node['host']:
                proxy['h2-opts'] = proxy.get('h2-opts', {})
                proxy['h2-opts']['host'] = [node['host']]
        elif node['network'] == 'grpc':
            if node['path']:
                proxy['grpc-opts'] = {'grpc-service-name': node['path']}
        
        return proxy
    
    def _convert_trojan_to_clash(self, node: Dict) -> Dict[str, Any]:
        """Convert Trojan node to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'trojan',
            'server': node['address'],
            'port': node['port'],
            'password': node['password']
        }
        
        if node['tls']:
            proxy['tls'] = True
            if node['sni']:
                proxy['sni'] = node['sni']
        
        return proxy
    
    def _convert_ss_to_clash(self, node: Dict) -> Dict[str, Any]:
        """Convert Shadowsocks node to Clash format"""
        return {
            'name': node['name'],
            'type': 'ss',
            'server': node['address'],
            'port': node['port'],
            'cipher': node['encryption'] or 'aes-256-gcm',
            'password': node['password']
        }
    
    def _convert_ssr_to_clash(self, node: Dict) -> Dict[str, Any]:
        """Convert ShadowsocksR node to Clash format"""
        return {
            'name': node['name'],
            'type': 'ssr',
            'server': node['address'],
            'port': node['port'],
            'cipher': node['encryption'] or 'aes-256-cfb',
            'password': node['password']
        }
    
    def _convert_vless_to_clash(self, node: Dict) -> Dict[str, Any]:
        """Convert VLESS node to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'vless',
            'server': node['address'],
            'port': node['port'],
            'uuid': node['uuid'],
            'network': node.get('network', 'tcp'),
            'flow': node.get('flow', ''),
            'encryption': node.get('encryption', 'none')
        }
        
        # 添加TLS配置
        if node.get('security') == 'tls':
            proxy['tls'] = True
            if node.get('sni'):
                proxy['servername'] = node['sni']
        elif node.get('security') == 'reality':
            proxy['tls'] = True
            proxy['reality-opts'] = {
                'public-key': node.get('public_key', ''),
                'short-id': node.get('short_id', '')
            }
            if node.get('sni'):
                proxy['servername'] = node['sni']
        
        # 添加网络特定配置
        if node.get('network') == 'ws':
            proxy['ws-opts'] = {}
            if node.get('path'):
                proxy['ws-opts']['path'] = node['path']
            if node.get('host'):
                proxy['ws-opts']['headers'] = {'Host': node['host']}
        elif node.get('network') == 'grpc':
            proxy['grpc-opts'] = {}
            if node.get('path'):
                proxy['grpc-opts']['grpc-service-name'] = node['path']
        
        return proxy
    
    def _convert_hysteria2_to_clash(self, node: Dict) -> Dict[str, Any]:
        """Convert Hysteria2 node to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'hysteria2',
            'server': node['address'],
            'port': node['port'],
            'password': node['password']
        }
        
        # 添加可选参数
        if node.get('sni'):
            proxy['sni'] = node['sni']
        
        if node.get('insecure'):
            proxy['skip-cert-verify'] = node['insecure']
        
        if node.get('pin_sha256'):
            proxy['pinSHA256'] = node['pin_sha256']
        
        if node.get('obfs'):
            proxy['obfs'] = node['obfs']
            if node.get('obfs_password'):
                proxy['obfs-password'] = node['obfs_password']
        
        if node.get('auth'):
            proxy['auth'] = node['auth']
        
        if node.get('up'):
            proxy['up'] = node['up']
        
        if node.get('down'):
            proxy['down'] = node['down']
        
        if node.get('fast_open'):
            proxy['fast-open'] = node['fast_open']
        
        if node.get('lazy'):
            proxy['lazy'] = node['lazy']
        
        return proxy