from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import Node, InputRecord, NodeStats
from datetime import datetime
import json
from typing import Dict, Any

class StatsService:
    """统计数据服务"""
    
    @staticmethod
    def calculate_node_stats(db: Session, user_id: int, input_record_id: int = None) -> Dict[str, Any]:
        """计算节点统计数据"""
        # 基础查询
        query = db.query(Node).join(InputRecord).filter(
            InputRecord.user_id == user_id,
            InputRecord.is_active == True
        )
        
        if input_record_id:
            query = query.filter(Node.input_record_id == input_record_id)
        
        nodes = query.all()
        
        if not nodes:
            return {
                'total_nodes': 0,
                'active_nodes': 0,
                'inactive_nodes': 0,
                'error_nodes': 0,
                'unknown_nodes': 0,
                'avg_latency': None,
                'min_latency': None,
                'max_latency': None,
                'country_distribution': {},
                'type_distribution': {}
            }
        
        # 统计节点状态
        status_counts = {}
        latencies = []
        country_counts = {}
        type_counts = {}
        
        for node in nodes:
            # 状态统计
            status = node.status or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 延迟统计
            if node.ping_latency is not None:
                latencies.append(node.ping_latency)
            
            # 国家统计
            if node.country:
                country_counts[node.country] = country_counts.get(node.country, 0) + 1
            
            # 类型统计
            node_type = node.node_type or 'unknown'
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        
        # 计算延迟统计
        avg_latency = sum(latencies) / len(latencies) if latencies else None
        min_latency = min(latencies) if latencies else None
        max_latency = max(latencies) if latencies else None
        
        return {
            'total_nodes': len(nodes),
            'active_nodes': status_counts.get('active', 0),
            'inactive_nodes': status_counts.get('inactive', 0),
            'error_nodes': status_counts.get('error', 0),
            'unknown_nodes': status_counts.get('unknown', 0),
            'disabled_nodes': status_counts.get('disabled', 0),
            'avg_latency': round(avg_latency, 2) if avg_latency else None,
            'min_latency': round(min_latency, 2) if min_latency else None,
            'max_latency': round(max_latency, 2) if max_latency else None,
            'country_distribution': country_counts,
            'type_distribution': type_counts
        }
    
    @staticmethod
    def update_node_stats(db: Session, user_id: int, input_record_id: int = None):
        """更新节点统计数据到数据库"""
        try:
            # 计算统计数据
            stats_data = StatsService.calculate_node_stats(db, user_id, input_record_id)
            
            # 查找或创建统计记录
            existing_stats = db.query(NodeStats).filter(
                NodeStats.user_id == user_id,
                NodeStats.input_record_id == input_record_id
            ).first()
            
            if existing_stats:
                # 更新现有记录
                existing_stats.total_nodes = stats_data['total_nodes']
                existing_stats.active_nodes = stats_data['active_nodes']
                existing_stats.inactive_nodes = stats_data['inactive_nodes']
                existing_stats.error_nodes = stats_data['error_nodes']
                existing_stats.unknown_nodes = stats_data['unknown_nodes']
                existing_stats.avg_latency = stats_data['avg_latency']
                existing_stats.min_latency = stats_data['min_latency']
                existing_stats.max_latency = stats_data['max_latency']
                existing_stats.country_distribution = json.dumps(stats_data['country_distribution'])
                existing_stats.type_distribution = json.dumps(stats_data['type_distribution'])
                existing_stats.last_updated = datetime.utcnow()
            else:
                # 创建新记录
                new_stats = NodeStats(
                    user_id=user_id,
                    input_record_id=input_record_id,
                    total_nodes=stats_data['total_nodes'],
                    active_nodes=stats_data['active_nodes'],
                    inactive_nodes=stats_data['inactive_nodes'],
                    error_nodes=stats_data['error_nodes'],
                    unknown_nodes=stats_data['unknown_nodes'],
                    avg_latency=stats_data['avg_latency'],
                    min_latency=stats_data['min_latency'],
                    max_latency=stats_data['max_latency'],
                    country_distribution=json.dumps(stats_data['country_distribution']),
                    type_distribution=json.dumps(stats_data['type_distribution']),
                    last_updated=datetime.utcnow()
                )
                db.add(new_stats)
            
            db.commit()
            return stats_data
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_cached_stats(db: Session, user_id: int, input_record_id: int = None) -> Dict[str, Any]:
        """获取缓存的统计数据"""
        stats = db.query(NodeStats).filter(
            NodeStats.user_id == user_id,
            NodeStats.input_record_id == input_record_id
        ).first()
        
        if not stats:
            # 如果没有缓存数据，计算并更新
            return StatsService.update_node_stats(db, user_id, input_record_id)
        
        return {
            'total_nodes': stats.total_nodes,
            'active_nodes': stats.active_nodes,
            'inactive_nodes': stats.inactive_nodes,
            'error_nodes': stats.error_nodes,
            'unknown_nodes': stats.unknown_nodes,
            'avg_latency': stats.avg_latency,
            'min_latency': stats.min_latency,
            'max_latency': stats.max_latency,
            'country_distribution': json.loads(stats.country_distribution) if stats.country_distribution else {},
            'type_distribution': json.loads(stats.type_distribution) if stats.type_distribution else {},
            'last_updated': stats.last_updated
        }
    
    @staticmethod
    def invalidate_stats_cache(db: Session, user_id: int, input_record_id: int = None):
        """使统计数据缓存失效"""
        query = db.query(NodeStats).filter(NodeStats.user_id == user_id)
        if input_record_id:
            query = query.filter(NodeStats.input_record_id == input_record_id)
        
        stats = query.all()
        for stat in stats:
            db.delete(stat)
        db.commit()
