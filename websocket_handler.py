"""
WebSocket 消息处理模块
处理前端与后端的 WebSocket 通信
"""

import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from iflow_manager import iflow_manager
from session_manager import session_manager
import logging
import config

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.connection_sessions: dict[WebSocket, str] = {}  # WebSocket -> session_id

    async def connect(self, websocket: WebSocket, session_id: str) -> None:
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_sessions[websocket] = session_id
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """断开 WebSocket 连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_sessions:
            session_id = self.connection_sessions[websocket]
            del self.connection_sessions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    def get_session_id(self, websocket: WebSocket) -> str:
        """获取 WebSocket 对应的会话 ID"""
        return self.connection_sessions.get(websocket)

    async def send_message(self, websocket: WebSocket, message: dict) -> None:
        """发送消息给指定的 WebSocket"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)


# 全局连接管理器
manager = ConnectionManager()


async def handle_websocket(websocket: WebSocket) -> None:
    """
    处理 WebSocket 连接和消息

    Args:
        websocket: WebSocket 连接对象
    """
    # 先接受 WebSocket 连接
    await websocket.accept()
    logger.info("WebSocket connection accepted, waiting for session_id...")

    session_id = None
    is_processing = False

    async def send_message_safe(message: dict) -> bool:
        """安全地发送消息，检查连接状态"""
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    try:
        # 等待客户端发送 session_id
        init_message = await websocket.receive_text()
        init_data = json.loads(init_message)

        session_id = init_data.get("session_id")

        if not session_id:
            await send_message_safe({"type": "error", "content": "Session ID is required"})
            return

        # 获取会话信息
        session = session_manager.get_session(session_id)
        if not session:
            await send_message_safe({"type": "error", "content": "Session not found"})
            return

        # 注册连接到管理器
        manager.active_connections.append(websocket)
        manager.connection_sessions[websocket] = session_id
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {len(manager.active_connections)}")

        # 发送pong响应
        await send_message_safe({"type": "pong"})

        # 处理消息循环
        while True:
            try:
                # 接收客户端消息
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message_data = json.loads(data)

                message_type = message_data.get("type")
                message_content = message_data.get("content", "")

                if message_type == "user_message":
                    if is_processing:
                        await send_message_safe({"type": "error", "content": "正在处理中，请稍候..."})
                        continue

                    # 处理用户消息
                    logger.info(f"Received user message from session {session_id}: {message_content}")
                    is_processing = True

                    # 更新会话活动时间
                    session_manager.update_activity(session_id)

                    # 发送用户消息回显
                    if not await send_message_safe({
                        "type": "user",
                        "content": message_content,
                    }):
                        break

                    # 获取或创建 iFlow 会话（传递模型参数）
                    iflow_session = await iflow_manager.get_or_create_session(session_id, session.working_dir, session.model)

                    # 发送给 iFlow 并处理响应
                    try:
                        async for response in iflow_session.send_message(message_content):
                            if not await send_message_safe(response):
                                logger.warning("WebSocket disconnected during message processing")
                                break
                    except asyncio.CancelledError:
                        logger.info("Message processing cancelled")
                        break
                    except Exception as e:
                        logger.error(f"Error processing iFlow message: {e}", exc_info=True)
                        await send_message_safe({
                            "type": "error",
                            "content": f"Error: {str(e)}",
                        })
                    finally:
                        is_processing = False

                elif message_type == "ping":
                    # 心跳检测
                    await send_message_safe({"type": "pong"})

            except asyncio.TimeoutError:
                logger.warning("WebSocket receive timeout, sending keepalive")
                await send_message_safe({"type": "pong"})
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
            except Exception as e:
                logger.error(f"Error receiving message: {e}")
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
    finally:
        is_processing = False
        if websocket in manager.active_connections:
            manager.active_connections.remove(websocket)
        if websocket in manager.connection_sessions:
            del manager.connection_sessions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(manager.active_connections)}")