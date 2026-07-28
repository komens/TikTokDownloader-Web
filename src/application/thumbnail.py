"""视频缩略图生成模块

从视频中提取第一帧作为缩略图，用于前端列表展示
"""
from pathlib import Path
from typing import Optional


class ThumbnailGenerator:
    """视频缩略图生成器"""

    def __init__(self, print_func=None):
        self.print = print_func or print

    def generate_thumbnail(
        self,
        video_path: Path,
        thumbnail_path: Path,
        frame_position: int = 0,
        max_width: int = 480,
        quality: int = 85,
    ) -> bool:
        """从视频生成缩略图

        Args:
            video_path: 视频文件路径
            thumbnail_path: 缩略图保存路径
            frame_position: 提取的帧位置(默认为第一帧)
            max_width: 缩略图最大宽度(像素)，保持宽高比缩放
            quality: JPEG压缩质量(1-100)

        Returns:
            bool: 是否成功生成缩略图
        """
        try:
            import cv2
        except ImportError:
            # opencv 未安装时记录日志便于诊断
            self.print(f"未安装 opencv-python-headless，无法生成视频缩略图: {video_path.name}")
            return False

        try:
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            # cv2 对非 ASCII 路径兼容性较差，使用 imdecode/imencode 避免直接读取
            import numpy as np
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                self.print(f"无法打开视频文件: {video_path.name}")
                return False
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total_frames == 0:
                cap.release()
                self.print(f"视频帧数为 0: {video_path.name}")
                return False
            if frame_position >= total_frames:
                frame_position = total_frames // 2
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                self.print(f"读取视频帧失败: {video_path.name}")
                return False
            height, width = frame.shape[:2]
            if width > max_width:
                scale_ratio = max_width / width
                new_width = max_width
                new_height = int(height * scale_ratio)
                frame = cv2.resize(
                    frame,
                    (new_width, new_height),
                    interpolation=cv2.INTER_AREA,
                )
            # 使用 imencode + 文件写入，避免 cv2.imwrite 对中文路径的兼容性问题
            success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if not success:
                self.print(f"编码 JPEG 失败: {video_path.name}")
                return False
            with open(thumbnail_path, "wb") as f:
                f.write(buffer.tobytes())
            return True
        except Exception as e:
            self.print(f"生成缩略图异常 {video_path.name}: {e}")
            return False

    def generate_video_thumbnail(
        self,
        video_file: Path,
        temp_dir: Path,
    ) -> Optional[Path]:
        """为视频文件生成缩略图

        Args:
            video_file: 视频文件路径
            temp_dir: 临时目录路径(Temp 目录)

        Returns:
            缩略图文件路径,失败返回 None
        """
        if not video_file.exists():
            return None
        if video_file.suffix.lower() not in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}:
            return None
        thumbnail_name = video_file.stem + '.jpg'
        thumbnail_path = temp_dir / thumbnail_name
        if thumbnail_path.exists():
            return thumbnail_path
        if self.generate_thumbnail(video_file, thumbnail_path):
            return thumbnail_path
        return None
