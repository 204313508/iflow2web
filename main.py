"""
iflow2web 主服务器
FastAPI + WebSocket 实现 iFlow CLI 的 Web 界面
"""

import os
import uvicorn
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import logging
import config
import websocket_handler
from session_manager import session_manager
from iflow_manager import iflow_manager

# 配置日志
logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用
app = FastAPI(title="iflow2web", description="iFlow CLI Web Interface")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="templates")


# 请求模型
class CreateSessionRequest(BaseModel):
    title: str
    working_dir: str
    model: str = None


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    主页 - 返回终端界面
    """
    # 如果配置的默认工作目录为空，使用当前目录
    default_working_dir = config.IFLOW_DEFAULT_WORKING_DIR if config.IFLOW_DEFAULT_WORKING_DIR else os.getcwd()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "server_host": config.SERVER_HOST,
            "server_port": config.SERVER_PORT,
            "terminal_theme": config.TERMINAL_THEME,
            "terminal_font_family": config.TERMINAL_FONT_FAMILY,
            "terminal_font_size": config.TERMINAL_FONT_SIZE,
            "default_working_dir": default_working_dir,
        }
    )


@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {"status": "healthy", "service": "iflow2web"}


@app.get("/api/models")
async def get_models():
    """
    获取可用的模型列表（从API动态获取）
    """
    return await iflow_manager.get_available_models()


@app.get("/api/sessions")
async def list_sessions():
    """
    列出所有会话
    """
    sessions = session_manager.list_sessions()
    return {"sessions": sessions}


@app.post("/api/sessions")
async def create_session(request: CreateSessionRequest):
    """
    创建新会话
    """
    try:
        session = session_manager.create_session(request.title, request.working_dir, request.model)
        return session.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取会话详情
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除会话
    """
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点 - 处理实时通信
    """
    await websocket_handler.handle_websocket(websocket)


def main():
    """
    启动服务器
    """
    import sys

    # 从命令行参数获取端口号
    port = config.SERVER_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except ValueError as e:
            logger.error(f"Invalid port number: {e}")
            logger.info(f"Using default port: {config.SERVER_PORT}")
            port = config.SERVER_PORT

    logger.info(f"Starting iflow2web server on {config.SERVER_HOST}:{port}")
    logger.info(f"Terminal theme: {config.TERMINAL_THEME}")
    logger.info(f"Access the interface at: http://{config.SERVER_HOST}:{port}")

    uvicorn.run(
        "main:app",
        host=config.SERVER_HOST,
        port=port,
        reload=False,
        log_level=config.LOG_LEVEL.lower(),
    )


if __name__ == "__main__":
    main()