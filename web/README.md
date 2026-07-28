# TikTokDownloader-Web Frontend

TikTokDownloader-Web 项目的前端代码，基于 Vue 3 + TypeScript + Vite 构建。

## 技术栈

- **框架**：[Vue 3](https://github.com/vuejs/core)（`<script setup>` 语法）
- **构建工具**：[Vite 6](https://github.com/vitejs/vite)
- **UI 库**：[Element Plus](https://github.com/element-plus/element-plus)
- **样式**：[Tailwind CSS 4](https://github.com/tailwindlabs/tailwindcss)
- **状态管理**：[Pinia](https://github.com/vuejs/pinia)
- **路由**：[Vue Router 4](https://github.com/vuejs/router)（hash 模式）
- **视频播放器**：[xgplayer](https://github.com/bytedance/xgplayer)
- **HTTP 客户端**：[axios](https://github.com/axios/axios)
- **图标**：[@element-plus/icons-vue](https://github.com/element-plus/element-plus-icons)

## 目录结构

```
web/
├── public/                 # 静态资源（favicon 等）
├── src/
│   ├── api/                # API 调用封装
│   ├── assets/             # 资源文件
│   ├── components/         # 公共组件（AppLayout）
│   ├── router/             # 路由配置
│   ├── stores/             # Pinia 状态管理（download / settings）
│   ├── types/              # TypeScript 类型定义
│   ├── utils/              # 工具函数
│   ├── views/              # 页面组件
│   │   ├── DetailView/     # 作品详情页（PC + 移动端）
│   │   ├── TaskListView/   # 任务列表页（表格 + 瀑布流）
│   │   ├── HomeView.vue    # 首页（下载队列）
│   │   └── SettingsView.vue# 设置页
│   ├── App.vue
│   ├── main.ts
│   └── style.css           # 全局样式与主题变量
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 开发

```bash
# 安装依赖
npm install

# 启动开发服务器（默认 http://localhost:5173）
npm run dev

# 类型检查
npm run build -- --mode typecheck
```

开发时需要在 `vite.config.ts` 中配置后端 API 代理，将 `/douyin` 等接口请求转发到 `http://127.0.0.1:5555`。

## 构建

```bash
# 构建生产版本到 dist/
npm run build
```

构建产物位于 `web/dist/`，由后端 FastAPI 静态托管，无需独立部署前端服务。

## 主题

主题色定义在 [src/style.css](src/style.css) 的 `@theme` 块中，采用黑/白/灰极简主题：

```css
@theme {
  --color-primary: #161823;       /* 主色：黑 */
  --color-primary-light: #2d2f3e; /* 深灰 */
  --color-primary-dark: #000000;  /* 纯黑 */
  --color-secondary: #4a4a4a;     /* 辅助灰 */
  --color-accent: #161823;        /* 强调色 */
}
```

修改这些 CSS 变量即可全局切换主题。

## 版本

当前版本：`1.0.0`（见 [package.json](package.json)）

## 许可

本项目遵循 [GPL-3.0](../license) 协议，与主项目保持一致。
