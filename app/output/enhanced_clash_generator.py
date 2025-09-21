import yaml
from typing import List, Dict, Any
from app.output.base import BaseOutputGenerator
from app.models import Node, NodeType

class EnhancedClashGenerator(BaseOutputGenerator):
    """Enhanced Clash configuration generator with advanced features"""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ["clash_enhanced"]
    
    def generate(self, nodes: List[Dict], filter_config=None) -> str:
        """Generate enhanced Clash configuration"""
        # Convert Node objects to dict format if needed
        if nodes and hasattr(nodes[0], 'name'):
            nodes = [self._node_to_dict(node) for node in nodes]
        
        filtered_nodes = self.filter_nodes(nodes, filter_config)
        
        proxies = []
        proxy_names = []
        
        for node in filtered_nodes:
            proxy = self._convert_node_to_clash_proxy(node)
            if proxy:
                proxies.append(proxy)
                proxy_names.append(node['name'])
        
        # Generate enhanced Clash configuration
        config = {
            'mixed-port': 7890,
            'allow-lan': True,
            'mode': 'rule',
            'log-level': 'info',
            'external-controller': ':9090',
            
            # Enhanced DNS configuration
            'dns': {
                'enable': True,
                'listen': '0.0.0.0:1053',
                'default-nameserver': [
                    '223.5.5.5',
                    '8.8.8.8',
                    '1.1.1.1'
                ],
                'proxy-server-nameserver': [
                    'https://dns.alidns.com/dns-query'
                ],
                'nameserver-policy': {
                    'geosite:gfw,geolocation-!cn': [
                        'https://1.1.1.1/dns-query#🚀 节点选择',
                        'https://1.0.0.1/dns-query#🚀 节点选择',
                        'https://8.8.8.8/dns-query#🚀 节点选择'
                    ]
                },
                'nameserver': [
                    'https://dns.alidns.com/dns-query',
                    'https://doh.pub/dns-query',
                    'https://8.8.8.8/dns-query#🚀 节点选择'
                ],
                'fallback': [
                    'https://1.1.1.1/dns-query#🚀 节点选择',
                    'https://1.0.0.1/dns-query#🚀 节点选择',
                    'https://8.8.8.8/dns-query#🚀 节点选择'
                ],
                'fallback-filter': {
                    'geoip': False,
                    'geoip-code': 'CN',
                    'ipcidr': [
                        '240.0.0.0/4'
                    ]
                },
                'fake-ip-filter': [
                    '+.lan',
                    '+.microsoft*.com',
                    'localhost.ptlogin2.qq.com'
                ]
            },
            
            'proxies': proxies,
            'proxy-groups': self._generate_proxy_groups(proxy_names),
            'rules': self._generate_rules()
        }
        
        return yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    def _node_to_dict(self, node) -> Dict:
        """Convert Node object to dictionary"""
        return {
            'name': node.name,
            'node_type': node.node_type,
            'address': node.address,
            'port': node.port,
            'encryption': node.encryption,
            'password': node.password,
            'uuid': node.uuid,
            'alter_id': node.alter_id,
            'network': node.network,
            'path': node.path,
            'host': node.host,
            'tls': node.tls,
            'sni': node.sni,
            'country': node.country,
            'region': node.region
        }
    
    def _generate_proxy_groups(self, proxy_names: List[str]) -> List[Dict]:
        """Generate enhanced proxy groups"""
        if not proxy_names:
            return []
        
        groups = [
            # Auto selection groups
            {
                'name': '♻️ 自动选择',
                'type': 'url-test',
                'proxies': proxy_names,
                'url': 'https://www.gstatic.com/generate_204',
                'interval': 300,
                'tolerance': 50
            },
            {
                'name': '🚀 手动切换1',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '🚀 手动切换2',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '🔯 故障转移',
                'type': 'fallback',
                'proxies': proxy_names,
                'url': 'https://www.gstatic.com/generate_204',
                'interval': 300
            },
            {
                'name': '🔮 负载均衡',
                'type': 'load-balance',
                'proxies': proxy_names,
                'url': 'https://www.gstatic.com/generate_204',
                'interval': 300,
                'strategy': 'consistent-hashing'
            }
        ]
        
        # Add region-based groups
        regions = self._group_nodes_by_region(proxy_names)
        for region, names in regions.items():
            if len(names) > 1:  # Only create groups with multiple nodes
                groups.append({
                    'name': region,
                    'type': 'url-test',
                    'proxies': names,
                    'url': 'https://www.gstatic.com/generate_204',
                    'interval': 300
                })
        
        # Add rule-based groups
        groups.extend([
            {
                'name': '📲 电报消息',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '💬 Ai平台',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '📹 油管视频',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '🎥 奈飞视频',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '📺 哔哩哔哩',
                'type': 'select',
                'proxies': ['🎯 全球直连']
            },
            {
                'name': '🌍 国外媒体',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': '🌏 国内媒体',
                'type': 'select',
                'proxies': ['🎯 全球直连']
            },
            {
                'name': '📢 谷歌服务',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            },
            {
                'name': 'Ⓜ️ 微软服务',
                'type': 'select',
                'proxies': ['🎯 全球直连']
            },
            {
                'name': '🍎 苹果服务',
                'type': 'select',
                'proxies': ['🎯 全球直连']
            },
            {
                'name': '🎮 游戏平台',
                'type': 'select',
                'proxies': ['🎯 全球直连']
            },
            {
                'name': '🎶 网易音乐',
                'type': 'select',
                'proxies': ['🎯 全球直连']
            },
            {
                'name': '🎯 全球直连',
                'type': 'select',
                'proxies': ['DIRECT']
            },
            {
                'name': '🛑 广告拦截',
                'type': 'select',
                'proxies': ['REJECT']
            },
            {
                'name': '🐟 漏网之鱼',
                'type': 'select',
                'proxies': ['♻️ 自动选择'] + proxy_names
            }
        ])
        
        return groups
    
    def _group_nodes_by_region(self, proxy_names: List[str]) -> Dict[str, List[str]]:
        """Group nodes by region based on name patterns"""
        regions = {}
        
        for name in proxy_names:
            if '🇭🇰' in name or 'HK' in name or 'Hong' in name or 'Kong' in name or '港' in name:
                regions.setdefault('🇭🇰 香港节点', []).append(name)
            elif '🇯🇵' in name or 'JP' in name or 'Japan' in name or '东京' in name or '大阪' in name or '日' in name:
                regions.setdefault('🇯🇵 日本节点', []).append(name)
            elif '🇺🇸' in name or 'US' in name or 'America' in name or '美' in name:
                regions.setdefault('🇺🇸 美国节点', []).append(name)
            elif '🇸🇬' in name or 'SG' in name or 'Singapore' in name or '狮城' in name:
                regions.setdefault('🇸🇬 狮城节点', []).append(name)
            elif '🇰🇷' in name or 'KR' in name or 'Korea' in name or '韩' in name:
                regions.setdefault('🇰🇷 韩国节点', []).append(name)
            elif '🇹🇼' in name or 'TW' in name or 'Taiwan' in name or '台' in name:
                regions.setdefault('🇹🇼 台湾节点', []).append(name)
        
        return regions
    
    def _generate_rules(self) -> List[str]:
        """Generate comprehensive rules"""
        return [
            # Local network rules
            'DOMAIN-SUFFIX,local,🎯 全球直连',
            'IP-CIDR,127.0.0.0/8,🎯 全球直连',
            'IP-CIDR,172.16.0.0/12,🎯 全球直连',
            'IP-CIDR,192.168.0.0/16,🎯 全球直连',
            'IP-CIDR,10.0.0.0/8,🎯 全球直连',
            'IP-CIDR,17.0.0.0/8,🎯 全球直连',
            'IP-CIDR,100.64.0.0/10,🎯 全球直连',
            
            # Telegram
            'DOMAIN-SUFFIX,t.me,📲 电报消息',
            'DOMAIN-SUFFIX,tdesktop.com,📲 电报消息',
            'DOMAIN-SUFFIX,telegra.ph,📲 电报消息',
            'DOMAIN-SUFFIX,telegram.org,📲 电报消息',
            
            # AI Platforms
            'DOMAIN-SUFFIX,openai.com,💬 Ai平台',
            'DOMAIN-SUFFIX,chatgpt.com,💬 Ai平台',
            'DOMAIN-SUFFIX,claude.ai,💬 Ai平台',
            'DOMAIN-SUFFIX,anthropic.com,💬 Ai平台',
            'DOMAIN-SUFFIX,poe.com,💬 Ai平台',
            
            # YouTube
            'DOMAIN-SUFFIX,youtube.com,📹 油管视频',
            'DOMAIN-SUFFIX,googlevideo.com,📹 油管视频',
            'DOMAIN-SUFFIX,youtube-nocookie.com,📹 油管视频',
            'DOMAIN-SUFFIX,ytimg.com,📹 油管视频',
            
            # Netflix
            'DOMAIN-SUFFIX,netflix.com,🎥 奈飞视频',
            'DOMAIN-SUFFIX,nflximg.net,🎥 奈飞视频',
            'DOMAIN-SUFFIX,nflxext.com,🎥 奈飞视频',
            'DOMAIN-SUFFIX,nflxso.net,🎥 奈飞视频',
            
            # Bilibili
            'DOMAIN-SUFFIX,bilibili.com,📺 哔哩哔哩',
            'DOMAIN-SUFFIX,bilivideo.com,📺 哔哩哔哩',
            'DOMAIN-SUFFIX,hdslb.com,📺 哔哩哔哩',
            
            # Google Services
            'DOMAIN-SUFFIX,google.com,📢 谷歌服务',
            'DOMAIN-SUFFIX,googleapis.com,📢 谷歌服务',
            'DOMAIN-SUFFIX,googleusercontent.com,📢 谷歌服务',
            'DOMAIN-SUFFIX,gstatic.com,📢 谷歌服务',
            'DOMAIN-SUFFIX,googletagmanager.com,📢 谷歌服务',
            'DOMAIN-SUFFIX,googletagservices.com,📢 谷歌服务',
            
            # Microsoft Services
            'DOMAIN-SUFFIX,microsoft.com,Ⓜ️ 微软服务',
            'DOMAIN-SUFFIX,office.com,Ⓜ️ 微软服务',
            'DOMAIN-SUFFIX,outlook.com,Ⓜ️ 微软服务',
            'DOMAIN-SUFFIX,onedrive.com,Ⓜ️ 微软服务',
            'DOMAIN-SUFFIX,skype.com,Ⓜ️ 微软服务',
            
            # Apple Services
            'DOMAIN-SUFFIX,apple.com,🍎 苹果服务',
            'DOMAIN-SUFFIX,icloud.com,🍎 苹果服务',
            'DOMAIN-SUFFIX,itunes.com,🍎 苹果服务',
            'DOMAIN-SUFFIX,appstore.com,🍎 苹果服务',
            
            # Gaming Platforms
            'DOMAIN-SUFFIX,steam.com,🎮 游戏平台',
            'DOMAIN-SUFFIX,steampowered.com,🎮 游戏平台',
            'DOMAIN-SUFFIX,epicgames.com,🎮 游戏平台',
            'DOMAIN-SUFFIX,origin.com,🎮 游戏平台',
            'DOMAIN-SUFFIX,ea.com,🎮 游戏平台',
            'DOMAIN-SUFFIX,ubisoft.com,🎮 游戏平台',
            
            # Music Services
            'DOMAIN-SUFFIX,music.163.com,🎶 网易音乐',
            'DOMAIN-SUFFIX,music.126.net,🎶 网易音乐',
            'DOMAIN-SUFFIX,spotify.com,🎶 网易音乐',
            'DOMAIN-SUFFIX,spotifycdn.com,🎶 网易音乐',
            
            # China Mainland
            'GEOIP,CN,🎯 全球直连',
            
            # Final fallback
            'MATCH,🐟 漏网之鱼'
        ]
    
    def _convert_node_to_clash_proxy(self, node: Dict) -> Dict:
        """Convert node to Clash proxy format"""
        node_type = node.get('node_type', '').lower()
        
        if node_type == 'ss':
            return self._convert_ss_to_clash(node)
        elif node_type == 'ssr':
            return self._convert_ssr_to_clash(node)
        elif node_type == 'v2ray':
            return self._convert_v2ray_to_clash(node)
        elif node_type == 'trojan':
            return self._convert_trojan_to_clash(node)
        elif node_type == 'vless':
            return self._convert_vless_to_clash(node)
        elif node_type == 'hysteria2':
            return self._convert_hysteria2_to_clash(node)
        else:
            return None
    
    def _convert_ss_to_clash(self, node: Dict) -> Dict:
        """Convert Shadowsocks to Clash format"""
        return {
            'name': node['name'],
            'type': 'ss',
            'server': node['address'],
            'port': node['port'],
            'cipher': node.get('encryption', 'aes-256-gcm'),
            'password': node.get('password', ''),
            'udp': True
        }
    
    def _convert_ssr_to_clash(self, node: Dict) -> Dict:
        """Convert ShadowsocksR to Clash format"""
        return {
            'name': node['name'],
            'type': 'ssr',
            'server': node['address'],
            'port': node['port'],
            'cipher': node.get('encryption', 'aes-256-cfb'),
            'password': node.get('password', ''),
            'obfs': node.get('obfs', 'plain'),
            'protocol': node.get('protocol', 'origin'),
            'udp': True
        }
    
    def _convert_v2ray_to_clash(self, node: Dict) -> Dict:
        """Convert V2Ray to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'vmess',
            'server': node['address'],
            'port': node['port'],
            'uuid': node.get('uuid', ''),
            'alterId': node.get('alter_id', 0),
            'cipher': 'auto',
            'udp': True
        }
        
        # Add network configuration
        network = node.get('network', 'tcp')
        proxy['network'] = network
        
        if network == 'ws':
            proxy['ws-opts'] = {
                'path': node.get('path', '/'),
                'headers': {
                    'Host': node.get('host', node['address'])
                }
            }
        elif network == 'h2':
            proxy['h2-opts'] = {
                'path': node.get('path', '/'),
                'host': [node.get('host', node['address'])]
            }
        elif network == 'grpc':
            proxy['grpc-opts'] = {
                'grpc-service-name': node.get('path', '')
            }
        
        # Add TLS configuration
        if node.get('tls', False):
            proxy['tls'] = True
            if node.get('sni'):
                proxy['servername'] = node['sni']
        
        return proxy
    
    def _convert_trojan_to_clash(self, node: Dict) -> Dict:
        """Convert Trojan to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'trojan',
            'server': node['address'],
            'port': node['port'],
            'password': node.get('password', ''),
            'udp': True
        }
        
        # Add TLS configuration
        if node.get('tls', True):  # Trojan requires TLS by default
            proxy['tls'] = True
            if node.get('sni'):
                proxy['sni'] = node['sni']
        
        return proxy
    
    def _convert_vless_to_clash(self, node: Dict) -> Dict:
        """Convert VLESS to Clash format"""
        proxy = {
            'name': node['name'],
            'type': 'vless',
            'server': node['address'],
            'port': node['port'],
            'uuid': node.get('uuid', ''),
            'udp': True
        }
        
        # Add network configuration
        network = node.get('network', 'tcp')
        proxy['network'] = network
        
        if network == 'ws':
            proxy['ws-opts'] = {
                'path': node.get('path', '/'),
                'headers': {
                    'Host': node.get('host', node['address'])
                }
            }
        elif network == 'grpc':
            proxy['grpc-opts'] = {
                'grpc-service-name': node.get('path', '')
            }
        
        # Add TLS configuration
        if node.get('tls', False):
            proxy['tls'] = True
            if node.get('sni'):
                proxy['servername'] = node['sni']
        
        return proxy
    
    def _convert_hysteria2_to_clash(self, node: Dict) -> Dict:
        """Convert Hysteria2 to Clash format"""
        return {
            'name': node['name'],
            'type': 'hysteria2',
            'server': node['address'],
            'port': node['port'],
            'password': node.get('password', ''),
            'obfs': node.get('obfs', ''),
            'skip-cert-verify': not node.get('tls', True),
            'udp': True
        }
