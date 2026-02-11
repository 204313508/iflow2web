"""
会话管理模块
管理多个 iFlow 会话和对应的工作目录
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Optional
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class Session:
    """会话类"""

    def __init__(self, session_id: str, title: str, working_dir: str, model: str = None):
        self.session_id = session_id
        self.title = title
        self.working_dir = working_dir
        self.model = model or config.IFLOW_DEFAULT_MODEL
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "working_dir": self.working_dir,
            "model": self.model,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
        }


class SessionManager:
    """会话管理器 - 单例模式"""

    _instance: Optional["SessionManager"] = None
    _sessions: Dict[str, Session] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_session(self, title: str, working_dir: str, model: str = None) -> Session:
        """
        创建新会话

        Args:
            title: 会话标题
            working_dir: 工作目录
            model: 模型名称（可选，默认使用配置的默认模型）

        Returns:
            Session: 新创建的会话
        """
        # 验证工作目录
        if not self._validate_working_dir(working_dir):
            raise ValueError(f"Working directory not allowed: {working_dir}")

        # 验证模型
        if model and model not in config.IFLOW_AVAILABLE_MODELS:
            raise ValueError(f"Model not available: {model}")

        session_id = str(uuid.uuid4())
        session = Session(session_id, title, working_dir, model)
        self._sessions[session_id] = session

        logger.info(f"Created session: {session_id} with working dir: {working_dir}, model: {model}")
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            Optional[Session]: 会话对象，如果不存在则返回 None
        """
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        """
        列出所有会话

        Returns:
            list[dict]: 会话列表
        """
        return [session.to_dict() for session in self._sessions.values()]

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否删除成功
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def update_activity(self, session_id: str) -> None:
        """
        更新会话活动时间

        Args:
            session_id: 会话 ID
        """
        session = self.get_session(session_id)
        if session:
            session.last_activity = datetime.now()

    def _validate_working_dir(self, working_dir: str) -> bool:
        """
        验证工作目录是否在允许的列表中

        Args:
            working_dir: 工作目录路径

        Returns:
            bool: 是否允许
        """
        # 如果没有配置白名单，允许所有目录
        if config.ALLOWED_WORKING_DIRS is None:
            return True

        # 检查是否在白名单中
        normalized_dir = working_dir.replace("/", "\\")
        for allowed_dir in config.ALLOWED_WORKING_DIRS:
            normalized_allowed = allowed_dir.replace("/", "\\")
            if normalized_dir == normalized_allowed or normalized_dir.startswith(normalized_allowed + "\\"):
                return True

        return False


# 全局会话管理器实例
session_manager = SessionManager()