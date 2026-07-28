# TikTokDownloader-Web

简体中文 

基于 TikTokDownloader 魔改的抖音作品下载工具 · 仅保留 API 模式 · 内置 Web 界面

![Version](https://img.shields.io/badge/version-1.0.0-161823?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.12-2d2f3e?style=flat-square\&logo=python\&logoColor=ffffff)
![License](https://img.shields.io/github/license/komens/TikTokDownloader-Web?style=flat-square\&color=161823)
![Stars](https://img.shields.io/github/stars/komens/TikTokDownloader-Web?style=flat-square\&color=4a4a4a)
![Forks](https://img.shields.io/github/forks/komens/TikTokDownloader-Web?style=flat-square\&color=8a8a8a)

> **感谢原作者** **[JoeanAmier](https://github.com/JoeanAmier)** **及原项目** **[TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)**
>
> 本项目是基于 `TikTokDownloader` 的二次开发版本。原项目是一个功能完整的抖音 / TikTok 数据采集工具，支持终端交互、Web UI、Web API 等多种模式。本项目在其基础上进行了精简和改造：
>
> - **移除**：终端交互模式、TikTok 平台支持、扫码登录、热榜/搜索/评论采集等非核心功能
> - **保留**：抖音作品下载、账号作品批量下载、API 模式
> - **新增**：内置 Vue 3 + Element Plus + Tailwind CSS 的 Web 界面，支持下载队列、作品列表、详情浏览、缩略图预览、xgplayer 视频播放等

***

## 项目功能

- 抖音作品 / 图集下载（视频、图片、封面、音乐）
- 抖音账号作品批量下载（支持 post / favorite / collection）
- 作品数据持久化存储（SQLite）
- 异步下载队列（短链哈希幂等去重、自动重试、过期清理）
- Web 界面（响应式，支持桌面 / 移动端）
- 作品列表（表格 / 瀑布流双视图，分页 / 搜索）
- 作品详情（PC 沉浸式 + 移动端沉浸式滑动浏览）
- 缩略图自动生成（视频首帧）
- xgplayer 视频在线播放
- 文件管理（下载文件预览、批量打包下载）
- Web API 接口（FastAPI 自动文档）
- Docker 容器部署

## 快速开始

### 方式一：Python 环境运行

**1. 安装依赖**

```bash
# 推荐使用 Python 3.12+
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

**2. 配置 Cookie**

将 `Volume/settings.json` 中的 `cookie` 字段填入你的抖音 Cookie（获取方式见 [Cookie 提取教程](https://github.com/JoeanAmier/TikTokDownloader/blob/master/docs/Cookie%E8%8E%B7%E5%8F%96%E6%95%99%E7%A8%8B.md)）。

**3. 启动服务**

```bash
python main.py
```

启动后访问：

- **Web 界面**：<http://127.0.0.1:5555/>
- **API 文档**：<http://127.0.0.1:5555/docs>

### 方式二：Docker 部署

```bash
# 构建镜像（multi-stage build，会自动构建前端）
docker build -t tiktok-downloader-web .

# 运行容器
docker run -d \
  --name tiktok-downloader-web \
  -p 5555:5555 \
  -v tiktok_downloader_web_volume:/app/Volume \
  tiktok-downloader-web
```

访问 <http://127.0.0.1:5555/> 即可使用。

### 方式三：开发模式

前端代码位于 `web/` 目录，基于 Vite + Vue 3：

```bash
cd web
npm install
npm run dev       # 启动开发服务器（热更新）
npm run build     # 构建生产版本至 web/dist/，由后端静态托管
```

## 使用说明

### Web 界面

| 页面   | 路径            | 说明                        |
| ---- | ------------- | ------------------------- |
| 首页   | `/`           | 输入抖音链接，添加到下载队列            |
| 任务列表 | `/tasks`      | 查看所有下载作品，支持搜索、分页、表格/瀑布流切换 |
| 作品详情 | `/detail/:id` | 查看作品详情，在线播放视频 / 浏览图片      |
| 设置   | `/settings`   | 配置下载参数                    |

### 下载队列

- 输入抖音短链后立即入队（毫秒级响应，无需等待网络请求）
- 后台异步解析短链并下载
- 同一短链重复提交自动去重
- 已完成任务按配置天数（默认 7 天）自动清理

### API 接口

启动后访问 <http://127.0.0.1:5555/docs> 查看完整 API 文档。核心接口：

| 方法     | 路径                         | 说明        |
| ------ | -------------------------- | --------- |
| POST   | `/douyin/download`         | 添加作品到下载队列 |
| POST   | `/douyin/detail`           | 获取作品详情    |
| POST   | `/douyin/account`          | 批量下载账号作品  |
| GET    | `/douyin/list`             | 获取作品列表    |
| GET    | `/douyin/queue`            | 获取下载队列状态  |
| GET    | `/douyin/detail/{work_id}` | 获取单个作品详情  |
| DELETE | `/douyin/delete/{work_id}` | 删除作品      |
| DELETE | `/douyin/queue/{work_id}`  | 从队列移除任务   |

#### 调用示例

```python
import httpx

# 添加下载任务
response = httpx.post(
    "http://127.0.0.1:5555/douyin/download",
    json={"url": "https://v.douyin.com/xxxxxxx/"},
)
print(response.json())

# 查询队列状态
response = httpx.get("http://127.0.0.1:5555/douyin/queue")
print(response.json())
```

## 配置说明

配置文件位于 `Volume/settings.json`，核心字段：

| 字段                     | 默认值          | 说明                 |
| ---------------------- | ------------ | ------------------ |
| `cookie`               | `""`         | 抖音 Cookie（必填）      |
| `root`                 | `"Volume"`   | 数据/文件存储根目录         |
| `folder_name`          | `"Download"` | 下载文件子目录            |
| `max_retry`            | `5`          | 下载失败最大重试次数         |
| `queue_retention_days` | `7`          | 下载队列任务保留天数         |
| `proxy`                | `null`       | HTTP 代理地址          |
| `browser_info`         | `{...}`      | 浏览器 User-Agent 等信息 |

## 项目结构

```
TikTokDownloader-Web/
├── src/                    # 后端 Python 代码
│   ├── application/        # 应用层（API 服务器、队列管理、缩略图）
│   ├── config/             # 配置参数处理
│   ├── custom/             # 项目常量、版本号
│   ├── extract/            # 链接提取
│   ├── manager/            # 数据库、记录器
│   └── ...                 # 其他模块
├── web/                    # 前端 Vue 3 项目
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── stores/         # Pinia 状态管理
│   │   └── api/            # API 调用
│   └── dist/               # 构建产物（由后端托管）
├── Volume/                 # 运行时数据（自动创建）
│   ├── settings.json       # 配置文件
│   ├── download_queue.json # 下载队列
│   └── Download/           # 下载文件
├── main.py                 # 程序入口
├── Dockerfile              # Docker 构建文件（multi-stage）
├── pyproject.toml          # Python 项目元数据
└── requirements.txt        # Python 依赖
```

## 免责声明

<details>
<summary><b>点击展开完整免责声明</b></summary>

1. 使用者对本项目的使用由使用者自行决定，并自行承担风险。作者对使用者使用本项目所产生的任何损失、责任、或风险概不负责。
2. 本项目的作者提供的代码和功能是基于现有知识和技术的开发成果。作者按现有技术水平努力确保代码的正确性和安全性，但不保证代码完全没有错误或缺陷。
3. 本项目依赖的所有第三方库、插件或服务各自遵循其原始开源或商业许可，使用者需自行查阅并遵守相应协议，作者不对第三方组件的稳定性、安全性及合规性承担任何责任。
4. 使用者在使用本项目时必须严格遵守 [GNU General Public License v3.0](./license) 的要求，并在适当的地方注明使用了 [GNU General Public License v3.0](./license) 的代码。
5. 使用者在使用本项目的代码和功能时，必须自行研究相关法律法规，并确保其使用行为合法合规。任何因违反法律法规而导致的法律责任和风险，均由使用者自行承担。
6. 使用者不得使用本工具从事任何侵犯知识产权的行为，包括但不限于未经授权下载、传播受版权保护的内容，开发者不参与、不支持、不认可任何非法内容的获取或分发。
7. 本项目不对使用者涉及的数据收集、存储、传输等处理活动的合规性承担责任。使用者应自行遵守相关法律法规，确保处理行为合法正当；因违规操作导致的法律责任由使用者自行承担。
8. 使用者在任何情况下均不得将本项目的作者、贡献者或其他相关方与使用者的使用行为联系起来，或要求其对使用者使用本项目所产生的任何损失或损害负责。
9. 本项目的作者不会提供 TikTokDownloader-Web 项目的付费版本，也不会提供与 TikTokDownloader-Web 项目相关的任何商业服务。
10. **本项目是基于** **[TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader)（原作者** **[JoeanAmier](https://github.com/JoeanAmier)）的二次开发版本。基于本项目进行的任何二次开发、修改或编译的程序与原创作者无关，原创作者不承担与二次开发行为或其结果相关的任何责任，使用者应自行对因二次开发可能带来的各种情况负全部责任。**
11. 本项目不授予使用者任何专利许可；若使用本项目导致专利纠纷或侵权，使用者自行承担全部风险和责任。未经作者或权利人书面授权，不得使用本项目进行任何商业宣传、推广或再授权。
12. 作者保留随时终止向任何违反本声明的使用者提供服务的权利，并可能要求其销毁已获取的代码及衍生作品。
13. 作者保留在不另行通知的情况下更新本声明的权利，使用者持续使用即视为接受修订后的条款。

**在使用本项目的代码和功能之前，请您认真考虑并接受以上免责声明。如果您对上述声明有任何疑问或不同意，请不要使用本项目的代码和功能。如果您使用了本项目的代码和功能，则视为您已完全理解并接受上述免责声明，并自愿承担使用本项目的一切风险和后果。**

</details>

## 开源许可

本项目基于 [GNU General Public License v3.0](./license) 协议开源。

根据 GPL-3.0 协议的传染性条款：

- 任何基于本项目的二次开发、修改或分发版本**必须**同样以 GPL-3.0 协议开源
- 必须保留原作者的版权声明和许可证文件
- 必须注明本项目及其上游项目 `TikTokDownloader` 的来源

## 致谢

| 项目                                                                 | 作者                                          | 说明                        |
| ------------------------------------------------------------------ | ------------------------------------------- | ------------------------- |
| [TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader) | [JoeanAmier](https://github.com/JoeanAmier) | 本项目的上游原始项目，提供了核心的抖音数据采集能力 |
| [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)     | [JoeanAmier](https://github.com/JoeanAmier) | 前端结构与交互参考                 |

本项目还使用了以下开源技术栈，在此一并致谢：

- **后端**：[FastAPI](https://github.com/tiangolo/fastapi)、[httpx](https://github.com/encode/httpx)、[uvicorn](https://github.com/encode/uvicorn)、[aiosqlite](https://github.com/omnilib/aiosqlite)、[rich](https://github.com/Textualize/rich)
- **前端**：[Vue 3](https://github.com/vuejs/core)、[Element Plus](https://github.com/element-plus/element-plus)、[Tailwind CSS](https://github.com/tailwindlabs/tailwindcss)、[Pinia](https://github.com/vuejs/pinia)、[Vue Router](https://github.com/vuejs/router)、[xgplayer](https://github.com/bytedance/xgplayer)、[Vite](https://github.com/vitejs/vite)

## 项目参考

- 上游项目：<https://github.com/JoeanAmier/TikTokDownloader>
- 参考项目：<https://github.com/JoeanAmier/XHS-Downloader>

