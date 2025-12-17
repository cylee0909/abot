# 项目技术栈约定

## 前端技术栈
- 框架：`React ^19.2.0`
- 构建与开发：`Vite ^7.2.4`、`@vitejs/plugin-react ^5.1.1` 、`yarn`
- 语言：`JavaScript (JSX)`（当前代码为 `.jsx`，未使用 TypeScript）
- 可视化：`ECharts ^6.0.0`
- 代码质量：`ESLint ^9.39.1`、`@eslint/js`、`eslint-plugin-react-hooks`、`eslint-plugin-react-refresh`

## 后端技术栈
- 语言与运行时：`Python >= 3.10`
- Web 框架：`Flask >= 3.1.0`
- 配置管理：`pydantic-settings >= 2.12.0`
- 数据库：`SQLite`（文件路径：`data/stock_history.db`）
- 数据/网络相关：`AkShare == 1.16.99`、`pandas >= 2.3.3`、`numpy >= 2.2.6`、`aiohttp >= 3.13.2`；必要时使用 `requests` 获取雪球 `xq_a_token`
- 使用uv 管理python包 和运行服务

## 端口与互通
- 前端开发服务：`http://localhost:5173`
- 后端 API 服务：`http://127.0.0.1:5001`
- CORS：允许 `*`，方法 `GET, OPTIONS`，头 `Content-Type`

> 以上版本信息来源：`frontend/package.json` 与 `backend/pyproject.toml`，并结合后端源码实际使用的库。
