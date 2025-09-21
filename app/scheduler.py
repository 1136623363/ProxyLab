from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.monitoring.node_checker import NodeChecker
from app.parsers.parser_factory import ParserFactory
from app.database import Node, InputRecord, SystemLog
from app.models import LogType, InputType
import requests
import asyncio
from datetime import datetime, timedelta
from app.database import beijing_now

class SchedulerManager:
    """定时任务管理器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.node_checker = NodeChecker()
        self.parser_factory = ParserFactory()
        self._setup_jobs()
    
    def _setup_jobs(self):
        """设置定时任务"""
        # 每10分钟检测节点状态
        self.scheduler.add_job(
            self.check_all_nodes,
            IntervalTrigger(minutes=10),
            id='check_nodes',
            name='检测所有节点状态',
            replace_existing=True
        )
        
        # 每6小时更新URL订阅源
        self.scheduler.add_job(
            self.refresh_url_subscriptions,
            IntervalTrigger(hours=6),
            id='refresh_subscriptions',
            name='刷新URL订阅源',
            replace_existing=True
        )
        
        # 每天凌晨2点清理30天前的日志
        self.scheduler.add_job(
            self.cleanup_old_logs,
            CronTrigger(hour=2, minute=0),
            id='cleanup_logs',
            name='清理旧日志',
            replace_existing=True
        )
    
    async def check_all_nodes(self):
        """检测所有节点状态"""
        try:
            print("[INFO] 开始检测所有节点状态...")
            db = SessionLocal()
            try:
                # 获取所有非禁用节点（包括unknown、active、inactive、error状态）
                nodes = db.query(Node).filter(Node.status != "disabled").all()
                if not nodes:
                    print("[INFO] 没有需要检测的节点")
                    return
                
                print(f"[INFO] 检测 {len(nodes)} 个节点...")
                
                # 批量检测节点
                results = await self.node_checker.check_nodes_batch([node.id for node in nodes])
                
                # 更新节点状态
                updated_count = 0
                for node_id, result in results.items():
                    node = db.query(Node).filter(Node.id == node_id).first()
                    if node:
                        if result['success']:
                            node.ping_latency = result.get('latency', 0)
                            node.last_check = beijing_now()
                            node.status = "active"
                        else:
                            node.status = "inactive"
                            node.last_check = beijing_now()
                        updated_count += 1
                
                db.commit()
                print(f"[INFO] 节点检测完成，更新了 {updated_count} 个节点")
                
                # 更新统计数据
                from app.services.stats_service import StatsService
                for user_id in set(node.input_record.user_id for node in nodes):
                    StatsService.update_node_stats(db, user_id)
                
                # 记录日志
                self._log_activity(
                    db=db,
                    log_type=LogType.INFO,
                    message=f"定时检测完成，检测了 {len(nodes)} 个节点，更新了 {updated_count} 个节点"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"[ERROR] 节点检测失败: {e}")
            # 记录错误日志
            db = SessionLocal()
            try:
                self._log_activity(
                    db=db,
                    log_type=LogType.ERROR,
                    message=f"节点检测失败: {str(e)}"
                )
            finally:
                db.close()
    
    async def refresh_url_subscriptions(self):
        """刷新URL订阅源"""
        try:
            print("[INFO] 开始刷新URL订阅源...")
            db = SessionLocal()
            try:
                # 获取所有URL类型的订阅记录
                subscriptions = db.query(InputRecord).filter(
                    InputRecord.input_type == InputType.URL
                ).all()
                
                if not subscriptions:
                    print("[INFO] 没有URL订阅源需要刷新")
                    return
                
                print(f"[INFO] 刷新 {len(subscriptions)} 个URL订阅源...")
                
                updated_count = 0
                for subscription in subscriptions:
                    try:
                        # 获取订阅内容
                        response = requests.get(subscription.source_url, timeout=30)
                        if response.status_code == 200:
                            content = response.text
                            
                            # 解析订阅内容
                            from app.models import InputType
                            input_type_enum = InputType(subscription.input_type) if hasattr(InputType, subscription.input_type.upper()) else InputType.TEXT
                            nodes_data = self.parser_factory.parse_content(content, input_type_enum)
                            
                            # 更新节点数据
                            if nodes_data:
                                # 删除该订阅源的旧节点
                                db.query(Node).filter(
                                    Node.input_record_id == subscription.id
                                ).delete()
                                
                                # 添加新节点
                                for node_data in nodes_data:
                                    node = Node(
                                        name=node_data.get('name', ''),
                                        node_type=node_data.get('type', ''),
                                        address=node_data.get('address', ''),
                                        port=node_data.get('port', 0),
                                        encryption=node_data.get('encryption', ''),
                                        password=node_data.get('password', ''),
                                        uuid=node_data.get('uuid', ''),
                                        alter_id=node_data.get('alter_id', 0),
                                        network=node_data.get('network', ''),
                                        path=node_data.get('path', ''),
                                        host=node_data.get('host', ''),
                                        tls=node_data.get('tls', False),
                                        sni=node_data.get('sni', ''),
                                        country=node_data.get('country', ''),
                                        region=node_data.get('region', ''),
                                        input_record_id=subscription.id,
                                        status='active',
                                        ignore_updates=False,
                                        created_at=beijing_now(),
                                        updated_at=beijing_now()
                                    )
                                    db.add(node)
                                    
                                    subscription.last_refresh = beijing_now()
                                    updated_count += 1
                                    print(f"[INFO] 刷新订阅源: {subscription.source_url}")
                                
                        else:
                            print(f"[WARN] 订阅源响应异常: {subscription.source_url} ({response.status_code})")
                            
                    except Exception as e:
                        print(f"[ERROR] 刷新订阅源失败: {subscription.source_url} - {e}")
                
                db.commit()
                print(f"[INFO] 订阅源刷新完成，更新了 {updated_count} 个订阅源")
                
                # 更新统计数据
                from app.services.stats_service import StatsService
                for subscription in subscriptions:
                    StatsService.update_node_stats(db, subscription.user_id, subscription.id)
                
                # 记录日志
                self._log_activity(
                    db=db,
                    log_type=LogType.INFO,
                    message=f"定时刷新完成，刷新了 {len(subscriptions)} 个订阅源，更新了 {updated_count} 个订阅源"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"[ERROR] 订阅源刷新失败: {e}")
            # 记录错误日志
            db = SessionLocal()
            try:
                self._log_activity(
                    db=db,
                    log_type=LogType.ERROR,
                    message=f"订阅源刷新失败: {str(e)}"
                )
            finally:
                db.close()
    
    async def cleanup_old_logs(self):
        """清理旧日志"""
        try:
            print("[INFO] 开始清理旧日志...")
            db = SessionLocal()
            try:
                # 删除30天前的日志
                cutoff_date = beijing_now() - timedelta(days=30)
                deleted_count = db.query(SystemLog).filter(
                    SystemLog.created_at < cutoff_date
                ).delete()
                
                db.commit()
                print(f"[INFO] 清理完成，删除了 {deleted_count} 条旧日志")
                
                # 记录清理日志
                self._log_activity(
                    db=db,
                    log_type=LogType.INFO,
                    message=f"日志清理完成，删除了 {deleted_count} 条30天前的日志"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"[ERROR] 日志清理失败: {e}")
            # 记录错误日志
            db = SessionLocal()
            try:
                self._log_activity(
                    db=db,
                    log_type=LogType.ERROR,
                    message=f"日志清理失败: {str(e)}"
                )
            finally:
                db.close()
    
    def _log_activity(self, db: Session, log_type: LogType, message: str):
        """记录活动日志"""
        try:
            log = SystemLog(
                log_type=log_type,
                message=message,
                created_at=beijing_now()
            )
            db.add(log)
            db.commit()
        except Exception as e:
            print(f"[ERROR] 记录日志失败: {e}")
    
    def start(self):
        """启动调度器"""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                print("[INFO] 定时任务调度器已启动")
        except Exception as e:
            print(f"[WARN] 定时任务调度器启动失败: {e}")
            # 不阻止应用启动
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("[INFO] 定时任务调度器已停止")
    
    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()

# 全局调度器实例
scheduler_manager = SchedulerManager()