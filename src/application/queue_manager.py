"""下载队列管理模块

使用 JSON 文件存储下载队列，保留所有状态的任务（含已完成）。
后台处理器串行处理队列中的 pending 任务。
超过指定天数的 completed/failed 任务会被自动清理。
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class DownloadStatus(str, Enum):
    """下载状态枚举"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class QueueItemData:
    """队列项数据类（仅用于类型提示，实际存储用 dict）"""
    work_id: str  # 短链 hash 生成的唯一ID
    title: str
    author: str
    status: DownloadStatus
    added_at: float
    url: str  # 原始短链
    error_message: Optional[str] = None
    real_work_id: Optional[str] = None  # 后台解析出的真实作品ID，用于关联作品列表
    completed_at: Optional[float] = None  # 下载完成时间


def _item_to_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    """规范化队列项为可序列化字典"""
    status = item.get("status")
    if isinstance(status, DownloadStatus):
        item["status"] = status.value
    return item


class DownloadQueueManager:
    """下载队列管理器

    队列文件使用 fcntl 文件锁保证并发安全。
    只保留 pending / downloading / failed 三种状态的任务。
    下载成功的任务会自动从队列中移除。
    """

    def __init__(self, queue_file: Path, print_func=None):
        """
        Args:
            queue_file: 队列文件路径
            print_func: 日志输出函数
        """
        self.queue_file = queue_file
        self.print = print_func or print
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not self.queue_file.exists():
            self.queue_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_queue([])

    def _read_queue(self) -> List[Dict[str, Any]]:
        """读取队列数据（带文件锁）"""
        try:
            import fcntl
        except ImportError:
            fcntl = None

        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
                finally:
                    if fcntl:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            self._log(f"读取队列文件失败: {e}", "WARNING")
            return []

    def _write_queue(self, queue_data: List[Dict[str, Any]]) -> bool:
        """写入队列数据（带文件锁）"""
        try:
            import fcntl
        except ImportError:
            fcntl = None

        try:
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                if fcntl:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(queue_data, f, ensure_ascii=False, indent=2)
                    return True
                finally:
                    if fcntl:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            self._log(f"写入队列文件失败: {e}", "ERROR")
            return False

    def _log(self, text: str, style: str = "INFO"):
        """简单日志输出"""
        try:
            self.print(f"[{style}] {text}")
        except Exception:
            pass

    def add_to_queue(
        self,
        work_id: str,
        title: str,
        author: str,
        url: str,
        status: DownloadStatus = DownloadStatus.PENDING,
    ) -> bool:
        """添加任务到队列"""
        queue_data = self._read_queue()
        for item in queue_data:
            if item["work_id"] == work_id:
                self._log(f"作品 {work_id} 已在队列中", "INFO")
                return False
        new_item = {
            "work_id": work_id,
            "title": title,
            "author": author,
            "url": url,
            "status": status.value if isinstance(status, DownloadStatus) else status,
            "added_at": time.time(),
            "error_message": None,
        }
        queue_data.append(new_item)
        success = self._write_queue(queue_data)
        if success:
            self._log(f"添加下载任务到队列: {title} ({work_id})", "INFO")
        return success

    def remove_from_queue(self, work_id: str) -> bool:
        """从队列中移除任务"""
        queue_data = self._read_queue()
        original_len = len(queue_data)
        queue_data = [item for item in queue_data if item["work_id"] != work_id]
        if len(queue_data) == original_len:
            self._log(f"作品 {work_id} 不在队列中", "WARNING")
            return False
        success = self._write_queue(queue_data)
        if success:
            self._log(f"从队列中移除任务: {work_id}", "INFO")
        return success

    def update_status(
        self,
        work_id: str,
        status: DownloadStatus,
        error_message: Optional[str] = None,
        real_work_id: Optional[str] = None,
    ) -> bool:
        """更新任务状态

        Args:
            work_id: 队列项唯一ID
            status: 新状态
            error_message: 错误信息（failed 时填写）
            real_work_id: 真实作品ID（completed 时填写，用于关联作品列表）
        """
        queue_data = self._read_queue()
        found = False
        for item in queue_data:
            if item["work_id"] == work_id:
                item["status"] = status.value if isinstance(status, DownloadStatus) else status
                if error_message is not None:
                    item["error_message"] = error_message
                if real_work_id is not None:
                    item["real_work_id"] = real_work_id
                if status == DownloadStatus.COMPLETED:
                    item["completed_at"] = time.time()
                found = True
                break
        if not found:
            self._log(f"作品 {work_id} 不在队列中", "WARNING")
            return False
        success = self._write_queue(queue_data)
        if success:
            self._log(f"更新任务状态: {work_id} -> {status.value}", "INFO")
        return success

    def cleanup_expired(self, retention_days: int) -> int:
        """清理超过指定天数的已完成/失败任务

        Args:
            retention_days: 保留天数（超过此天数的 completed/failed 任务将被删除）

        Returns:
            清理的任务数量
        """
        if retention_days <= 0:
            return 0
        queue_data = self._read_queue()
        now = time.time()
        threshold = retention_days * 86400
        expired_statuses = {
            DownloadStatus.COMPLETED.value,
            DownloadStatus.FAILED.value,
        }
        kept = []
        removed = 0
        for item in queue_data:
            if item.get("status") in expired_statuses:
                # 优先用 completed_at 判断，回退到 added_at
                check_time = item.get("completed_at") or item.get("added_at", 0)
                if now - check_time > threshold:
                    removed += 1
                    continue
            kept.append(item)
        if removed > 0:
            self._write_queue(kept)
            self._log(f"清理了 {removed} 个过期任务（超过 {retention_days} 天）", "INFO")
        return removed

    def get_queue(self) -> List[Dict[str, Any]]:
        """获取整个队列（按添加时间倒序）"""
        queue_data = self._read_queue()
        queue_data.sort(key=lambda x: x.get("added_at", 0), reverse=True)
        return queue_data

    def get_item(self, work_id: str) -> Optional[Dict[str, Any]]:
        """获取单个队列项"""
        queue_data = self._read_queue()
        for item in queue_data:
            if item["work_id"] == work_id:
                return item
        return None

    def reset_downloading_tasks(self) -> int:
        """重置所有 downloading 状态的任务为 pending（服务启动时调用）"""
        queue_data = self._read_queue()
        reset_count = 0
        for item in queue_data:
            if item["status"] == DownloadStatus.DOWNLOADING.value:
                item["status"] = DownloadStatus.PENDING.value
                item["error_message"] = "服务重启，任务重新排队"
                reset_count += 1
        if reset_count > 0:
            self._write_queue(queue_data)
            self._log(f"重置了 {reset_count} 个下载中的任务为待下载状态", "INFO")
        return reset_count


class BackgroundDownloader:
    """后台下载处理器

    持续轮询下载队列，串行处理 pending 任务。
    """

    def __init__(self, queue_manager: DownloadQueueManager, server_instance, print_func=None):
        """
        Args:
            queue_manager: 队列管理器实例
            server_instance: APIServer 实例（提供 _process_single_download 方法）
            print_func: 日志输出函数
        """
        self.queue_manager = queue_manager
        self.server = server_instance
        self.print = print_func or print
        self._running = False
        self._task = None

    def _log(self, text: str, style: str = "INFO"):
        try:
            self.print(f"[{style}] {text}")
        except Exception:
            pass

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._download_loop())
        self._log("后台下载处理器已启动", "INFO")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._log("后台下载处理器已停止", "INFO")

    async def _download_loop(self):
        """下载循环：每秒检查队列，定期清理过期任务"""
        last_cleanup = time.time()
        cleanup_interval = 3600  # 每小时清理一次过期任务
        while self._running:
            try:
                # 定期清理过期任务
                if time.time() - last_cleanup > cleanup_interval:
                    retention_days = getattr(
                        self.server.parameter, "queue_retention_days", 7
                    )
                    self.queue_manager.cleanup_expired(retention_days)
                    last_cleanup = time.time()

                queue_data = self.queue_manager.get_queue()
                pending_item = None
                for item in queue_data:
                    if item["status"] == DownloadStatus.PENDING.value:
                        pending_item = item
                        break
                if pending_item:
                    await self._process_download(pending_item)
                else:
                    await asyncio.sleep(1)
            except Exception as e:
                self._log(f"下载循环异常: {str(e)}", "ERROR")
                await asyncio.sleep(1)

    async def _process_download(self, queue_item: Dict[str, Any]):
        """处理单个下载任务

        下载成功后更新状态为 COMPLETED（保留在队列中供前端查看历史），
        并记录真实作品ID用于关联作品列表。
        """
        work_id = queue_item["work_id"]
        title = queue_item.get("title", "未知作品")
        self._log(f"开始下载: {title} ({work_id})", "INFO")
        self.queue_manager.update_status(work_id, DownloadStatus.DOWNLOADING)
        try:
            real_work_id = await self.server._process_single_download(queue_item)
            if real_work_id:
                self.queue_manager.update_status(
                    work_id,
                    DownloadStatus.COMPLETED,
                    real_work_id=real_work_id,
                )
                self._log(f"下载成功: {title} -> 真实作品ID: {real_work_id}", "INFO")
            else:
                raise Exception("下载失败：未获取到作品数据")
        except Exception as e:
            error_msg = str(e)
            self.queue_manager.update_status(
                work_id,
                DownloadStatus.FAILED,
                error_msg,
            )
            self._log(f"下载失败: {title} - {error_msg}", "ERROR")
