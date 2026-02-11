// iflow2web 终端逻辑

class Terminal {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000;
        this.currentAssistantMessage = null;
        this.isConnected = false;
        this.isProcessing = false;
        this.currentSessionId = null;
        this.sessions = [];
        this.messageQueue = []; // 消息队列
        this.pendingMessages = new Map(); // 待确认的消息

        this.init();
    }

    init() {
        this.setupDOM();
        this.setupEventListeners();
        this.loadModels();
        this.loadSessions();
    }

    setupDOM() {
        this.terminalContainer = document.querySelector('.terminal-container');
        this.terminalContent = document.querySelector('.terminal-content');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.statusIndicator = document.querySelector('.status-indicator');
        this.sessionsList = document.querySelector('.sessions-list');
        this.newSessionBtn = document.getElementById('new-session-btn');
        this.modal = document.getElementById('session-modal');
        this.modalTitleInput = document.getElementById('session-title');
        this.modalWorkingDirInput = document.getElementById('session-working-dir');
        this.modalModelSelect = document.getElementById('session-model');
        this.modalCancelBtn = document.getElementById('modal-cancel');
        this.modalCreateBtn = document.getElementById('modal-create');
        this.showDetailsToggle = document.getElementById('show-details-toggle');
        this.showDetails = true; // 默认显示详细信息
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.sidebar = document.querySelector('.sidebar');
        this.sidebarOverlay = document.getElementById('sidebar-overlay');
    }

    setupEventListeners() {
        // 发送按钮点击
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // 输入框回车发送
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 新建会话按钮
        this.newSessionBtn.addEventListener('click', () => this.showNewSessionModal());

        // 模态框按钮
        this.modalCancelBtn.addEventListener('click', () => this.hideNewSessionModal());
        this.modalCreateBtn.addEventListener('click', () => this.createNewSession());

        // 点击模态框背景关闭
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hideNewSessionModal();
            }
        });

        // 移动端侧边栏切换
        this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        this.sidebarOverlay.addEventListener('click', () => this.closeSidebar());

        // 页面关闭时断开连接
        window.addEventListener('beforeunload', () => {
            if (this.ws) {
                this.ws.close();
            }
        });

        // 自动滚动到底部
        this.terminalContainer.addEventListener('DOMNodeInserted', () => {
            this.scrollToBottom();
        });
    }

    async loadModels() {
        try {
            const response = await fetch('/api/models');
            const data = await response.json();
            this.models = data.available_models;
            this.defaultModel = data.default_model;
            this.renderModelOptions();
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }

    renderModelOptions() {
        this.modalModelSelect.innerHTML = '<option value="" disabled selected>选择模型</option>';
        this.models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            if (model === this.defaultModel) {
                option.selected = true;
            }
            this.modalModelSelect.appendChild(option);
        });
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            const data = await response.json();
            this.sessions = data.sessions;
            this.renderSessions();

            // 如果没有会话，创建默认会话
            if (this.sessions.length === 0) {
                const defaultDir = document.querySelector('[data-default-working-dir]')?.dataset.defaultWorkingDir || '.';
                await this.createSession('Default Session', defaultDir);
            } else {
                // 自动选择第一个会话
                this.selectSession(this.sessions[0].session_id);
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    renderSessions() {
        this.sessionsList.innerHTML = '';
        this.sessions.forEach(session => {
            const sessionElement = document.createElement('div');
            sessionElement.className = `session-item ${session.session_id === this.currentSessionId ? 'active' : ''}`;
            sessionElement.dataset.sessionId = session.session_id;
            sessionElement.innerHTML = `
                <div class="session-title">${this.escapeHtml(session.title)}</div>
                <div class="session-info">${this.escapeHtml(session.working_dir)}</div>
                <div class="session-info">模型: ${this.escapeHtml(session.model)}</div>
                <div class="session-actions">
                    <button class="session-delete-btn" data-action="delete">删除</button>
                </div>
            `;

            sessionElement.addEventListener('click', (e) => {
                if (!e.target.classList.contains('session-delete-btn')) {
                    this.selectSession(session.session_id);
                }
            });

            sessionElement.querySelector('.session-delete-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(session.session_id);
            });

            this.sessionsList.appendChild(sessionElement);
        });
    }

    selectSession(sessionId) {
        this.currentSessionId = sessionId;
        this.renderSessions();
        this.connect();
    }

    async createSession(title, workingDir) {
        try {
            const model = this.modalModelSelect.value || this.defaultModel;
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title, working_dir: workingDir, model }),
            });
            const session = await response.json();
            this.sessions.push(session);
            this.renderSessions();
            this.selectSession(session.session_id);
            this.hideNewSessionModal();
        } catch (error) {
            console.error('Failed to create session:', error);
            alert('Failed to create session');
        }
    }

    async deleteSession(sessionId) {
        if (!confirm('确定要删除这个会话吗？')) {
            return;
        }

        try {
            await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
            this.sessions = this.sessions.filter(s => s.session_id !== sessionId);
            this.renderSessions();

            if (this.currentSessionId === sessionId) {
                if (this.sessions.length > 0) {
                    this.selectSession(this.sessions[0].session_id);
                } else {
                    this.currentSessionId = null;
                    if (this.ws) {
                        this.ws.close();
                    }
                    this.terminalContent.innerHTML = '';
                }
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
            alert('Failed to delete session');
        }
    }

    showNewSessionModal() {
        this.modal.classList.add('show');
        this.modalTitleInput.value = '';
        this.modalWorkingDirInput.value = document.querySelector('[data-default-working-dir]')?.dataset.defaultWorkingDir || '.';
        if (this.defaultModel) {
            this.modalModelSelect.value = this.defaultModel;
        }
        this.modalTitleInput.focus();
    }

    hideNewSessionModal() {
        this.modal.classList.remove('show');
    }

    createNewSession() {
        const title = this.modalTitleInput.value.trim();
        const workingDir = this.modalWorkingDirInput.value.trim();

        if (!title || !workingDir) {
            alert('请填写会话标题和工作目录');
            return;
        }

        this.createSession(title, workingDir);
    }

    connect() {
        if (!this.currentSessionId) {
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        // 关闭现有连接
        if (this.ws) {
            this.ws.close();
        }

        this.updateConnectionStatus('initializing');
        if (this.terminalContent.innerHTML === '' || this.terminalContent.querySelector('.init-message')) {
            this.terminalContent.innerHTML = '<div class="init-message">正在初始化 CLI 环境，请稍候...</div>';
        }

        try {
            this.ws = new WebSocket(wsUrl);

            // 连接成功后发送会话 ID
            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('connecting');
                if (this.terminalContent.querySelector('.init-message')) {
                    this.terminalContent.innerHTML = '<div class="init-message">正在连接会话，请稍候...</div>';
                }
                this.ws.send(JSON.stringify({ session_id: this.currentSessionId }));
            };

            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'error') {
                    console.error('Session error:', data.content);
                    this.appendMessage(data.content, 'error');
                    // 不更新连接状态，因为可能是临时错误
                    return;
                }

                if (data.type === 'pong') {
                    this.reconnectAttempts = 0;
                    this.updateConnectionStatus('connected');
                    if (this.terminalContent.querySelector('.init-message')) {
                        this.showWelcomeMessage();
                    }
                    return;
                }

                this.handleMessage(data);
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                // 只有在非初始化状态下才显示断开连接
                if (this.ws.readyState !== WebSocket.CONNECTING) {
                    this.updateConnectionStatus('disconnected');
                }
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket closed, code:', event.code, 'reason:', event.reason);
                // 只有在非初始化状态下才显示断开连接
                if (this.ws.readyState !== WebSocket.CONNECTING) {
                    this.updateConnectionStatus('disconnected');
                    this.attemptReconnect();
                }
            };
        } catch (error) {
            console.error('Failed to connect:', error);
            this.updateConnectionStatus('disconnected');
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
            this.appendMessage('Connection failed. Please try again.', 'error');
        }
    }

    handleMessage(data) {
        // 收到任何响应消息时隐藏处理中指示器
        if (data.type !== 'user') {
            this.hideProcessingIndicator();
        }

        switch (data.type) {
            case 'user':
                // 用户消息回显
                break;

            case 'assistant':
                // AI 回复（流式）
                if (data.is_stream && data.content) {
                    this.appendStreamMessage(data.content, 'assistant', data);
                } else if (!data.is_stream && data.content) {
                    this.appendMessage(data.content, 'assistant', data);
                }
                break;

            case 'tool':
                // 工具调用
                this.appendMessage(`${data.tool_name}: ${data.status}`, 'tool', data);
                break;

            case 'plan':
                // 任务计划
                this.appendMessage(data.content, 'plan', data);
                break;

            case 'finish':
                // 任务完成
                this.finalizeStreamMessage();
                this.isProcessing = false;
                this.updateInputState();
                break;

            case 'error':
                // 错误消息
                this.appendMessage(data.content, 'error', data);
                this.isProcessing = false;
                this.updateInputState();
                break;

            default:
                console.warn('Unknown message type:', data.type);
        }
    }

    sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message || !this.currentSessionId) {
            return;
        }

        // 检查连接状态
        if (!this.isConnected) {
            this.appendMessage('正在连接中，请稍候...', 'error');
            return;
        }

        if (this.isProcessing) {
            this.appendMessage('正在处理中，请稍候...', 'error');
            return;
        }

        // 显示用户消息
        this.appendMessage(message, 'user');

        // 保存消息到队列（用于重试）
        const messageId = Date.now().toString();
        this.messageQueue.push({
            id: messageId,
            content: message,
            timestamp: Date.now()
        });

        // 显示处理中指示器
        this.showProcessingIndicator();

        // 发送到服务器
        try {
            this.ws.send(JSON.stringify({
                type: 'user_message',
                content: message
            }));

            // 清空输入框
            this.messageInput.value = '';

            // 标记为处理中
            this.isProcessing = true;
            this.updateInputState();
        } catch (error) {
            console.error('Error sending message:', error);
            this.appendMessage('发送消息失败，请重试', 'error');
            this.hideProcessingIndicator();
            this.isProcessing = false;
            this.updateInputState();
        }
    }

    appendMessage(content, type, details = null) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = content;

        // 添加详细信息
        if (details && this.hasDetails(details)) {
            const detailsElement = this.createDetailsElement(type, details);
            messageElement.appendChild(detailsElement);
        }

        this.terminalContent.appendChild(messageElement);
    }

    appendStreamMessage(content, type, details = null) {
        if (!this.currentAssistantMessage) {
            this.currentAssistantMessage = document.createElement('div');
            this.currentAssistantMessage.className = `message ${type}`;
            this.currentAssistantMessage.textContent = content;

            // 添加详细信息
            if (details && this.hasDetails(details)) {
                this.currentAssistantDetails = this.createDetailsElement(type, details);
                this.currentAssistantMessage.appendChild(this.currentAssistantDetails);
            }

            this.terminalContent.appendChild(this.currentAssistantMessage);
        } else {
            this.currentAssistantMessage.childNodes[0].textContent += content;
        }
    }

    finalizeStreamMessage() {
        this.currentAssistantMessage = null;
    }

    showWelcomeMessage() {
        const session = this.sessions.find(s => s.session_id === this.currentSessionId);
        const welcomeHtml = `
            <div class="welcome-message">
                <h1>CLI Tools Web Interface</h1>
                <p>会话: ${this.escapeHtml(session?.title || 'Unknown')}</p>
                <p>工作目录: ${this.escapeHtml(session?.working_dir || 'Unknown')}</p>
                <p>模型: ${this.escapeHtml(session?.model || 'Unknown')}</p>
                <p>Type your message and press Enter to send</p>
            </div>
        `;
        this.terminalContent.innerHTML = welcomeHtml;
    }

    updateConnectionStatus(status) {
        this.statusIndicator.className = 'status-indicator';

        switch (status) {
            case 'connected':
                this.statusIndicator.classList.add('connected');
                this.isConnected = true;
                break;
            case 'connecting':
                this.statusIndicator.classList.add('connecting');
                this.isConnected = false;
                break;
            case 'initializing':
                this.statusIndicator.classList.add('connecting');
                this.isConnected = false;
                break;
            case 'disconnected':
                this.isConnected = false;
                break;
        }

        this.updateInputState();
    }

    updateInputState() {
        this.messageInput.disabled = !this.isConnected || this.isProcessing;
        this.sendButton.disabled = !this.isConnected || this.isProcessing;

        if (this.isConnected && !this.isProcessing) {
            this.messageInput.focus();
        }
    }

    showProcessingIndicator() {
        // 移除现有的处理中指示器
        this.hideProcessingIndicator();

        // 创建新的处理中指示器
        const indicator = document.createElement('div');
        indicator.className = 'processing-indicator';
        indicator.id = 'processing-indicator';
        indicator.innerHTML = `
            <div class="processing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span class="processing-text">正在处理...</span>
        `;
        this.terminalContent.appendChild(indicator);
        this.scrollToBottom();
    }

    hideProcessingIndicator() {
        const indicator = document.getElementById('processing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    scrollToBottom() {
        this.terminalContainer.scrollTop = this.terminalContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    hasDetails(data) {
        // 检查是否有额外的详细信息
        return data && (
            data.agent_id ||
            data.agent_info ||
            data.args ||
            data.confirmation ||
            data.tool_content ||
            data.locations
        );
    }

    createDetailsElement(type, data) {
        const detailsElement = document.createElement('div');
        detailsElement.className = 'message-details';

        // 添加 agent_id
        if (data.agent_id) {
            const item = document.createElement('div');
            item.className = 'message-detail-item';
            item.innerHTML = `<span class="message-detail-label">Agent ID:</span> ${this.escapeHtml(data.agent_id)}`;
            detailsElement.appendChild(item);
        }

        // 添加 agent_info
        if (data.agent_info) {
            const item = document.createElement('div');
            item.className = 'message-detail-item';
            item.innerHTML = `<span class="message-detail-label">Agent Info:</span> ${this.escapeHtml(JSON.stringify(data.agent_info))}`;
            detailsElement.appendChild(item);
        }

        // 添加工具调用详细信息
        if (type === 'tool') {
            if (data.args) {
                const item = document.createElement('div');
                item.className = 'message-detail-item';
                item.innerHTML = `<span class="message-detail-label">Args:</span> ${this.escapeHtml(JSON.stringify(data.args))}`;
                detailsElement.appendChild(item);
            }
            if (data.confirmation) {
                const item = document.createElement('div');
                item.className = 'message-detail-item';
                item.innerHTML = `<span class="message-detail-label">Confirmation:</span> ${this.escapeHtml(data.confirmation)}`;
                detailsElement.appendChild(item);
            }
            if (data.tool_content) {
                const item = document.createElement('div');
                item.className = 'message-detail-item';
                item.innerHTML = `<span class="message-detail-label">Content:</span> ${this.escapeHtml(data.tool_content)}`;
                detailsElement.appendChild(item);
            }
            if (data.locations) {
                const item = document.createElement('div');
                item.className = 'message-detail-item';
                item.innerHTML = `<span class="message-detail-label">Locations:</span> ${this.escapeHtml(JSON.stringify(data.locations))}`;
                detailsElement.appendChild(item);
            }
        }

        return detailsElement;
    }

    updateDetailsVisibility() {
        const messages = this.terminalContent.querySelectorAll('.message');
        messages.forEach(message => {
            if (this.showDetails) {
                message.classList.add('show-details');
            } else {
                message.classList.remove('show-details');
            }
        });
    }

    // 心跳检测
    startHeartbeat() {
        setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // 每30秒发送一次心跳
    }

    // 移动端侧边栏切换
    toggleSidebar() {
        this.sidebar.classList.toggle('open');
        this.sidebarOverlay.classList.toggle('show');
        document.body.style.overflow = this.sidebar.classList.contains('open') ? 'hidden' : '';
    }

    closeSidebar() {
        this.sidebar.classList.remove('open');
        this.sidebarOverlay.classList.remove('show');
        document.body.style.overflow = '';
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.terminal = new Terminal();
    window.terminal.startHeartbeat();
});