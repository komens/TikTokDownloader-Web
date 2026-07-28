# ---- 阶段 1: 前端构建 (Frontend Builder) ----
# 使用 Node 镜像构建前端静态资源
FROM node:20-slim AS frontend

WORKDIR /web

# 先复制依赖清单，利用 Docker 缓存层
COPY web/package.json web/package-lock.json ./

# 安装依赖
RUN npm ci --no-audit --no-fund

# 复制前端源码并构建
COPY web/ ./
RUN npm run build

# ---- 阶段 2: Python 依赖构建器 (Python Builder) ----
# 使用一个功能完整的镜像，它包含编译工具或可以轻松安装它们
FROM python:3.12-bullseye AS builder

# 安装编译 uvloop 和 httptools 所需的系统依赖 (C编译器等)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制需求文件
COPY requirements.txt .

# 在这个具备编译环境的阶段安装所有 Python 依赖
# 安装到一个独立的目录 /install 中，以便后续复制
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# ---- 阶段 3: 最终镜像 (Final Image) ----
# 使用轻量级 slim 镜像作为最终的运行环境
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 添加元数据标签
LABEL name="TikTokDownloader-Web" \
      version="1.0.0" \
      authors="Komens" \
      repository="https://github.com/komens/TikTokDownloader-Web" \
      upstream="https://github.com/JoeanAmier/TikTokDownloader" \
      license="GPL-3.0"

# 从构建器阶段，将已经安装好的依赖包复制到最终镜像的系统路径中
COPY --from=builder /install /usr/local

# 复制后端应用程序代码和相关文件
COPY src /app/src
COPY locale /app/locale
COPY static /app/static
COPY license /app/license
COPY main.py /app/main.py

# 从前端构建阶段，复制构建产物到 web/dist（由后端 FastAPI 静态托管）
COPY --from=frontend /web/dist /app/web/dist

# 暴露端口
EXPOSE 5555

# 创建挂载点（运行时数据：配置、下载文件、队列、数据库）
VOLUME /app/Volume

# 设置容器启动命令
CMD ["python", "main.py"]
