import asyncio
import aiohttp
import time
import socket
from typing import List, Dict, Any, Optional
from app.models import Node, NodeStatus, NodeCheckResult
import statistics

class NodeChecker:
    """Node checker"""
    
    def __init__(self):
        self.timeout = 10  # Connection timeout (seconds)
        self.ping_timeout = 5  # Ping timeout (seconds)
    
    async def check_node(self, node: Node) -> NodeCheckResult:
        """Check single node"""
        result = NodeCheckResult(
            node_id=node.id,
            status=NodeStatus.UNKNOWN
        )
        
        try:
            # Check connectivity
            is_connected = await self._check_connectivity(node)
            
            if is_connected:
                result.status = NodeStatus.ACTIVE
                
                # Check latency
                latency = await self._check_latency(node)
                if latency is not None:
                    result.ping_latency = latency
            else:
                result.status = NodeStatus.INACTIVE
                
        except Exception as e:
            result.status = NodeStatus.ERROR
            result.error_message = str(e)
        
        return result
    
    async def check_nodes_batch(self, node_ids: List[int], max_concurrent: int = 10) -> Dict[int, Dict[str, Any]]:
        """Check multiple nodes by IDs (optimized for batch processing)"""
        results = {}
        
        # 限制并发数量，避免资源耗尽
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def check_with_semaphore(node_id: int):
            async with semaphore:
                return await self._check_node_connectivity_batch(node_id)
        
        # 批量检测节点连接性
        tasks = [check_with_semaphore(node_id) for node_id in node_ids]
        
        # 并发执行所有检测任务
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for i, result in enumerate(batch_results):
            node_id = node_ids[i]
            if isinstance(result, Exception):
                results[node_id] = {
                    'success': False,
                    'error': str(result),
                    'latency': None
                }
            else:
                results[node_id] = result
        
        return results
    
    async def _check_node_connectivity_batch(self, node_id: int) -> Dict[str, Any]:
        """Check single node connectivity (optimized for batch)"""
        try:
            # 从数据库获取节点信息
            from app.database import SessionLocal, Node
            db = SessionLocal()
            try:
                node = db.query(Node).filter(Node.id == node_id).first()
                if not node:
                    return {
                        'success': False,
                        'error': 'Node not found',
                        'latency': None
                    }
                
                # 检查连接性
                is_connected = await self._check_connectivity(node)
                if is_connected:
                    # 检查延迟
                    latency = await self._check_latency(node)
                    return {
                        'success': True,
                        'latency': latency or 0.0
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Connection failed',
                        'latency': None
                    }
            finally:
                db.close()
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'latency': None
            }
    
    async def _check_connectivity(self, node: Node) -> bool:
        """Check node connectivity"""
        try:
            # Use asyncio for connection
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(node.address, node.port),
                timeout=self.timeout
            )
            writer.close()
            await writer.wait_closed()
            return True
        except Exception:
            return False
    
    async def _check_latency(self, node: Node) -> Optional[float]:
        """Check node latency using asyncio"""
        try:
            # 使用asyncio进行延迟检测
            start_time = time.time()
            
            # 创建异步连接
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(node.address, node.port),
                timeout=self.ping_timeout
            )
            end_time = time.time()
            
            # 关闭连接
            writer.close()
            await writer.wait_closed()
            
            # 计算延迟（毫秒）
            latency = (end_time - start_time) * 1000
            return round(latency, 2)  # 保留2位小数
                
        except Exception:
            return None
    
    