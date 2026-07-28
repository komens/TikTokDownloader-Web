"""作品元数据记录器

存储作品完整元数据到 SQLite，支持分页查询、搜索过滤、按 ID 查询、删除等操作。
字段使用中文名（与前端 types/index.ts 对齐）。
"""
from asyncio import CancelledError
from contextlib import suppress
from json import loads, dumps
from pathlib import Path
from typing import Optional, Dict, List, Any

from aiosqlite import connect

__all__ = ["DataRecorder"]


class DataRecorder:
    """作品元数据记录器

    数据库 schema 与参照项目（XHS-Downloader-Web）保持一致，
    使用中文字段名以便前端类型对齐。
    """

    # 数据表结构：(字段名, 类型)
    DATA_TABLE = (
        ("采集时间", "TEXT"),
        ("作品ID", "TEXT PRIMARY KEY"),
        ("作品类型", "TEXT"),
        ("作品标题", "TEXT"),
        ("作品描述", "TEXT"),
        ("作品标签", "TEXT"),
        ("发布时间", "TEXT"),
        ("最后更新时间", "TEXT"),
        ("收藏数量", "TEXT"),
        ("评论数量", "TEXT"),
        ("分享数量", "TEXT"),
        ("点赞数量", "TEXT"),
        ("作者昵称", "TEXT"),
        ("作者ID", "TEXT"),
        ("作者链接", "TEXT"),
        ("作品链接", "TEXT"),
        ("下载地址", "TEXT"),
        ("动图地址", "TEXT"),
        ("下载文件路径", "TEXT"),
    )

    def __init__(self, root: Path, folder: Path, switch: bool = True):
        """
        Args:
            root: Volume 根目录（存放数据库文件）
            folder: 下载文件夹（兼容旧版可能存放 ExploreData.db）
            switch: 是否启用数据记录
        """
        self.name = "ExploreData.db"
        self.root = root
        self.folder = folder
        self.file = root.joinpath(self.name)
        self.switch = switch
        self.database = None
        self.cursor = None

    async def _connect_database(self):
        self.database = await connect(self.file)
        self.cursor = await self.database.cursor()
        await self.database.execute(
            f"CREATE TABLE IF NOT EXISTS explore_data ("
            f"{','.join(' '.join(i) for i in self.DATA_TABLE)}"
            f");"
        )
        await self.database.commit()
        # 兼容性：检查并添加缺失的列
        await self.cursor.execute("PRAGMA table_info(explore_data)")
        existing_columns = {row[1] for row in await self.cursor.fetchall()}
        for column_name, _ in self.DATA_TABLE:
            if column_name not in existing_columns:
                await self.database.execute(
                    f"ALTER TABLE explore_data ADD COLUMN {column_name} TEXT"
                )
                await self.database.commit()

    async def select(self, id_: str) -> Optional[Dict[str, Any]]:
        """按作品 ID 查询单条记录"""
        if not self.switch:
            return None
        await self.cursor.execute(
            "SELECT * FROM explore_data WHERE 作品ID=?", (id_,)
        )
        result = await self.cursor.fetchone()
        if result:
            return self._parse_data(
                {i[0]: result[idx] for idx, i in enumerate(self.DATA_TABLE)}
            )
        return None

    async def select_all(
        self,
        page: int = 1,
        page_size: int = 20,
        search_conditions: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """分页查询作品数据列表，支持模糊搜索"""
        if not self.switch:
            return []
        offset = (page - 1) * page_size
        where_clauses = []
        params: List[Any] = []
        if search_conditions:
            for field, value in search_conditions.items():
                if value:
                    where_clauses.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
        if where_clauses:
            where_sql = " AND ".join(where_clauses)
            query = (
                f"SELECT * FROM explore_data WHERE {where_sql} "
                f"ORDER BY 采集时间 DESC LIMIT {page_size} OFFSET {offset}"
            )
        else:
            query = (
                f"SELECT * FROM explore_data ORDER BY 采集时间 DESC "
                f"LIMIT {page_size} OFFSET {offset}"
            )
        await self.cursor.execute(query, params)
        results = await self.cursor.fetchall()
        return [
            self._parse_data(
                {i[0]: result[idx] for idx, i in enumerate(self.DATA_TABLE)}
            )
            for result in results
        ]

    async def count(self, search_conditions: Optional[Dict[str, str]] = None) -> int:
        """统计作品总数，支持搜索条件"""
        if not self.switch:
            return 0
        where_clauses = []
        params: List[Any] = []
        if search_conditions:
            for field, value in search_conditions.items():
                if value:
                    where_clauses.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
        if where_clauses:
            where_sql = " AND ".join(where_clauses)
            query = f"SELECT COUNT(*) FROM explore_data WHERE {where_sql}"
        else:
            query = "SELECT COUNT(*) FROM explore_data"
        await self.cursor.execute(query, params)
        result = await self.cursor.fetchone()
        return result[0] if result else 0

    async def add(self, **kwargs) -> None:
        """新增或替换一条作品记录"""
        if not self.switch:
            return
        # 确保所有字段都存在，缺失的填空字符串
        for column_name, _ in self.DATA_TABLE:
            if column_name not in kwargs:
                kwargs[column_name] = ""
        await self.database.execute(
            f"""REPLACE INTO explore_data (
            {", ".join(i[0] for i in self.DATA_TABLE)}
            ) VALUES (
            {", ".join("?" for _ in self.DATA_TABLE)}
            );""",
            self._generate_values(kwargs),
        )
        await self.database.commit()

    async def update_file_paths(self, id_: str, file_paths: List[str]) -> None:
        """更新指定作品的下载文件路径字段"""
        if not self.switch or not id_:
            return
        await self.database.execute(
            "UPDATE explore_data SET 下载文件路径=? WHERE 作品ID=?",
            (dumps(file_paths, ensure_ascii=False), id_),
        )
        await self.database.commit()

    async def delete(self, ids: List[str]) -> None:
        """删除一条或多条作品记录"""
        if not self.switch:
            return
        for id_ in ids:
            if id_:
                await self.database.execute(
                    "DELETE FROM explore_data WHERE 作品ID=?", (id_,)
                )
        await self.database.commit()

    def _parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据，将 JSON 字符串转为数组"""
        if data.get("下载文件路径"):
            try:
                data["下载文件路径"] = loads(data["下载文件路径"])
            except (ValueError, TypeError):
                data["下载文件路径"] = []
        else:
            data["下载文件路径"] = []
        if data.get("下载地址"):
            try:
                data["下载地址"] = loads(data["下载地址"])
            except (ValueError, TypeError):
                # 兼容旧数据：空格分隔的字符串
                data["下载地址"] = data["下载地址"].split() if data["下载地址"] else []
        else:
            data["下载地址"] = []
        if data.get("动图地址"):
            try:
                data["动图地址"] = loads(data["动图地址"])
            except (ValueError, TypeError):
                data["动图地址"] = data["动图地址"].split() if data["动图地址"] else []
        else:
            data["动图地址"] = []
        return data

    def _generate_values(self, data: Dict[str, Any]) -> tuple:
        """按 DATA_TABLE 顺序生成插入值"""
        values = []
        for column_name, _ in self.DATA_TABLE:
            value = data.get(column_name, "")
            # 列表/字典类型转 JSON 字符串
            if isinstance(value, (list, dict)):
                value = dumps(value, ensure_ascii=False)
            elif value is None:
                value = ""
            values.append(value)
        return tuple(values)

    async def __aenter__(self):
        self._ensure_parent_dir()
        await self._connect_database()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.cursor:
            with suppress(CancelledError):
                await self.cursor.close()
        if self.database:
            await self.database.close()

    def _ensure_parent_dir(self):
        """确保数据库文件所在目录存在"""
        self.file.parent.mkdir(parents=True, exist_ok=True)
