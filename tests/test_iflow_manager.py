"""
iflow_manager.py 单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from iflow_manager import IFlowSession, IFlowManager


@pytest.fixture
def iflow_manager():
    """
    创建 iFlow 管理器实例
    """
    # 清理之前的状态
    IFlowManager._instance = None
    IFlowManager._sessions = {}
    return IFlowManager()


@pytest.fixture
def iflow_session():
    """
    创建 iFlow 会话实例
    """
    return IFlowSession(
        session_id="test-123",
        working_dir="F:\\test\\workspace",
        model="glm-4.7"
    )


class TestIFlowSession:
    """IFlowSession 类测试"""

    def test_session_initialization(self):
        """测试会话初始化"""
        session = IFlowSession(
            session_id="test-123",
            working_dir="F:\\test\\workspace",
            model="glm-4.7"
        )

        assert session.session_id == "test-123"
        assert session.working_dir == "F:\\test\\workspace"
        assert session.model == "glm-4.7"
        assert session._client is None
        assert session._lock is not None

    def test_session_default_model(self):
        """测试会话默认模型"""
        session = IFlowSession(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        assert session.model is not None

    @pytest.mark.asyncio
    @patch('iflow_manager.os.path.isdir')
    @patch('iflow_manager.os.path.exists')
    @patch('iflow_manager.os.path.abspath')
    @patch('iflow_manager.IFlowClient')
    async def test_initialize(self, mock_client_class, mock_abspath, mock_exists, mock_isdir):
        """测试初始化 iFlow 客户端"""
        mock_abspath.return_value = "F:\\test\\workspace"
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value = mock_client

        session = IFlowSession(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        await session.initialize()

        mock_abspath.assert_called_once_with("F:\\test\\workspace")
        mock_exists.assert_called_once()
        mock_isdir.assert_called_once()
        mock_client_class.assert_called_once()
        assert session._client is not None

    @pytest.mark.asyncio
    @patch('iflow_manager.os.path.isdir')
    @patch('iflow_manager.os.path.exists')
    @patch('iflow_manager.IFlowClient')
    async def test_send_message(self, mock_client_class, mock_exists, mock_isdir):
        """测试发送消息"""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.send_message = AsyncMock()
        mock_client.receive_messages = self._mock_receive_messages()
        mock_client_class.return_value = mock_client

        session = IFlowSession(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        await session.initialize()

        responses = []
        async for response in session.send_message("Hello, iFlow!"):
            responses.append(response)

        mock_client.send_message.assert_called_once_with("Hello, iFlow!")
        assert len(responses) > 0

    def _mock_receive_messages(self):
        """模拟接收消息"""
        async def generator():
            from iflow_sdk.types import AssistantMessage, TaskFinishMessage

            # 创建模拟的 AssistantMessage
            mock_chunk = Mock()
            mock_chunk.text = "Hello! How can I help you?"

            yield AssistantMessage(
                chunk=mock_chunk,
                agent_id="agent-123",
                agent_info=Mock(
                    agent_id="agent-123",
                    task_id="task-456",
                    agent_index=0
                )
            )

            # 创建模拟的 TaskFinishMessage
            yield TaskFinishMessage(stop_reason="completed")

        return generator

    @pytest.mark.asyncio
    @patch('iflow_manager.IFlowClient')
    async def test_close(self, mock_client_class):
        """测试关闭会话"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client_class.return_value = mock_client

        session = IFlowSession(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        # 手动设置客户端
        session._client = mock_client

        await session.close()

        mock_client.__aexit__.assert_called_once()
        assert session._client is None


class TestIFlowManager:
    """IFlowManager 类测试"""

    def test_singleton_pattern(self, iflow_manager):
        """测试单例模式"""
        manager1 = IFlowManager()
        manager2 = IFlowManager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    @patch('iflow_manager.IFlowSession')
    async def test_get_or_create_session(self, mock_session_class, iflow_manager):
        """测试获取或创建会话"""
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        session = await iflow_manager.get_or_create_session(
            session_id="test-123",
            working_dir="F:\\test\\workspace",
            model="glm-4.7"
        )

        mock_session_class.assert_called_once_with("test-123", "F:\\test\\workspace", "glm-4.7")
        assert session is not None

    @pytest.mark.asyncio
    @patch('iflow_manager.IFlowSession')
    async def test_get_existing_session(self, mock_session_class, iflow_manager):
        """测试获取已存在的会话"""
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        # 第一次创建
        session1 = await iflow_manager.get_or_create_session(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        # 第二次获取（应该返回同一个实例）
        session2 = await iflow_manager.get_or_create_session(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        assert session1 is session2
        mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    @patch('iflow_manager.IFlowSession')
    async def test_close_session(self, mock_session_class, iflow_manager):
        """测试关闭会话"""
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        # 创建会话
        await iflow_manager.get_or_create_session(
            session_id="test-123",
            working_dir="F:\\test\\workspace"
        )

        # 关闭会话
        await iflow_manager.close_session("test-123")

        mock_session.close.assert_called_once()
        assert "test-123" not in iflow_manager._sessions

    @pytest.mark.asyncio
    @patch('iflow_manager.IFlowSession')
    async def test_close_all_sessions(self, mock_session_class, iflow_manager):
        """测试关闭所有会话"""
        mock_session = AsyncMock()
        mock_session_class.return_value = mock_session

        # 创建多个会话
        await iflow_manager.get_or_create_session("test-1", "F:\\test\\workspace1")
        await iflow_manager.get_or_create_session("test-2", "F:\\test\\workspace2")

        # 关闭所有会话
        await iflow_manager.close_all()

        assert len(iflow_manager._sessions) == 0