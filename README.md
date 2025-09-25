

# CSIndex - 股票指数分析工具

一个用于分析股票指数成分股的 Web 应用程序。

## 功能特性

- 📊 支持中证指数和国证指数数据源
- 🔍 指数成分股查询和展示
- 📈 指数重叠度热力图可视化
- 🎯 多指数重叠分析
- 💡 实时数据获取和缓存

## 技术栈

### 后端
- Python 3.12+
- Flask - Web 框架
- AKShare - 金融数据接口
- NumPy & Pandas - 数据处理

### 前端
- Vue 3 - 前端框架
- Element Plus - UI 组件库
- ECharts - 图表可视化
- Axios - HTTP 客户端

## 快速开始

### 环境要求
- Python 3.12+
- Node.js 16+
- uv (Python 包管理器)

### 安装依赖

1. 安装 Python 依赖：
```bash
uv sync
```

2. 安装前端依赖：
```bash
cd frontend
npm install
```

### 运行项目

1. 启动后端服务：
```bash
python app.py
```
后端服务将在 http://127.0.0.1:5001 启动

2. 启动前端开发服务器：
```bash
cd frontend
npm run serve
```
前端服务将在 http://localhost:8081 启动

### 访问应用

打开浏览器访问 http://localhost:8081 即可使用应用。

## API 接口

- `GET /api/index_providers` - 获取指数提供商列表
- `GET /api/indices/<provider>` - 获取指定提供商的指数列表
- `GET /api/index_components` - 获取指数成分股数据
- `POST /api/index_heatmap` - 生成指数热力图数据
- `POST /api/calculate_overlap` - 计算指数重叠度

## 项目结构

```
csindex/
├── app.py              # Flask 后端应用
├── pyproject.toml      # Python 项目配置
├── frontend/           # Vue 前端应用
│   ├── src/
│   │   ├── components/ # Vue 组件
│   │   ├── views/      # 页面视图
│   │   └── api/        # API 配置
│   └── package.json    # 前端依赖配置
└── README.md          # 项目说明
```

## 开发说明

本项目使用 uv 作为 Python 包管理器，所有 Python 依赖都在 `pyproject.toml` 中定义。前端使用 Vue CLI 构建，支持热重载开发。

## 许可证

MIT License