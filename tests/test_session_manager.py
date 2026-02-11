"""
session_manager.py 单元测试
"""

import pytest
from session_manager import Session, SessionManager
import config


@pytest.fixture
def session_manager():
    """
    创建会话管理器实例
    """
    # 清理之前的状态
    SessionManager._instance = None
    SessionManager._sessions = {}
    return SessionManager()


@pytest.fixture
def sample_session():
    """
    创建示例会话
    """
    return Session(
        session_id="test-123",
        title="Test Session",
        working_dir="F:\\test\\workspace",
        model="glm-4.7"
    )


class TestSession:
    """Session 类测试"""

    def test_session_initialization(self):
        """测试会话初始化"""
        session = Session(
            session_id="test-123",
            title="Test Session",
            working_dir="F:\\test\\workspace",
            model="glm-4.7"
        )

        assert session.session_id == "test-123"
        assert session.title == "Test Session"
        assert session.working_dir == "F:\\test\\workspace"
        assert session.model == "glm-4.7"

    def test_session_default_model(self):
        """测试会话默认模型"""
        session = Session(
            session_id="test-123",
            title="Test Session",
            working_dir="F:\\test\\workspace"
        )

        assert session.model == config.IFLOW_DEFAULT_MODEL

    def test_session_to_dict(self):
        """测试会话转换为字典"""
        session = Session(
            session_id="test-123",
            title="Test Session",
            working_dir="F:\\test\\workspace",
            model="glm-4.7"
        )

        session_dict = session.to_dict()

        assert session_dict["session_id"] == "test-123"
        assert session_dict["title"] == "Test Session"
        assert session_dict["working_dir"] == "F:\\test\\workspace"
        assert session_dict["model"] == "glm-4.7"
        assert "created_at" in session_dict
        assert "last_activity" in session_dict


class TestSessionManager:
    """SessionManager 类测试"""

    def test_singleton_pattern(self, session_manager):
        """测试单例模式"""
        manager1 = SessionManager()
        manager2 = SessionManager()

        assert manager1 is manager2

    def test_create_session(self, session_manager, temp_working_dir):
        """测试创建会话"""
        session = session_manager.create_session(
            title="Test Session",
            working_dir=temp_working_dir,
            model="glm-4.7"
        )

        assert session.title == "Test Session"
        assert session.working_dir == temp_working_dir
        assert session.model == "glm-4.7"
        assert session.session_id in session_manager._sessions

    def test_create_session_default_model(self, session_manager, temp_working_dir):
        """测试创建会话使用默认模型"""
        session = session_manager.create_session(
            title="Test Session",
            working_dir=temp_working_dir
        )

        assert session.model == config.IFLOW_DEFAULT_MODEL

    def test_create_session_invalid_model(self, session_manager, temp_working_dir):
        """测试创建会话使用无效模型"""
        with pytest.raises(ValueError, match="Model not available"):
            session_manager.create_session(
                title="Test Session",
                working_dir=temp_working_dir,
                model="invalid-model"
            )

    def test_create_session_invalid_directory(self, session_manager):
        """测试创建会话使用无效目录（如果配置了白名单）"""
        # 由于当前配置允许所有目录，这个测试主要用于验证白名单功能
        # 如果将来配置了白名单，这个测试会变得有用
        session = session_manager.create_session(
            title="Test Session",
            working_dir="F:\\invalid\\path"
        )

        assert session is not None

    def test_get_session(self, session_manager, temp_working_dir):
        """测试获取会话"""
        session = session_manager.create_session(
            title="Test Session",
            working_dir=temp_working_dir
        )

        retrieved_session = session_manager.get_session(session.session_id)

        assert retrieved_session is not None
        assert retrieved_session.session_id == session.session_id

    def test_get_nonexistent_session(self, session_manager):
        """测试获取不存在的会话"""
        session = session_manager.get_session("nonexistent-id")

        assert session is None

    def test_list_sessions(self, session_manager, temp_working_dir):
        """测试列出所有会话"""
        session1 = session_manager.create_session(
            title="Session 1",
            working_dir=temp_working_dir
        )
        session2 = session_manager.create_session(
            title="Session 2",
            working_dir=temp_working_dir
        )

        sessions = session_manager.list_sessions()

        assert len(sessions) == 2
        assert sessions[0]["title"] == "Session 1"
        assert sessions[1]["title"] == "Session 2"

    def test_delete_session(self, session_manager, temp_working_dir):
        """测试删除会话"""
        session = session_manager.create_session(
            title="Test Session",
            working_dir=temp_working_dir
        )

        result = session_manager.delete_session(session.session_id)

        assert result is True
        assert session.session_id not in session_manager._sessions

    def test_delete_nonexistent_session(self, session_manager):
        """测试删除不存在的会话"""
        result = session_manager.delete_session("nonexistent-id")

        assert result is False

    def test_update_activity(self, session_manager, temp_working_dir):
        """测试更新会话活动时间"""
        session = session_manager.create_session(
            title="Test Session",
            working_dir=temp_working_dir
        )

        old_activity = session.last_activity

        # 等待一小段时间
        import time
        time.sleep(0.01)

        session_manager.update_activity(session.session_id)

        assert session.last_activity > old_activity

    def test_validate_working_dir_no_whitelist(self, session_manager):
        """测试验证工作目录（无白名单）"""
        # 当前配置允许所有目录
        assert session_manager._validate_working_dir("F:\\any\\path") is True
        assert session_manager._validate_working_dir("C:\\another\\path") is True