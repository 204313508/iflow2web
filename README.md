<div align="center">

# iflow2web

**iFlow CLI Web Interface** / **iFlow CLI Web 界面**

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🌐 Language / 语言

**[English](#english)** | **[中文](#中文)**

---

<a id="english"></a>

## English

### 📖 Introduction

**iflow2web** is a web-based interface for iFlow CLI, built with FastAPI and WebSocket. It provides a terminal-like interface for interacting with iFlow CLI through your browser, supporting multiple sessions and real-time communication.

### ✨ Features

- 🖥️ **Web Terminal**: Terminal-like interface in your browser
- 💬 **Real-time Communication**: WebSocket-based real-time message exchange
- 📁 **Multi-session Management**: Create, switch, and manage multiple sessions
- 🤖 **Multiple Models**: Support for various AI models (GLM-4.7, Qwen3, DeepSeek, etc.)
- 🎨 **Customizable Themes**: Dark/Light terminal themes
- 🚀 **Easy Deployment**: Simple setup with Docker or Python environment

### 🚀 Quick Start

#### Prerequisites

- Python 3.12+
- pip

#### Installation

1. **Clone the repository**
```bash
git clone https://github.com/204313508/iflow2web.git
cd iflow2web
```

2. **Create virtual environment**
```bash
python -m venv iflow2web
iflow2web\Scripts\activate  # Windows
# or
source iflow2web/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env to configure your settings
```

5. **Run the server**
```bash
python main.py
```

Or use the batch file on Windows:
```bash
start.bat
```

6. **Open your browser**
Visit `http://localhost:8000`

### ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# iFlow
IFLOW_DEFAULT_WORKING_DIR=
IFLOW_DEFAULT_MODEL=glm-4.7

# Terminal
TERMINAL_THEME=dark
TERMINAL_FONT_FAMILY=Consolas, Monaco, 'Courier New', monospace
TERMINAL_FONT_SIZE=14px

# Log
LOG_LEVEL=INFO
```

### 📁 Project Structure

```
iflow2web/
├── main.py                 # FastAPI application entry
├── config.py               # Configuration settings
├── websocket_handler.py    # WebSocket message handling
├── session_manager.py      # Session management
├── iflow_manager.py        # iFlow CLI integration
├── static/                 # Static files (CSS, JS)
├── templates/              # HTML templates
├── tests/                  # Unit tests
├── requirements.txt        # Python dependencies
└── .env.example           # Environment variables template
```

### 🧪 Testing

Run tests with pytest:

```bash
pytest
```

With coverage:

```bash
pytest --cov=. --cov-report=html
```

### 🛠️ Development

#### Running with hot reload

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### API Endpoints

- `GET /` - Web interface
- `GET /health` - Health check
- `GET /api/models` - Get available models
- `GET /api/sessions` - List all sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{id}` - Get session details
- `DELETE /api/sessions/{id}` - Delete session
- `WS /ws` - WebSocket endpoint

### 📝 License

MIT License

---

<a id="中文"></a>

## 中文

### 📖 简介

**iflow2web** 是一个基于 Web 的 iFlow CLI 界面，使用 FastAPI 和 WebSocket 构建。它提供了类似终端的浏览器界面，支持通过浏览器与 iFlow CLI 进行交互，支持多会话管理和实时通信。

### ✨ 特性

- 🖥️ **Web 终端**：浏览器中的类终端界面
- 💬 **实时通信**：基于 WebSocket 的实时消息交换
- 📁 **多会话管理**：创建、切换和管理多个会话
- 🤖 **多种模型支持**：支持多种 AI 模型（GLM-4.7、Qwen3、DeepSeek 等）
- 🎨 **自定义主题**：深色/浅色终端主题
- 🚀 **简单部署**：使用 Docker 或 Python 环境轻松部署

### 🚀 快速开始

#### 环境要求

- Python 3.12+
- pip

#### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/204313508/iflow2web.git
cd iflow2web
```

2. **创建虚拟环境**
```bash
python -m venv iflow2web
iflow2web\Scripts\activate  # Windows
# 或
source iflow2web/bin/activate  # Linux/Mac
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 配置您的设置
```

5. **运行服务器**
```bash
python main.py
```

或在 Windows 上使用批处理文件：
```bash
start.bat
```

6. **打开浏览器**
访问 `http://localhost:8000`

### ⚙️ 配置

在项目根目录创建 `.env` 文件：

```env
# 服务器
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# iFlow
IFLOW_DEFAULT_WORKING_DIR=
IFLOW_DEFAULT_MODEL=glm-4.7

# 终端
TERMINAL_THEME=dark
TERMINAL_FONT_FAMILY=Consolas, Monaco, 'Courier New', monospace
TERMINAL_FONT_SIZE=14px

# 日志
LOG_LEVEL=INFO
```

### 📁 项目结构

```
iflow2web/
├── main.py                 # FastAPI 应用入口
├── config.py               # 配置设置
├── websocket_handler.py    # WebSocket 消息处理
├── session_manager.py      # 会话管理
├── iflow_manager.py        # iFlow CLI 集成
├── static/                 # 静态文件（CSS、JS）
├── templates/              # HTML 模板
├── tests/                  # 单元测试
├── requirements.txt        # Python 依赖
└── .env.example           # 环境变量模板
```

### 🧪 测试

使用 pytest 运行测试：

```bash
pytest
```

生成覆盖率报告：

```bash
pytest --cov=. --cov-report=html
```

### 🛠️ 开发

#### 使用热重载运行

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### API 端点

- `GET /` - Web 界面
- `GET /health` - 健康检查
- `GET /api/models` - 获取可用模型
- `GET /api/sessions` - 列出所有会话
- `POST /api/sessions` - 创建新会话
- `GET /api/sessions/{id}` - 获取会话详情
- `DELETE /api/sessions/{id}` - 删除会话
- `WS /ws` - WebSocket 端点

### 📝 许可证

MIT License

---

<div align="center">

Made with ❤️ by [iflow2web](https://github.com/204313508/iflow2web)

</div>