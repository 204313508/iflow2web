"""
websocket_handler.py 单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from websocket_handler import ConnectionManager
from fastapi import WebSocket
import asyncio


@pytest.fixture
def connection_manager():
    """
    创建连接管理器实例
    """
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """
    创建模拟的 WebSocket
    """
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


class TestConnectionManager:
    """ConnectionManager 类测试"""

    @pytest.mark.asyncio
    async def test_connect(self, connection_manager, mock_websocket):
        """测试连接 WebSocket"""
        await connection_manager.connect(mock_websocket, "test-session-123")

        mock_websocket.accept.assert_called_once()
        assert mock_websocket in connection_manager.active_connections
        assert connection_manager.connection_sessions.get(mock_websocket) == "test-session-123"
        assert len(connection_manager.active_connections) == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, connection_manager, mock_websocket):
        """测试断开 WebSocket"""
        # 先连接
        await connection_manager.connect(mock_websocket, "test-session-123")

        # 再断开
        connection_manager.disconnect(mock_websocket)

        assert mock_websocket not in connection_manager.active_connections
        assert mock_websocket not in connection_manager.connection_sessions
        assert len(connection_manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_send_message(self, connection_manager, mock_websocket):
        """测试发送消息"""
        await connection_manager.connect(mock_websocket, "test-session-123")

        message = {"type": "test", "content": "Hello"}
        await connection_manager.send_message(mock_websocket, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_message_error(self, connection_manager, mock_websocket):
        """测试发送消息时出错"""
        await connection_manager.connect(mock_websocket, "test-session-123")

        # 模拟发送消息时出错
        mock_websocket.send_json.side_effect = Exception("Connection error")

        message = {"type": "test", "content": "Hello"}
        await connection_manager.send_message(mock_websocket, message)

        # 连接应该被移除
        assert mock_websocket not in connection_manager.active_connections
        assert mock_websocket not in connection_manager.connection_sessions

    def test_get_session_id(self, connection_manager, mock_websocket):
        """测试获取会话 ID"""
        connection_manager.connection_sessions[mock_websocket] = "test-session-123"

        session_id = connection_manager.get_session_id(mock_websocket)

        assert session_id == "test-session-123"


@pytest.mark.skip(reason="WebSocket 集成测试需要更复杂的设置")
class TestHandleWebsocket:
    """handle_websocket 函数测试"""

    @pytest.mark.asyncio
    @patch('websocket_handler.session_manager')
    @patch('websocket_handler.iflow_manager')
    async def test_handle_websocket_user_message(self, mock_iflow_manager, mock_session_manager, mock_websocket):
        """测试处理用户消息"""
        # 设置模拟
        mock_session = Mock()
        mock_session.working_dir = "F:\\test\\workspace"
        mock_session_manager.get_session.return_value = mock_session

        mock_iflow_session = AsyncMock()
        mock_iflow_session.send_message = self._mock_send_message()
        mock_iflow_manager.get_or_create_session = AsyncMock(return_value=mock_iflow_session)

        mock_websocket.receive_text.side_effect = [
            '{"session_id": "test-123"}',
            '{"type": "user_message", "content": "Hello"}',
        ]

        # 调用处理函数
        from websocket_handler import handle_websocket
        await handle_websocket(mock_websocket)

        # 验证调用
        mock_session_manager.get_session.assert_called_once_with("test-123")
        mock_iflow_manager.get_or_create_session.assert_called_once()

    @pytest.mark.asyncio
    @patch('websocket_handler.session_manager')
    async def test_handle_websocket_invalid_session(self, mock_session_manager, mock_websocket):
        """测试处理无效会话"""
        # 设置模拟
        mock_session_manager.get_session.return_value = None

        mock_websocket.receive_text.return_value = '{"session_id": "invalid-id"}'

        # 调用处理函数
        from websocket_handler import handle_websocket
        await handle_websocket(mock_websocket)

        # 验证发送错误消息
        mock_websocket.send_json.assert_called_once()
        error_message = mock_websocket.send_json.call_args[0][0]
        assert error_message["type"] == "error"

    @pytest.mark.asyncio
    @patch('websocket_handler.session_manager')
    async def test_handle_websocket_ping(self, mock_session_manager, mock_websocket):
        """测试处理心跳消息"""
        # 设置模拟
        mock_session = Mock()
        mock_session.working_dir = "F:\\test\\workspace"
        mock_session_manager.get_session.return_value = mock_session

        mock_websocket.receive_text.side_effect = [
            '{"session_id": "test-123"}',
            '{"type": "ping"}',
        ]

        # 调用处理函数
        from websocket_handler import handle_websocket
        await handle_websocket(mock_websocket)

        # 验证发送 pong 响应
        mock_websocket.send_json.assert_called_with({"type": "pong"})

    def _mock_send_message(self):
        """模拟发送消息生成器"""
        async def generator(message):
            # 模拟用户消息回显
            yield {"type": "user", "content": message}
            # 模拟 AI 回复
            yield {"type": "assistant", "content": "Hello!", "is_stream": True}
            # 模拟任务完成
            yield {"type": "finish", "content": "Task finished", "is_stream": False}

        return generator