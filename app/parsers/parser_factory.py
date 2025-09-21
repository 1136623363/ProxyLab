from typing import List, Dict, Any
from app.parsers.base import BaseParser
from app.parsers.v2ray_parser import V2RayParser
from app.parsers.trojan_parser import TrojanParser
from app.parsers.ss_parser import SSParser
from app.parsers.clash_parser import ClashParser
from app.parsers.vless_parser import VLESSParser
from app.parsers.hysteria2_parser import Hysteria2Parser
from app.parsers.subscription_fetcher import SubscriptionFetcher
from app.models import InputType

class ParserFactory:
    """Parser factory class"""
    
    def __init__(self):
        self.parsers = {
            InputType.URL: [V2RayParser(), TrojanParser(), SSParser(), ClashParser(), VLESSParser(), Hysteria2Parser()],
            InputType.YAML: [ClashParser()],
            InputType.JSON: [V2RayParser(), ClashParser()],
            InputType.TEXT: [V2RayParser(), TrojanParser(), SSParser(), ClashParser(), VLESSParser(), Hysteria2Parser()],
        }
        self.subscription_fetcher = SubscriptionFetcher()
    
    def parse_content(self, content: str, input_type: InputType) -> List[Dict[str, Any]]:
        """Parse content"""
        all_nodes = []
        
        # 如果是URL类型，先获取订阅内容
        if input_type == InputType.URL:
            success, fetched_content, error = self.subscription_fetcher.fetch_subscription(content)
            if not success:
                print(f"获取订阅失败: {error}")
                # 返回空列表而不是抛出异常
                return []
            content = fetched_content
            # 自动检测获取到的内容类型
            input_type = self.detect_input_type(content)
        
        parsers = self.parsers.get(input_type, [])
        
        for parser in parsers:
            try:
                nodes = parser.parse(content)
                all_nodes.extend(nodes)
            except Exception as e:
                print(f"Parser {parser.__class__.__name__} failed: {e}")
                continue
        
        # Remove duplicates
        unique_nodes = self._deduplicate_nodes(all_nodes)
        
        return unique_nodes
    
    def _deduplicate_nodes(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate nodes"""
        seen = set()
        unique_nodes = []
        
        for node in nodes:
            # Use address, port, type as unique identifier
            key = (node.get('address'), node.get('port'), node.get('type'))
            if key not in seen:
                seen.add(key)
                unique_nodes.append(node)
        
        return unique_nodes
    
    def detect_input_type(self, content: str) -> InputType:
        """Auto-detect input type"""
        content = content.strip()
        
        # Check if it's a URL
        if content.startswith(('http://', 'https://')):
            return InputType.URL
        
        # Check if it's YAML
        if content.startswith('proxies:') or content.startswith('proxy-groups:') or 'proxies:' in content:
            return InputType.YAML
        
        # Check if it's JSON
        if content.startswith('{') or content.startswith('['):
            return InputType.JSON
        
        # Check if it's vmess link
        if 'vmess://' in content:
            return InputType.TEXT
        
        # Check if it's trojan link
        if 'trojan://' in content:
            return InputType.TEXT
        
        # Check if it's ss link
        if 'ss://' in content:
            return InputType.TEXT
        
        # Check if it's vless link
        if 'vless://' in content:
            return InputType.TEXT
        
        # Check if it's hysteria2 link
        if 'hy2://' in content:
            return InputType.TEXT
        
        # Default to text
        return InputType.TEXT
    
    def get_parser(self, input_type: InputType) -> BaseParser:
        """Get parser for specified type"""
        parsers = self.parsers.get(input_type, [])
        if parsers:
            return parsers[0]  # Return first available parser
        return None
    