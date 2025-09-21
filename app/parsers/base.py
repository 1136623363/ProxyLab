from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models import Node, NodeType, InputType
import re
import ipaddress
import base64

class BaseParser(ABC):
    """Base parser class"""
    
    def __init__(self):
        self.supported_types = []
    
    @abstractmethod
    def parse(self, content: str) -> List[Dict[str, Any]]:
        """Parse content and return node list"""
        pass
    
    def validate_node(self, node_data: Dict[str, Any]) -> bool:
        """Validate if node data is valid"""
        required_fields = ['name', 'address', 'port']
        
        # Check required fields
        for field in required_fields:
            if field not in node_data or not node_data[field]:
                return False
        
        # Validate IP address or domain
        address = node_data['address']
        if not self._is_valid_address(address):
            return False
        
        # Validate port
        port = node_data['port']
        if not isinstance(port, int) or port < 1 or port > 65535:
            return False
        
        return True
    
    def _is_valid_address(self, address: str) -> bool:
        """Validate if address is valid"""
        if not address:
            return False
        
        # Check if it's a valid IP address
        try:
            ipaddress.ip_address(address)
            return True
        except ValueError:
            pass
        
        # Check if it's a valid domain
        if self._is_valid_domain(address):
            return True
        
        return False
    
    def _is_valid_domain(self, domain: str) -> bool:
        """Validate if domain is valid"""
        if not domain:
            return False
        
        # Simple domain validation
        domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(domain_pattern, domain))
    
    def _extract_country_from_name(self, name: str) -> Optional[str]:
        """Extract country information from node name"""
        # Common country code mapping
        country_mapping = {
            'US': ['美国', 'USA', 'United States'],
            'HK': ['香港', 'Hong Kong', 'HK'],
            'SG': ['新加坡', 'Singapore', 'SG'],
            'JP': ['日本', 'Japan', 'JP'],
            'TW': ['台湾', 'Taiwan', 'TW'],
            'UK': ['英国', 'United Kingdom', 'UK'],
            'DE': ['德国', 'Germany', 'DE'],
            'FR': ['法国', 'France', 'FR'],
            'CA': ['加拿大', 'Canada', 'CA'],
            'AU': ['澳大利亚', 'Australia', 'AU']
        }
        
        name_upper = name.upper()
        for country_code, keywords in country_mapping.items():
            for keyword in keywords:
                if keyword.upper() in name_upper:
                    return country_code
        
        return None
    
    def _extract_region_from_name(self, name: str) -> Optional[str]:
        """Extract region information from node name"""
        # Common region keywords
        region_keywords = {
            'Asia': ['亚洲', 'Asia', 'AS'],
            'Europe': ['欧洲', 'Europe', 'EU'],
            'North America': ['北美', 'North America', 'NA'],
            'South America': ['南美', 'South America', 'SA'],
            'Africa': ['非洲', 'Africa', 'AF'],
            'Oceania': ['大洋洲', 'Oceania', 'OC']
        }
        
        name_upper = name.upper()
        for region, keywords in region_keywords.items():
            for keyword in keywords:
                if keyword.upper() in name_upper:
                    return region
        
        return None
    
    def safe_decode_base64(self, encoded_data: str) -> str:
        """安全解码base64数据，尝试多种编码方式"""
        try:
            decoded_bytes = base64.b64decode(encoded_data)
            decoded = None
            
            # 尝试多种编码方式
            for encoding in ['utf-8', 'latin-1', 'cp1252', 'gbk', 'gb2312']:
                try:
                    decoded = decoded_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            # 如果所有编码都失败，使用错误替换模式
            if decoded is None:
                decoded = decoded_bytes.decode('utf-8', errors='replace')
            
            return decoded
        except Exception as e:
            # 如果base64解码失败，返回原始数据
            return encoded_data