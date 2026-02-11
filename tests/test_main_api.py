"""
main.py API 集成测试
"""

import pytest
from fastapi.testclient import TestClient
import tempfile
import os

# 导入应用前需要清理单例
from session_manager import SessionManager
from iflow_manager import IFlowManager

SessionManager._instance = None
SessionManager._sessions = {}
IFlowManager._instance = None
IFlowManager._sessions = {}

from main import app


@pytest.fixture
def client():
    """
    创建测试客户端
    """
    # 清理单例状态
    SessionManager._instance = None
    SessionManager._sessions = {}
    IFlowManager._instance = None
    IFlowManager._sessions = {}

    return TestClient(app)


@pytest.fixture
def temp_working_dir():
    """
    创建临时工作目录
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestHealthEndpoint:
    """健康检查端点测试"""

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "iflow2web"


class TestModelsEndpoint:
    """模型端点测试"""

    def test_get_models(self, client):
        """测试获取模型列表"""
        response = client.get("/api/models")

        assert response.status_code == 200
        data = response.json()
        assert "default_model" in data
        assert "available_models" in data
        assert isinstance(data["available_models"], list)
        assert len(data["available_models"]) > 0


class TestSessionsEndpoints:
    """会话端点测试"""

    def test_list_sessions_empty(self, client):
        """测试列出空会话列表"""
        response = client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)
        assert len(data["sessions"]) == 0

    def test_create_session(self, client, temp_working_dir):
        """测试创建会话"""
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir,
            "model": "glm-4.7"
        }

        response = client.post("/api/sessions", json=session_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Session"
        assert data["working_dir"] == temp_working_dir
        assert data["model"] == "glm-4.7"
        assert "session_id" in data
        assert "created_at" in data

    def test_create_session_default_model(self, client, temp_working_dir):
        """测试创建会话使用默认模型"""
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir
        }

        response = client.post("/api/sessions", json=session_data)

        assert response.status_code == 200
        data = response.json()
        assert data["model"] is not None

    def test_create_session_invalid_model(self, client, temp_working_dir):
        """测试创建会话使用无效模型"""
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir,
            "model": "invalid-model"
        }

        response = client.post("/api/sessions", json=session_data)

        assert response.status_code == 400

    def test_list_sessions(self, client, temp_working_dir):
        """测试列出会话"""
        # 创建会话
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir
        }
        client.post("/api/sessions", json=session_data)

        # 列出会话
        response = client.get("/api/sessions")

        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 1
        assert data["sessions"][0]["title"] == "Test Session"

    def test_get_session(self, client, temp_working_dir):
        """测试获取会话详情"""
        # 创建会话
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir
        }
        create_response = client.post("/api/sessions", json=session_data)
        session_id = create_response.json()["session_id"]

        # 获取会话详情
        response = client.get(f"/api/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["title"] == "Test Session"

    def test_get_nonexistent_session(self, client):
        """测试获取不存在的会话"""
        response = client.get("/api/sessions/nonexistent-id")

        assert response.status_code == 404

    def test_delete_session(self, client, temp_working_dir):
        """测试删除会话"""
        # 创建会话
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir
        }
        create_response = client.post("/api/sessions", json=session_data)
        session_id = create_response.json()["session_id"]

        # 删除会话
        response = client.delete(f"/api/sessions/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Session deleted"

        # 验证会话已删除
        get_response = client.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_session(self, client):
        """测试删除不存在的会话"""
        response = client.delete("/api/sessions/nonexistent-id")

        assert response.status_code == 404


class TestRootEndpoint:
    """根端点测试"""

    def test_root_endpoint(self, client):
        """测试根端点返回 HTML"""
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")


@pytest.mark.integration
class TestWebsocketEndpoint:
    """WebSocket 端点集成测试"""

    @pytest.mark.skip(reason="WebSocket 集成测试需要更复杂的设置")
    def test_websocket_connection(self, client, temp_working_dir):
        """测试 WebSocket 连接"""
        # 首先创建会话
        session_data = {
            "title": "Test Session",
            "working_dir": temp_working_dir
        }
        create_response = client.post("/api/sessions", json=session_data)
        session_id = create_response.json()["session_id"]

        # 测试 WebSocket 连接
        # 注意：TestClient 对 WebSocket 的支持有限
        # 完整的 WebSocket 测试需要使用其他工具
        pass