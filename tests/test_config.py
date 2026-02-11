"""
config.py 单元测试
"""

import pytest
import config


class TestConfig:
    """配置测试类"""

    def test_server_host_exists(self):
        """测试服务器主机配置存在"""
        assert hasattr(config, 'SERVER_HOST')
        assert config.SERVER_HOST == "0.0.0.0"

    def test_server_port_exists(self):
        """测试服务器端口配置存在"""
        assert hasattr(config, 'SERVER_PORT')
        assert config.SERVER_PORT == 8000

    def test_ws_max_connections_exists(self):
        """测试 WebSocket 最大连接数配置存在"""
        assert hasattr(config, 'WS_MAX_CONNECTIONS')
        assert config.WS_MAX_CONNECTIONS == 10

    def test_iflow_default_working_dir_exists(self):
        """测试 iFlow 默认工作目录配置存在"""
        assert hasattr(config, 'IFLOW_DEFAULT_WORKING_DIR')
        assert isinstance(config.IFLOW_DEFAULT_WORKING_DIR, str)

    def test_iflow_approval_mode_exists(self):
        """测试 iFlow 审批模式配置存在"""
        assert hasattr(config, 'IFLOW_APPROVAL_MODE')
        assert config.IFLOW_APPROVAL_MODE in ["DEFAULT", "AUTO_EDIT", "YOLO", "PLAN"]

    def test_iflow_default_model_exists(self):
        """测试 iFlow 默认模型配置存在"""
        assert hasattr(config, 'IFLOW_DEFAULT_MODEL')
        assert config.IFLOW_DEFAULT_MODEL == "glm-4.7"

    def test_iflow_available_models_exists(self):
        """测试 iFlow 可用模型列表配置存在"""
        assert hasattr(config, 'IFLOW_AVAILABLE_MODELS')
        assert isinstance(config.IFLOW_AVAILABLE_MODELS, list)
        assert len(config.IFLOW_AVAILABLE_MODELS) > 0
        assert config.IFLOW_DEFAULT_MODEL in config.IFLOW_AVAILABLE_MODELS

    def test_allowed_working_dirs_is_none(self):
        """测试允许的工作目录白名单为 None（个人使用）"""
        assert hasattr(config, 'ALLOWED_WORKING_DIRS')
        assert config.ALLOWED_WORKING_DIRS is None

    def test_terminal_theme_exists(self):
        """测试终端主题配置存在"""
        assert hasattr(config, 'TERMINAL_THEME')
        assert config.TERMINAL_THEME == "dark"

    def test_log_level_exists(self):
        """测试日志级别配置存在"""
        assert hasattr(config, 'LOG_LEVEL')
        assert config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_terminal_font_family_exists(self):
        """测试终端字体配置存在"""
        assert hasattr(config, 'TERMINAL_FONT_FAMILY')
        assert isinstance(config.TERMINAL_FONT_FAMILY, str)

    def test_terminal_font_size_exists(self):
        """测试终端字体大小配置存在"""
        assert hasattr(config, 'TERMINAL_FONT_SIZE')
        assert isinstance(config.TERMINAL_FONT_SIZE, str)