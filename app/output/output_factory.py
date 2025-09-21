from typing import List
from app.output.base import BaseOutputGenerator
from app.output.clash_generator import ClashGenerator
from app.output.enhanced_clash_generator import EnhancedClashGenerator
from app.output.v2rayn_generator import V2RayNGenerator
from app.output.raw_generator import RawGenerator
from app.models import OutputFormat, Node, NodeFilter

class OutputFactory:
    """输出生成器工厂类"""
    
    def __init__(self):
        self.generators = {
            OutputFormat.CLASH: ClashGenerator(),
            OutputFormat.CLASH_ENHANCED: EnhancedClashGenerator(),
            OutputFormat.V2RAYN: V2RayNGenerator(),
            OutputFormat.RAW: RawGenerator(),
        }
    
    def generate_output(self, nodes: List[Node], output_format: OutputFormat, filter_config: NodeFilter = None) -> str:
        """生成指定格式输出"""
        generator = self.generators.get(output_format)
        if not generator:
            raise ValueError(f"不支持的输出格式: {output_format}")
        
        return generator.generate(nodes, filter_config)
    
    def get_generator(self, output_format: OutputFormat) -> BaseOutputGenerator:
        """获取指定格式的生成器"""
        return self.generators.get(output_format)
    
    def get_supported_formats(self) -> List[OutputFormat]:
        """获取支持的输出格式列表"""
        return list(self.generators.keys())