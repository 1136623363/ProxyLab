from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.models import Node, NodeFilter, OutputFormat

class BaseOutputGenerator(ABC):
    """Base class for output generators"""
    
    def __init__(self):
        self.supported_formats = []
    
    @abstractmethod
    def generate(self, nodes: List[Node], filter_config: Optional[NodeFilter] = None) -> str:
        """Generate output content from nodes"""
        pass
    
    def filter_nodes(self, nodes: List[Node], filter_config: Optional[NodeFilter] = None) -> List[Node]:
        """Filter nodes based on configuration"""
        if not filter_config:
            return nodes
        
        filtered_nodes = nodes
        
        # Filter by country
        if filter_config.countries:
            filtered_nodes = [n for n in filtered_nodes if n.country in filter_config.countries]
        
        # Filter by region
        if filter_config.regions:
            filtered_nodes = [n for n in filtered_nodes if n.region in filter_config.regions]
        
        # Filter by node type
        if filter_config.node_types:
            filtered_nodes = [n for n in filtered_nodes if n.node_type in filter_config.node_types]
        
        # Filter by maximum latency
        if filter_config.max_latency is not None:
            filtered_nodes = [n for n in filtered_nodes if n.ping_latency is None or n.ping_latency <= filter_config.max_latency]
        
        # Filter by keywords
        if filter_config.exclude_keywords:
            filtered_nodes = [n for n in filtered_nodes if not any(keyword.lower() in n.name.lower() for keyword in filter_config.exclude_keywords)]
        
        if filter_config.include_keywords:
            filtered_nodes = [n for n in filtered_nodes if any(keyword.lower() in n.name.lower() for keyword in filter_config.include_keywords)]
        
        return filtered_nodes