"""
iflow2web 配置文件
从环境变量和.env文件加载配置
"""

import os
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 服务器配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")  # 监听所有网络接口，允许局域网访问
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))  # 服务器端口

# WebSocket 配置
WS_MAX_CONNECTIONS = int(os.getenv("WS_MAX_CONNECTIONS", "10"))  # 最大并发连接数
WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "20"))  # 心跳间隔（秒）
WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", "60"))  # 心跳超时（秒）

# iFlow 配置
# 默认工作目录（从环境变量读取，如果为空则使用当前目录）
IFLOW_DEFAULT_WORKING_DIR = os.getenv("IFLOW_DEFAULT_WORKING_DIR", "")
IFLOW_APPROVAL_MODE = os.getenv("IFLOW_APPROVAL_MODE", "YOLO")  # 审批模式: DEFAULT, AUTO_EDIT, YOLO, PLAN

# 模型配置
IFLOW_DEFAULT_MODEL = os.getenv("IFLOW_DEFAULT_MODEL", "glm-4.7")  # 默认模型（推荐）
IFLOW_AVAILABLE_MODELS = [
    # 从API获取的模型
    "iflow-rome-30ba3b",
    "qwen3-coder-plus",
    "qwen3-max",
    "qwen3-vl-plus",
    "kimi-k2-0905",
    "qwen3-max-preview",
    "glm-4.6",
    "kimi-k2",
    "deepseek-v3.2",
    "deepseek-r1",
    "deepseek-v3",
    "qwen3-32b",
    "qwen3-235b-a22b-thinking-2507",
    "qwen3-235b-a22b-instruct",
    "qwen3-235b",
    # 额外支持的模型（API返回中未包含但可用）
    "glm-4.7",
    "DeepSeek-V3.2",
    "Qwen3-Coder-Plus",
    "Kimi-K2-Thinking",
    "MiniMax-M2.1",
    "Kimi-K2.5",
]  # 可用模型列表（从API动态获取 + 额外支持的模型）

# 允许的工作目录白名单（安全限制）
# TODO: 如果需要限制访问的目录，取消注释并添加允许的目录列表
# ALLOWED_WORKING_DIRS = [
#     "F:\\pythonProjects\\iflow2web",
#     "F:\\pythonProjects\\project1",
#     "F:\\pythonProjects\\project2",
# ]
ALLOWED_WORKING_DIRS = None  # None 表示允许访问任意目录（仅限个人使用）

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")  # DEBUG, INFO, WARNING, ERROR

# 前端配置
TERMINAL_THEME = os.getenv("TERMINAL_THEME", "dark")  # dark, light
TERMINAL_FONT_FAMILY = os.getenv("TERMINAL_FONT_FAMILY", "Consolas, Monaco, 'Courier New', monospace")
TERMINAL_FONT_SIZE = os.getenv("TERMINAL_FONT_SIZE", "14px")