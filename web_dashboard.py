#!/usr/bin/env python3
"""
OpenClaw Pro Web Dashboard
Flask-based web interface for easy access to the AI agent
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
import json
from pathlib import Path
from datetime import datetime
import secrets
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global agent instance
agent = None
active_sessions = {}


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status')
def status():
    """Get agent status"""
    return jsonify({
        'status': 'ready' if agent else 'not_initialized',
        'model': agent.model if agent else None,
        'tools': len(agent.tools) if agent else 0,
        'memory_enabled': True
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    if not agent:
        return jsonify({'error': 'Agent not initialized'}), 500

    try:
        # Process message in background
        session_id = session.get('session_id', 'default')

        # TODO: Call agent.chat() with message
        response = f"[Demo] Processing: {message}"

        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tools')
def list_tools():
    """List available tools"""
    if not agent:
        return jsonify({'error': 'Agent not initialized'}), 500

    tools = []
    for name, tool in agent.tools.items():
        tools.append({
            'name': name,
            'description': tool.description
        })

    return jsonify({'tools': tools})


@app.route('/api/memory/search', methods=['POST'])
def search_memory():
    """Search Obsidian memory"""
    data = request.json
    query = data.get('query', '')

    try:
        from obsidian_memory import obsidian_memory
        results = obsidian_memory.search_notes(query)

        return jsonify({
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/memory/recent')
def recent_memory():
    """Get recent memory items"""
    try:
        from obsidian_memory import obsidian_memory

        conversations = obsidian_memory.get_recent_conversations(5)
        projects = obsidian_memory.get_active_projects()

        return jsonify({
            'conversations': conversations,
            'projects': projects
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/projects')
def list_projects():
    """List projects"""
    try:
        from obsidian_memory import obsidian_memory
        projects = obsidian_memory.get_active_projects()

        return jsonify({
            'projects': projects,
            'count': len(projects)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# SocketIO events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    session_id = secrets.token_hex(8)
    session['session_id'] = session_id
    active_sessions[session_id] = {'connected_at': datetime.now().isoformat()}
    emit('connected', {'session_id': session_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    session_id = session.get('session_id')
    if session_id in active_sessions:
        del active_sessions[session_id]


@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle real-time chat messages"""
    message = data.get('message', '')

    if not message:
        return

    # Echo user message
    emit('message', {
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().isoformat()
    })

    # Process with agent (in background)
    if agent:
        try:
            # TODO: Integrate actual agent
            response = f"[Demo] Response to: {message}"

            emit('message', {
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            emit('error', {'message': str(e)})


def create_html_template():
    """Create HTML template if it doesn't exist"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    template_file = templates_dir / 'index.html'

    if not template_file.exists():
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenClaw Pro 🦅 Dashboard</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            background: white;
            border-radius: 15px;
            padding: 20px 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        h1 {
            color: #333;
            font-size: 2em;
            margin-bottom: 5px;
        }

        .status {
            color: #666;
            font-size: 0.9em;
        }

        .status.ready { color: #00aa00; }
        .status.error { color: #cc0000; }

        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .panel {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .panel h2 {
            color: #333;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }

        #chat-container {
            height: 500px;
            display: flex;
            flex-direction: column;
        }

        #chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 15px;
        }

        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 8px;
            max-width: 80%;
        }

        .message.user {
            background: #667eea;
            color: white;
            margin-left: auto;
        }

        .message.assistant {
            background: #e3f2fd;
            color: #333;
        }

        .message-role {
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 0.9em;
        }

        .input-group {
            display: flex;
            gap: 10px;
        }

        #message-input {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
        }

        #message-input:focus {
            outline: none;
            border-color: #667eea;
        }

        button {
            padding: 12px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: background 0.3s;
        }

        button:hover {
            background: #5568d3;
        }

        button:active {
            transform: scale(0.98);
        }

        .tool-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }

        .tool-button {
            padding: 15px;
            background: #f8f9fa;
            border: 2px solid #ddd;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: left;
        }

        .tool-button:hover {
            background: #e3f2fd;
            border-color: #667eea;
        }

        .tool-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }

        .tool-desc {
            font-size: 0.85em;
            color: #666;
        }

        .memory-item {
            padding: 10px;
            background: #f8f9fa;
            border-left: 3px solid #667eea;
            margin-bottom: 8px;
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.3s;
        }

        .memory-item:hover {
            background: #e3f2fd;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }

        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🦅 OpenClaw Pro Dashboard</h1>
            <div class="status ready" id="status">● Ready</div>
        </header>

        <div class="main-grid">
            <!-- Chat Panel -->
            <div class="panel">
                <h2>💬 Chat with OpenClaw</h2>
                <div id="chat-container">
                    <div id="chat-messages"></div>
                    <div class="input-group">
                        <input type="text" id="message-input" placeholder="Type your message..."
                               onkeypress="if(event.key==='Enter') sendMessage()">
                        <button onclick="sendMessage()">Send 🚀</button>
                    </div>
                </div>
            </div>

            <!-- Tools Panel -->
            <div class="panel">
                <h2>🔧 Quick Tools</h2>
                <div class="tool-grid">
                    <div class="tool-button" onclick="useTool('read_file')">
                        <div class="tool-name">📖 Read File</div>
                        <div class="tool-desc">Read file contents</div>
                    </div>
                    <div class="tool-button" onclick="useTool('write_file')">
                        <div class="tool-name">✍️ Write File</div>
                        <div class="tool-desc">Create/modify files</div>
                    </div>
                    <div class="tool-button" onclick="useTool('web_search')">
                        <div class="tool-name">🌐 Web Search</div>
                        <div class="tool-desc">Search the web</div>
                    </div>
                    <div class="tool-button" onclick="useTool('run_command')">
                        <div class="tool-name">⚡ Run Command</div>
                        <div class="tool-desc">Execute commands</div>
                    </div>
                </div>

                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value" id="conversations-count">0</div>
                        <div class="stat-label">Conversations</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value" id="projects-count">0</div>
                        <div class="stat-label">Projects</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Memory Panel -->
        <div class="panel">
            <h2>🧠 Recent Memory</h2>
            <div id="memory-list">
                <div class="memory-item">Loading memory...</div>
            </div>
        </div>
    </div>

    <script>
        const socket = io();

        socket.on('connect', () => {
            console.log('Connected to OpenClaw Pro');
            document.getElementById('status').className = 'status ready';
            document.getElementById('status').textContent = '● Ready';
        });

        socket.on('message', (data) => {
            addMessage(data.role, data.content);
        });

        socket.on('error', (data) => {
            addMessage('system', 'Error: ' + data.message);
        });

        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();

            if (!message) return;

            socket.emit('chat_message', { message: message });
            input.value = '';
        }

        function addMessage(role, content) {
            const messagesDiv = document.getElementById('chat-messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + role;

            const roleLabel = role === 'user' ? '👤 You' : '🦅 OpenClaw';
            messageDiv.innerHTML = `
                <div class="message-role">${roleLabel}</div>
                <div>${content}</div>
            `;

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function useTool(toolName) {
            const input = document.getElementById('message-input');
            input.value = `Use ${toolName} to `;
            input.focus();
        }

        // Load recent memory
        fetch('/api/memory/recent')
            .then(r => r.json())
            .then(data => {
                const memoryList = document.getElementById('memory-list');
                memoryList.innerHTML = '';

                data.conversations.forEach(conv => {
                    const item = document.createElement('div');
                    item.className = 'memory-item';
                    item.textContent = '💬 ' + conv;
                    memoryList.appendChild(item);
                });

                data.projects.forEach(proj => {
                    const item = document.createElement('div');
                    item.className = 'memory-item';
                    item.textContent = '📁 ' + proj;
                    memoryList.appendChild(item);
                });

                document.getElementById('conversations-count').textContent = data.conversations.length;
                document.getElementById('projects-count').textContent = data.projects.length;
            })
            .catch(err => console.error('Error loading memory:', err));

        // Load status
        fetch('/api/status')
            .then(r => r.json())
            .then(data => {
                console.log('Agent status:', data);
            });
    </script>
</body>
</html>"""

        template_file.write_text(html_content)


def start_dashboard(openclaw_agent, host='0.0.0.0', port=5000):
    """Start the web dashboard"""
    global agent
    agent = openclaw_agent

    # Create HTML template
    create_html_template()

    print(f"\n🌐 Starting OpenClaw Pro Dashboard...")
    print(f"📍 Access at: http://localhost:{port}")
    print(f"🔗 Or: http://{host}:{port}")
    print(f"\n✅ Dashboard ready!\n")

    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    create_html_template()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
