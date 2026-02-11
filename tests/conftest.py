"""
pytest 配置文件
提供共享的 fixtures
"""

import pytest
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_working_dir(tmp_path):
    """
    创建临时工作目录
    """
    working_dir = tmp_path / "workspace"
    working_dir.mkdir()
    return str(working_dir)


@pytest.fixture
def sample_session_data():
    """
    提供示例会话数据
    """
    return {
        "session_id": "test-session-123",
        "title": "Test Session",
        "working_dir": "F:\\test\\workspace",
        "model": "glm-4.7",
    }


@pytest.fixture
def sample_message_data():
    """
    提供示例消息数据
    """
    return {
        "type": "user_message",
        "content": "Hello, iFlow!",
    }