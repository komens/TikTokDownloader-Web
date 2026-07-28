"""TikTokDownloader-Web API 服务器

基于 TikTokDownloader（原作者 JoeanAmier）魔改的精简版本：
仅保留抖音平台的 detail / download / list / queue / files / account 等核心路由，
并集成下载队列管理器与前端 SPA 入口。
"""
from io import BytesIO
from json import dumps, loads
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace
from typing import Optional
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from uvicorn import Config, Server

from ..custom import (
    REPOSITORY,
    SERVER_HOST,
    SERVER_PORT,
    VERSION_BETA,
    __VERSION__,
)
from ..manager.data_recorder import DataRecorder
from ..models import Settings
from ..translation import _
from .main_terminal import TikTok
from .queue_manager import BackgroundDownloader, DownloadQueueManager, DownloadStatus
from .thumbnail import ThumbnailGenerator

__all__ = ["APIServer"]


# ==================== 请求模型 ====================


class DownloadRequest(BaseModel):
    """下载作品请求参数"""

    url: str = Field(..., description="抖音作品/账号链接，自动提取")


class AccountDownloadRequest(BaseModel):
    """账号作品批量下载请求"""

    url: str = Field(..., description="抖音账号主页链接")
    mark: str = Field("", description="账号备注标识")
    tab: str = Field("post", description="账号页面类型：post/favorite/collection")
    earliest: str = Field("", description="作品最早发布日期")
    latest: str = Field("", description="作品最晚发布日期")


# ==================== API 服务器 ====================


class APIServer(TikTok):
    """API 服务器：精简版，仅保留抖音核心下载功能"""

    _INSTANCE = None

    def __new__(cls, *args, **kwargs):
        if not cls._INSTANCE:
            cls._INSTANCE = super().__new__(cls)
        return cls._INSTANCE

    def __init__(
        self,
        parameter,
        database,
        server_mode: bool = True,
    ):
        if getattr(self, "_initialized", False):
            # 单例已初始化，仅更新 parameter/database 引用
            self.parameter = parameter
            self.database = database
            return
        super().__init__(
            parameter,
            database,
            server_mode,
        )
        self._initialized = True
        self.server: Optional[FastAPI] = None
        self.queue_manager: Optional[DownloadQueueManager] = None
        self.background_downloader: Optional[BackgroundDownloader] = None
        self.data_recorder: Optional[DataRecorder] = None
        self.thumbnail_generator = ThumbnailGenerator(self._log_print)

    def _log_print(self, text: str, style: str = "INFO"):
        try:
            self.logger.info(text)
        except Exception:
            pass

    # ---------- 生命周期 ----------

    async def run_server(
        self,
        host=SERVER_HOST,
        port=SERVER_PORT,
        log_level="info",
    ):
        """启动 API 服务器"""
        self.server = FastAPI(
            debug=VERSION_BETA,
            title="DouK-Downloader",
            version=__VERSION__,
            description="抖音作品下载 API 服务",
        )
        self.setup_routes(self.server)
        config = Config(
            self.server,
            host=host,
            port=port,
            log_level=log_level,
        )
        server = Server(config)
        await server.serve()

    def setup_routes(self, app: FastAPI):
        """注册所有 API 路由并初始化队列管理器"""
        # 初始化 DataRecorder（数据库放 Volume/）
        root = self.parameter.ROOT
        folder = self.parameter.root.joinpath(self.parameter.folder_name)
        self.data_recorder = DataRecorder(
            root=root,
            folder=folder,
            switch=True,
        )

        # 初始化下载队列管理器（队列文件放 Volume/）
        queue_file = Path(root) / "download_queue.json"
        self.queue_manager = DownloadQueueManager(queue_file, self._log_print)
        self.queue_manager.reset_downloading_tasks()

        # 初始化后台下载处理器
        self.background_downloader = BackgroundDownloader(
            self.queue_manager,
            self,
            self._log_print,
        )

        @app.on_event("startup")
        async def startup_event():
            await self.data_recorder.__aenter__()
            # 启动时清理过期任务 + 重置下载中断的任务
            if self.queue_manager:
                self.queue_manager.cleanup_expired(
                    getattr(self.parameter, "queue_retention_days", 7)
                )
                self.queue_manager.reset_downloading_tasks()
            await self.background_downloader.start()
            self.logger.info(_("API 服务器已启动"))

        @app.on_event("shutdown")
        async def shutdown_event():
            await self.background_downloader.stop()
            await self.data_recorder.__aexit__(None, None, None)
            self.logger.info(_("API 服务器已关闭"))

        self._register_routes(app)

    # ---------- 路由注册 ----------

    def _register_routes(self, app: FastAPI):
        """注册具体路由"""
        app.post("/douyin/detail", tags=["抖音"])(self._route_detail)
        app.post("/douyin/download", tags=["抖音"])(self._route_download)
        app.post("/douyin/account", tags=["抖音"])(self._route_account_download)
        app.get("/douyin/list", tags=["抖音"])(self._route_list)
        app.get("/douyin/detail/{work_id}", tags=["抖音"])(self._route_get_detail)
        app.delete("/douyin/delete/{work_id}", tags=["抖音"])(self._route_delete)
        app.get("/douyin/queue", tags=["下载队列"])(self._route_get_queue)
        app.delete("/douyin/queue/{work_id}", tags=["下载队列"])(
            self._route_delete_queue
        )
        app.get("/files/{file_path:path}", tags=["文件访问"])(self._route_files)
        app.get("/", tags=["前端"])(self._route_index)
        app.get("/{full_path:path}", tags=["前端"])(self._route_spa_fallback)

    # ---------- 抖音详情/下载 ----------

    async def _route_detail(self, request: DownloadRequest):
        """获取作品数据及下载地址

        提取链接 → 调用 __deal_extract 风格逻辑 → 写入 DataRecorder → 返回数据
        """
        links = await self.links.run(request.url, "detail")
        if not links:
            return {"message": _("提取抖音作品链接失败"), "data": None}

        work_id = links[0]
        data = await self._extract_detail_data(work_id)
        if not data:
            return {"message": _("获取作品数据失败"), "data": None}

        # 转换为中文键并写入数据库
        record_data = self._map_to_record(data, request.url)
        await self.data_recorder.add(**record_data)

        # 补全文件访问信息
        file_paths = record_data.get("下载文件路径", [])
        if file_paths:
            data["文件访问信息"] = self.convert_file_paths_to_urls(file_paths)

        return {"message": _("获取作品数据成功"), "data": data}

    async def _route_download(self, request: DownloadRequest):
        """下载作品文件 - 加入队列后台处理

        通过短链生成唯一ID（md5 hash），立即加入队列，无网络请求，毫秒级响应。
        短链解析和真实作品ID获取由后台处理器异步完成。

        智能识别链接类型：
        - 作品链接：加入下载队列后台处理
        - 账号链接：直接触发账号作品批量下载（同步执行）
        """
        import hashlib

        url = request.url.strip()
        if not url:
            return {"message": _("请输入链接"), "data": None}

        # 提取链接中的 URL（用户可能粘贴带描述文字的分享文本）
        url_match = self.links.requester.URL.search(url)
        if not url_match:
            return {"message": _("未找到有效链接"), "data": None}
        raw_url = url_match.group()

        # 账号链接判断：直接用正则匹配原始文本（无需网络请求）
        sec_user_ids = self.links.user(raw_url)
        if sec_user_ids:
            # 账号链接：同步处理账号作品批量下载
            sec_user_id = sec_user_ids[0]
            try:
                data = await self.deal_account_detail(
                    0,
                    sec_user_id=sec_user_id,
                    mark="",
                    tab="post",
                    earliest="",
                    latest="",
                    api=True,
                    source=False,
                    tiktok=False,
                )
            except Exception as e:
                return {
                    "message": _("账号作品下载失败：{error}").format(error=e),
                    "data": None,
                }

            if not data:
                return {"message": _("账号无作品或获取失败"), "data": None}

            # 写入数据库
            written = 0
            for item in data:
                try:
                    record_data = self._map_to_record(item, request.url)
                    await self.data_recorder.add(**record_data)
                    written += 1
                except Exception:
                    continue

            return {
                "message": _(
                    "账号作品处理完成，共 {count} 个作品，{written} 个已记录"
                ).format(count=len(data), written=written),
                "data": {
                    "type": "account",
                    "sec_user_id": sec_user_id,
                    "total": len(data),
                    "written": written,
                },
            }

        # 作品链接：用短链 hash 生成唯一ID，立即加入队列（无网络请求）
        unique_id = hashlib.md5(raw_url.encode()).hexdigest()[:16]
        if not self.queue_manager:
            return {"message": _("队列管理器未初始化"), "data": None}

        existing = self.queue_manager.get_item(unique_id)
        if existing:
            status_text = {
                "pending": "待下载",
                "downloading": "下载中",
                "completed": "已完成",
                "failed": "下载失败",
            }.get(existing["status"], existing["status"])
            return {
                "message": _("作品已存在于下载队列中（状态：{status}）").format(
                    status=status_text
                ),
                "data": existing,
            }

        success = self.queue_manager.add_to_queue(
            work_id=unique_id,
            title=raw_url,
            author="",
            url=raw_url,
            status=DownloadStatus.PENDING,
        )
        if success:
            return {
                "message": _("已添加到下载队列"),
                "data": {
                    "work_id": unique_id,
                    "title": raw_url,
                    "status": "pending",
                },
            }
        return {"message": _("添加到队列失败"), "data": None}

    async def _route_account_download(self, request: AccountDownloadRequest):
        """账号作品批量下载：输入账号链接，下载该账号所有作品"""
        sec_user_ids = await self.links.run(request.url, "user")
        if not sec_user_ids:
            return {"message": _("提取账号 sec_user_id 失败"), "data": None}

        sec_user_id = sec_user_ids[0]
        try:
            data = await self.deal_account_detail(
                0,
                sec_user_id=sec_user_id,
                mark=request.mark,
                tab=request.tab or "post",
                earliest=request.earliest or "",
                latest=request.latest or "",
                api=True,
                source=False,
                tiktok=False,
            )
        except Exception as e:
            return {"message": _("账号作品下载失败：{error}").format(error=e), "data": None}

        if not data:
            return {"message": _("账号无作品或获取失败"), "data": None}

        # 写入数据库
        written = 0
        for item in data:
            try:
                record_data = self._map_to_record(item, request.url)
                await self.data_recorder.add(**record_data)
                written += 1
            except Exception:
                continue

        # 触发实际下载（账号作品批量下载，使用 deal_account_detail 内部已下载）
        return {
            "message": _("账号作品处理完成，共 {count} 个作品，{written} 个已记录").format(
                count=len(data), written=written
            ),
            "data": {
                "sec_user_id": sec_user_id,
                "total": len(data),
                "written": written,
            },
        }

    # ---------- 列表 / 详情 / 删除 ----------

    async def _route_list(
        self,
        page: int = 1,
        pageSize: int = 20,
        author_nickname: Optional[str] = None,
        author_id: Optional[str] = None,
        work_title: Optional[str] = None,
        work_desc: Optional[str] = None,
    ):
        """获取作品数据列表（支持搜索）"""
        search_conditions = {}
        if author_nickname:
            search_conditions["作者昵称"] = author_nickname
        if author_id:
            search_conditions["作者ID"] = author_id
        if work_title:
            search_conditions["作品标题"] = work_title
        if work_desc:
            search_conditions["作品描述"] = work_desc

        total = await self.data_recorder.count(search_conditions)
        data_list = await self.data_recorder.select_all(page, pageSize, search_conditions)

        for item in data_list:
            await self._populate_file_access_info(item)

        return {
            "message": _("获取作品数据列表成功"),
            "total": total,
            "page": page,
            "pageSize": pageSize,
            "data": data_list,
        }

    async def _route_get_detail(self, work_id: str):
        """获取单个作品数据详情"""
        data = await self.data_recorder.select(work_id)
        if data:
            await self._populate_file_access_info(data)
            return {"message": _("获取作品数据成功"), "data": data}
        return {"message": _("作品不存在"), "data": None}

    async def _route_delete(self, work_id: str, delete_files: bool = False):
        """删除作品数据，可选择同时删除文件资源"""
        data = await self.data_recorder.select(work_id)
        if not data:
            return {"message": _("作品不存在")}

        deleted_files = []
        if delete_files:
            file_paths = data.get("下载文件路径", [])
            if isinstance(file_paths, str):
                try:
                    file_paths = loads(file_paths)
                except Exception:
                    file_paths = []
            for fp in file_paths:
                if not fp:
                    continue
                try:
                    p = Path(fp)
                    if p.exists():
                        p.unlink()
                        deleted_files.append(fp)
                    # 删除视频缩略图
                    if p.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
                        thumb = self.parameter.ROOT / "Temp" / (p.stem + ".jpg")
                        if thumb.exists():
                            thumb.unlink()
                except Exception:
                    pass

        await self.data_recorder.delete([work_id])
        try:
            await self.recorder.delete_id(work_id)
        except Exception:
            pass

        return {
            "message": _("删除作品数据成功"),
            "deleted_files": deleted_files if delete_files else None,
        }

    # ---------- 队列 ----------

    async def _route_get_queue(self):
        """获取下载队列"""
        if not self.queue_manager:
            return {"message": _("队列管理器未初始化"), "data": []}
        queue_data = self.queue_manager.get_queue()
        return {
            "message": _("获取下载队列成功"),
            "count": len(queue_data),
            "data": queue_data,
        }

    async def _route_delete_queue(self, work_id: str):
        """从队列中删除任务"""
        if not self.queue_manager:
            return {"message": _("队列管理器未初始化"), "success": False}
        success = self.queue_manager.remove_from_queue(work_id)
        if success:
            return {"message": _("已从队列中删除任务: {0}").format(work_id), "success": True}
        return {"message": _("任务不存在或删除失败: {0}").format(work_id), "success": False}

    # ---------- 文件访问 ----------

    async def _route_files(self, file_path: str):
        """静态文件访问接口"""
        full_path = self.parameter.ROOT.joinpath(file_path)
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        if not full_path.is_file():
            raise HTTPException(status_code=400, detail="请求的路径不是文件")
        return FileResponse(
            path=str(full_path),
            filename=full_path.name,
            media_type="application/octet-stream",
        )

    # ---------- 前端入口 ----------

    async def _route_index(self):
        """前端页面入口"""
        frontend_index = (
            Path(__file__).parent.parent.parent / "web" / "dist" / "index.html"
        )
        if frontend_index.exists():
            return FileResponse(str(frontend_index))
        return RedirectResponse(url=REPOSITORY)

    async def _route_spa_fallback(self, full_path: str):
        """SPA 路由回退"""
        frontend_dist = Path(__file__).parent.parent.parent / "web" / "dist"
        static_file = frontend_dist / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(str(static_file))
        frontend_index = frontend_dist / "index.html"
        if frontend_index.exists():
            return FileResponse(str(frontend_index))
        raise HTTPException(status_code=404, detail="Not Found")

    # ---------- 后台下载处理器调用的核心方法 ----------

    async def _process_single_download(self, queue_item: dict) -> Optional[str]:
        """处理单个下载任务（由 BackgroundDownloader 调用）

        1. 通过短链解析获取真实作品ID
        2. 提取作品数据
        3. 调用 Downloader 下载文件
        4. 更新 DataRecorder 中的下载文件路径
        5. 生成视频缩略图

        Returns:
            真实作品ID（用于关联队列与作品列表），失败返回 None
        """
        work_id = queue_item["work_id"]  # 短链 hash 唯一ID
        url = queue_item.get("url", "")

        # 后台解析短链获取真实作品ID
        detail_id = None
        try:
            if url:
                links = await self.links.run(url, "detail")
                if links:
                    detail_id = links[0]
        except Exception as e:
            raise Exception(f"解析短链失败: {e}")

        if not detail_id:
            raise Exception(f"无法从链接提取作品ID: {url}")

        self.logger.info(f"队列任务 {work_id} -> 真实作品ID: {detail_id}")

        # 提取作品数据
        data = await self._extract_detail_data(detail_id)
        if not data:
            raise Exception(f"提取作品数据失败: {detail_id}")

        # 调用下载器下载
        try:
            await self.downloader.run([data], "detail", tiktok=False)
        except Exception as e:
            raise Exception(f"下载文件失败: {e}")

        # 计算实际下载文件路径
        file_paths = self._resolve_downloaded_files(data)
        if file_paths:
            # 更新数据库
            record_data = self._map_to_record(data, url or "")
            record_data["下载文件路径"] = file_paths
            await self.data_recorder.add(**record_data)
            # 生成视频缩略图（保存到 Volume/Temp/，前端通过 /files/Temp/xxx.jpg 访问）
            temp_dir = self.parameter.ROOT / "Temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            for fp in file_paths:
                try:
                    p = Path(fp)
                    if p.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
                        thumb = self.thumbnail_generator.generate_video_thumbnail(p, temp_dir)
                        if thumb:
                            self.logger.info(f"已生成缩略图: {thumb.name}")
                        else:
                            self.logger.warning(f"缩略图生成失败: {p.name}")
                except Exception as e:
                    self.logger.warning(f"生成缩略图异常 {p.name}: {e}")

        # 更新下载记录
        try:
            await self.recorder.update_id(detail_id)
        except Exception:
            pass

        return detail_id

    # ---------- 数据提取辅助 ----------

    async def _extract_detail_data(self, work_id: str) -> Optional[dict]:
        """提取单个作品数据，返回 dict 形式的作品数据"""
        from ..interface import Detail

        try:
            detail_data = await Detail(
                self.parameter,
                None,
                None,
                work_id,
            ).run()
        except Exception as e:
            self.logger.error(f"提取作品 {work_id} 失败: {e}")
            return None

        if not detail_data:
            return None

        # 调用 extractor 处理为标准 dict
        # 使用 blank recorder（BaseTextLogger），避免写入文件，仅做数据提取
        try:
            root, params, logger = self.record.run(self.parameter, blank=True)
            async with logger(root, **params) as recorder:
                processed = await self.extractor.run(
                    detail_data if isinstance(detail_data, list) else [detail_data],
                    recorder,
                    type_="detail",
                    tiktok=False,
                )
            if processed and isinstance(processed, list):
                return processed[0]
        except Exception as e:
            self.logger.error(f"处理作品数据失败: {e}")
            return None
        return None

    def _map_to_record(self, data: dict, source_url: str = "") -> dict:
        """将 extractor 产出的数据映射为 DataRecorder 中文键"""
        from datetime import datetime

        downloads = data.get("downloads")
        if isinstance(downloads, str):
            download_urls = [downloads] if downloads else []
        elif isinstance(downloads, list):
            download_urls = [u for u in downloads if u]
        else:
            download_urls = []

        music_url = data.get("music_url", "")
        return {
            "采集时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "作品ID": data.get("id", ""),
            "作品类型": data.get("type", ""),
            "作品标题": data.get("desc", "")[:64] if data.get("desc") else "",
            "作品描述": data.get("desc", ""),
            "作品标签": dumps(
                data.get("text_extra") or data.get("tag") or [],
                ensure_ascii=False,
            ),
            "发布时间": data.get("create_time", ""),
            "最后更新时间": data.get("create_time", ""),
            "收藏数量": str(data.get("collect_count", -1)),
            "评论数量": str(data.get("comment_count", -1)),
            "分享数量": str(data.get("share_count", -1)),
            "点赞数量": str(data.get("digg_count", -1)),
            "作者昵称": data.get("nickname", ""),
            "作者ID": data.get("uid", ""),
            "作者链接": f"https://www.douyin.com/user/{data.get('sec_uid', '')}"
            if data.get("sec_uid")
            else "",
            "作品链接": data.get("share_url") or source_url,
            "下载地址": dumps(download_urls, ensure_ascii=False),
            "动图地址": dumps([data.get("dynamic_cover") or ""], ensure_ascii=False),
            "下载文件路径": dumps([], ensure_ascii=False),
        }

    def _resolve_downloaded_files(self, data: dict) -> list:
        """下载完成后，根据命名规则扫描实际下载的文件路径"""
        try:
            root = self.parameter.root.joinpath(self.parameter.folder_name)
            if not root.exists():
                return []
            name = self.downloader.generate_detail_name(data)
            matched = sorted(f for f in root.glob(f"{name}*") if f.is_file())
            media_exts = {
                ".mp4", ".mov", ".avi", ".mkv", ".webm",
                ".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic",
                ".gif", ".live", ".mp3",
            }
            return [str(f) for f in matched if f.suffix.lower() in media_exts]
        except Exception:
            return []

    async def _populate_file_access_info(self, data: dict) -> None:
        """为作品数据填充文件访问信息

        当"下载文件路径"为空时，扫描 Download 目录匹配已下载的文件，
        找到后回填数据并异步更新数据库。
        """
        try:
            file_paths = data.get("下载文件路径", [])
            if isinstance(file_paths, str):
                try:
                    file_paths = loads(file_paths)
                except Exception:
                    file_paths = []
            if not isinstance(file_paths, list):
                return

            if not file_paths:
                scanned = self._scan_download_files(data)
                if scanned:
                    file_paths = scanned
                    data["下载文件路径"] = scanned
                    await self.data_recorder.update_file_paths(
                        data.get("作品ID", ""), scanned
                    )

            if file_paths:
                data["文件访问信息"] = self.convert_file_paths_to_urls(file_paths)
        except Exception:
            pass

    def _scan_download_files(self, data: dict) -> list:
        """扫描 Download 目录，匹配已下载的文件"""
        try:
            mapped = {
                "id": data.get("作品ID", ""),
                "desc": data.get("作品描述", "") or data.get("作品标题", ""),
                "create_time": data.get("发布时间", ""),
                "nickname": data.get("作者昵称", ""),
                "uid": data.get("作者ID", ""),
                "type": data.get("作品类型", ""),
            }
            name = self.downloader.generate_detail_name(mapped)
            search_dir = self.parameter.root.joinpath(self.parameter.folder_name)
            if not search_dir.exists():
                return []
            matched = sorted(f for f in search_dir.glob(f"{name}*") if f.is_file())
            media_exts = {
                ".mp4", ".mov", ".avi", ".mkv", ".webm",
                ".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic",
                ".gif", ".live", ".mp3",
            }
            return [str(f) for f in matched if f.suffix.lower() in media_exts]
        except Exception:
            return []

    @staticmethod
    def _extract_relative_path(path_str: str) -> str:
        """从绝对路径中提取相对于 Volume 的相对路径"""
        import re

        normalized = path_str.replace("\\", "/")
        match = re.search(r"(?:^|/)(Download|Temp|Music|Live)/(.+)$", normalized)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return normalized

    def convert_file_paths_to_urls(self, file_paths: list) -> list:
        """将文件绝对路径转换为可访问的 URL 信息"""
        from urllib.parse import quote

        result = []
        for path_str in file_paths:
            if not path_str:
                continue
            try:
                path = Path(path_str)
                try:
                    relative_path = path.relative_to(self.parameter.ROOT)
                    relative_path_str = str(relative_path).replace("\\", "/")
                except ValueError:
                    relative_path_str = self._extract_relative_path(path_str)

                # 对路径进行 URL 编码（保留 / 分隔符）
                # 必须编码 #、空格、中文等特殊字符，否则浏览器会把 # 之后当作 fragment 截断
                encoded_path = quote(relative_path_str, safe="/")
                url = f"/files/{encoded_path}"
                file_info = {
                    "absolute_path": path_str,
                    "relative_path": relative_path_str,
                    "url": url,
                    "filename": path.name,
                }

                # 视频文件附加缩略图 URL（同样需要编码）
                if path.suffix.lower() in {".mp4", ".mov", ".avi", ".mkv", ".webm"}:
                    thumbnail_relative = f"Temp/{path.stem}.jpg"
                    file_info["thumbnail_url"] = f"/files/{quote(thumbnail_relative, safe='/')}"

                result.append(file_info)
            except Exception:
                result.append(
                    {
                        "absolute_path": path_str,
                        "relative_path": self._extract_relative_path(path_str)
                        if path_str
                        else "",
                        "url": path_str,
                        "filename": Path(path_str).name if path_str else "",
                    }
                )
        return result
