"""
iFlow SDK 管理模块
使用 iflow-cli-sdk 与 iFlow CLI 通信
支持多会话，每个会话有独立的工作目录
"""

import asyncio
import os
from typing import AsyncGenerator, Optional
from iflow_sdk import IFlowClient, IFlowOptions, ApprovalMode
from iflow_sdk.types import (
    AssistantMessage,
    ToolCallMessage,
    PlanMessage,
    TaskFinishMessage,
)
import config
import logging

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """
    脱敏敏感数据（如API密钥）

    Args:
        data: 需要脱敏的数据
        mask_char: 掩码字符
        visible_chars: 可见字符数

    Returns:
        脱敏后的数据
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data)
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


class IFlowSession:
    """iFlow 会话 - 每个会话有独立的客户端"""

    def __init__(self, session_id: str, working_dir: str, model: str = None):
        self.session_id = session_id
        self.working_dir = working_dir
        self.model = model or config.IFLOW_DEFAULT_MODEL
        self._client: Optional[IFlowClient] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def initialize(self) -> None:
        """初始化 iFlow 客户端"""
        async with self._lock:
            if self._client is None:
                # 使用绝对路径
                abs_working_dir = os.path.abspath(self.working_dir)

                # 检查工作目录是否存在
                if not os.path.exists(abs_working_dir):
                    logger.warning(f"Working directory does not exist: {abs_working_dir}")
                    # 不修改全局工作目录，让iFlow SDK自己处理

                # 创建 iFlow 配置
                # 注意：模型配置需要在 iFlow CLI 的配置文件中设置（~/.iflow/settings.json）
                # 这里通过 metadata 传递模型信息，用于日志记录
                options = IFlowOptions(
                    approval_mode=ApprovalMode[config.IFLOW_APPROVAL_MODE],
                    auto_start_process=True,  # 自动管理 iFlow 进程
                    metadata={"model": self.model, "session_id": self.session_id}
                )

                # 创建客户端
                self._client = IFlowClient(options)
                await self._client.__aenter__()
                logger.info(f"Initialized iFlow client for session: {mask_sensitive_data(self.session_id)}, working_dir: {abs_working_dir}, model: {self.model}")

    async def send_message(self, message: str) -> AsyncGenerator[dict, None]:
        """
        发送消息给 iFlow 并接收响应

        Args:
            message: 用户消息

        Yields:
            dict: 消息数据，包含 type 和 content
        """
        if self._client is None:
            await self.initialize()

        # 发送消息
        await self._client.send_message(message)

        # 接收响应流
        async for msg in self._client.receive_messages():
            if isinstance(msg, AssistantMessage):
                # AI 回复消息（流式）
                response = {
                    "type": "assistant",
                    "content": msg.chunk.text if hasattr(msg.chunk, 'text') else "",
                    "is_stream": True,
                }
                # 添加额外信息
                if hasattr(msg, 'agent_id') and msg.agent_id:
                    response['agent_id'] = msg.agent_id
                if hasattr(msg, 'agent_info') and msg.agent_info:
                    response['agent_info'] = {
                        'agent_id': msg.agent_info.agent_id if hasattr(msg.agent_info, 'agent_id') else None,
                        'task_id': msg.agent_info.task_id if hasattr(msg.agent_info, 'task_id') else None,
                        'agent_index': msg.agent_info.agent_index if hasattr(msg.agent_info, 'agent_index') else None,
                    }
                yield response
            elif isinstance(msg, ToolCallMessage):
                # 工具调用消息
                response = {
                    "type": "tool",
                    "content": f"Tool: {msg.tool_name}",
                    "tool_name": msg.tool_name,
                    "status": msg.status,
                    "is_stream": False,
                }
                # 添加额外信息
                if hasattr(msg, 'args') and msg.args:
                    response['args'] = msg.args
                if hasattr(msg, 'confirmation') and msg.confirmation:
                    response['confirmation'] = msg.confirmation
                if hasattr(msg, 'content') and msg.content:
                    response['tool_content'] = msg.content
                if hasattr(msg, 'locations') and msg.locations:
                    response['locations'] = msg.locations
                if hasattr(msg, 'agent_id') and msg.agent_id:
                    response['agent_id'] = msg.agent_id
                if hasattr(msg, 'agent_info') and msg.agent_info:
                    response['agent_info'] = {
                        'agent_id': msg.agent_info.agent_id if hasattr(msg.agent_info, 'agent_id') else None,
                        'task_id': msg.agent_info.task_id if hasattr(msg.agent_info, 'task_id') else None,
                        'agent_index': msg.agent_info.agent_index if hasattr(msg.agent_info, 'agent_index') else None,
                    }
                yield response
            elif isinstance(msg, PlanMessage):
                # 任务计划消息
                yield {
                    "type": "plan",
                    "content": f"Plan created",
                    "is_stream": False,
                }
            elif isinstance(msg, TaskFinishMessage):
                # 任务完成消息
                response = {
                    "type": "finish",
                    "content": "Task finished",
                    "reason": msg.stop_reason if hasattr(msg, 'stop_reason') else "completed",
                    "is_stream": False,
                }
                yield response
                break  # 任务完成，退出循环

    async def close(self) -> None:
        """关闭 iFlow 客户端"""
        async with self._lock:
            if self._client is not None:
                await self._client.__aexit__(None, None, None)
                self._client = None
                logger.info(f"Closed iFlow client for session: {self.session_id}")


class IFlowManager:
    """iFlow 管理器 - 管理多个会话"""

    _instance: Optional["IFlowManager"] = None
    _sessions: dict[str, IFlowSession] = {}
    _lock: asyncio.Lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    async def get_available_models() -> dict:
        """
        从API获取可用的模型列表，并合并配置文件中的额外模型

        Returns:
            dict: 包含 default_model 和 available_models 的字典
        """
        import json
        import os

        try:
            # 读取配置文件获取API密钥
            settings_path = os.path.expanduser("~/.iflow/settings.json")
            api_key = None
            base_url = "https://apis.iflow.cn/v1"

            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    api_key = settings.get("apiKey")
                    base_url = settings.get("baseUrl", "https://apis.iflow.cn/v1")

            # 获取当前配置的默认模型（使用代码中的默认值）
            default_model = config.IFLOW_DEFAULT_MODEL

            if not api_key:
                logger.warning("No API key found in settings, using configured models")
                return {
                    "default_model": default_model,
                    "available_models": config.IFLOW_AVAILABLE_MODELS,
                }

            # 调用API获取模型列表
            import aiohttp
            models_url = f"{base_url}/models"
            headers = {"Authorization": f"Bearer {api_key}"}

            logger.info(f"Fetching models from API with key: {mask_sensitive_data(api_key)}")

            async with aiohttp.ClientSession() as session:
                async with session.get(models_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        api_models = [model["id"] for model in data.get("data", [])]

                        # 合并API返回的模型和配置文件中的额外模型
                        # 使用字典去重，保持顺序
                        all_models = {}
                        # 先添加配置文件中的模型（包括额外支持的模型）
                        for model in config.IFLOW_AVAILABLE_MODELS:
                            all_models[model] = True
                        # 再添加API返回的模型
                        for model in api_models:
                            all_models[model] = True

                        models = list(all_models.keys())

                        # 如果默认模型不在列表中，使用第一个模型
                        if default_model not in models:
                            default_model = models[0] if models else config.IFLOW_DEFAULT_MODEL

                        logger.info(f"Successfully fetched {len(api_models)} models from API, total {len(models)} models available")
                        return {
                            "default_model": default_model,
                            "available_models": models,
                        }
                    else:
                        logger.warning(f"Failed to fetch models from API (status: {response.status}), using configured models")
                        return {
                            "default_model": default_model,
                            "available_models": config.IFLOW_AVAILABLE_MODELS,
                        }
        except Exception as e:
            logger.error(f"Error fetching models from API: {e}, using configured models")
            return {
                "default_model": config.IFLOW_DEFAULT_MODEL,
                "available_models": config.IFLOW_AVAILABLE_MODELS,
            }

    async def get_or_create_session(self, session_id: str, working_dir: str, model: str = None) -> IFlowSession:
        """
        获取或创建会话

        Args:
            session_id: 会话 ID
            working_dir: 工作目录
            model: 模型名称

        Returns:
            IFlowSession: 会话对象
        """
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = IFlowSession(session_id, working_dir, model)
                logger.info(f"Created new iFlow session: {session_id}, model: {model}")
            return self._sessions[session_id]

    async def close_session(self, session_id: str) -> None:
        """
        关闭会话

        Args:
            session_id: 会话 ID
        """
        async with self._lock:
            if session_id in self._sessions:
                await self._sessions[session_id].close()
                del self._sessions[session_id]
                logger.info(f"Closed iFlow session: {session_id}")

    async def close_all(self) -> None:
        """关闭所有会话"""
        async with self._lock:
            for session_id, session in self._sessions.items():
                await session.close()
            self._sessions.clear()
            logger.info("Closed all iFlow sessions")


# 全局 iFlow 管理器实例
iflow_manager = IFlowManager()