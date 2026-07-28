"""DouK-Downloader 应用入口

精简版：只保留 Web API 模式，移除终端交互/剪贴板监听/Web UI 等其他模式。
"""
from asyncio import CancelledError, run
from threading import Event, Thread
from time import sleep

from src.config import Parameter, Settings
from src.custom import (
    COOKIE_UPDATE_INTERVAL,
    PROJECT_NAME,
    PROJECT_ROOT,
    SERVER_HOST,
    SERVER_PORT,
    VERSION_BETA,
    VERSION_MAJOR,
    VERSION_MINOR,
)
from src.manager import Database, DownloadRecorder
from src.module import Cookie, MigrateFolder
from src.record import BaseLogger, LoggerManager
from src.tools import (
    ColorfulConsole,
    RenameCompatible,
    remove_empty_directories,
)
from src.translation import _

from .main_server import APIServer

__all__ = ["TikTokDownloader"]


class TikTokDownloader:
    """DouK-Downloader 应用入口（仅 API 模式）"""

    VERSION_MAJOR = VERSION_MAJOR
    VERSION_MINOR = VERSION_MINOR
    VERSION_BETA = VERSION_BETA
    NAME = PROJECT_NAME

    def __init__(self):
        self.rename_compatible()
        self.console = ColorfulConsole(debug=self.VERSION_BETA)
        self.logger = None
        self.recorder = None
        self.settings = Settings(PROJECT_ROOT, self.console)
        self.event_cookie = Event()
        self.cookie = Cookie(self.settings, self.console)
        self.params_task = None
        self.parameter = None
        self.running = True
        self.database = Database()
        self.config = None
        self.option = None

    @staticmethod
    def rename_compatible():
        RenameCompatible.migration_file()

    async def read_config(self):
        # 简化：直接使用默认配置，不再依赖数据库存储配置项
        self.config = {"Record": 1, "Logger": 1, "Disclaimer": 1}
        self.option = {"Language": "zh_CN"}

    async def __aenter__(self):
        await self.database.__aenter__()
        await self.read_config()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.database.__aexit__(exc_type, exc_val, exc_tb)
        if self.parameter:
            await self.parameter.close_client()
            self.close()

    def check_config(self):
        self.recorder = DownloadRecorder(
            self.database,
            self.config["Record"],
            self.console,
        )
        self.logger = {1: LoggerManager, 0: BaseLogger}[self.config["Logger"]]

    async def check_settings(self, restart=True):
        if restart:
            await self.parameter.close_client()
        self.parameter = Parameter(
            self.settings,
            self.cookie,
            logger=self.logger,
            console=self.console,
            **self.settings.read(),
            recorder=self.recorder,
        )
        MigrateFolder(self.parameter).compatible()
        self.parameter.set_headers_cookie()
        self.restart_cycle_task(restart)

    async def server(self):
        """启动 Web API 服务器"""
        self.console.print(
            _(
                "访问 http://127.0.0.1:5555/docs 或者 http://127.0.0.1:5555/redoc 可以查阅 API 模式说明文档！"
            ),
            highlight=True,
        )
        await APIServer(
            self.parameter,
            self.database,
        ).run_server(
            SERVER_HOST,
            SERVER_PORT,
        )

    async def run(self):
        """启动应用：初始化配置后直接进入 API 模式"""
        self.check_config()
        await self.check_settings(False)
        try:
            await self.server()
        except KeyboardInterrupt:
            self.running = False

    def periodic_update_params(self):
        async def inner():
            while not self.event_cookie.is_set():
                await self.parameter.update_params()
                self.event_cookie.wait(COOKIE_UPDATE_INTERVAL)

        run(inner())

    def restart_cycle_task(self, restart=True):
        if restart:
            self.event_cookie.set()
            while self.params_task.is_alive():
                sleep(1)
        self.params_task = Thread(target=self.periodic_update_params)
        self.event_cookie.clear()
        self.params_task.start()

    def close(self):
        self.event_cookie.set()
        if self.parameter.folder_mode:
            remove_empty_directories(self.parameter.ROOT)
            remove_empty_directories(self.parameter.root)
        self.parameter.logger.info(_("正在关闭程序"))
