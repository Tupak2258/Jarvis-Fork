"""
Простая веб-панель для мониторинга Jarvis
Запуск: python web_dashboard.py
"""

import json
import time
from pathlib import Path
from flask import Flask, render_template_string, jsonify
import threading


app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Jarvis Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status { display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; font-size: 12px; }
        .status.online { background: #28a745; }
        .status.offline { background: #dc3545; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-value { font-size: 24px; font-weight: bold; color: #007bff; }
        .metric-label { font-size: 12px; color: #666; }
        .log-entry { padding: 5px 0; border-bottom: 1px solid #eee; font-family: monospace; font-size: 12px; }
        .refresh-btn { background: #007bff; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Jarvis Assistant Dashboard</h1>
        
        <div class="card">
            <h3>Статус системы <span id="status" class="status offline">OFFLINE</span></h3>
            <div id="metrics">
                <div class="metric">
                    <div class="metric-value" id="uptime">--</div>
                    <div class="metric-label">Время работы</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="memory">--</div>
                    <div class="metric-label">Память (MB)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="response-time">--</div>
                    <div class="metric-label">Время отклика (s)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="requests">--</div>
                    <div class="metric-label">Запросов</div>
                </div>
            </div>
            <button class="refresh-btn" onclick="refreshData()">Обновить</button>
        </div>
        
        <div class="card">
            <h3>Последние логи</h3>
            <div id="logs" style="max-height: 300px; overflow-y: auto;">
                <div class="log-entry">Загрузка логов...</div>
            </div>
        </div>
    </div>

    <script>
        function refreshData() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.online ? 'ONLINE' : 'OFFLINE';
                    document.getElementById('status').className = 'status ' + (data.online ? 'online' : 'offline');
                    
                    if (data.metrics) {
                        document.getElementById('uptime').textContent = data.metrics.uptime_formatted || '--';
                        document.getElementById('memory').textContent = data.metrics.current_memory_mb ? 
                            Math.round(data.metrics.current_memory_mb) : '--';
                        document.getElementById('response-time').textContent = data.metrics.average_response_time ? 
                            data.metrics.average_response_time.toFixed(2) : '--';
                        document.getElementById('requests').textContent = data.metrics.total_requests || '--';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    document.getElementById('status').textContent = 'ERROR';
                    document.getElementById('status').className = 'status offline';
                });
            
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    const logsDiv = document.getElementById('logs');
                    logsDiv.innerHTML = '';
                    data.logs.forEach(log => {
                        const div = document.createElement('div');
                        div.className = 'log-entry';
                        div.textContent = log;
                        logsDiv.appendChild(div);
                    });
                })
                .catch(error => console.error('Logs error:', error));
        }
        
        // Автообновление каждые 5 секунд
        setInterval(refreshData, 5000);
        refreshData(); // Первоначальная загрузка
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def api_status():
    """API для получения статуса системы"""
    try:
        # Проверяем наличие файла сессии
        session_file = Path("data/session.json")
        if session_file.exists():
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Проверяем, работает ли система (файл обновлялся недавно)
            file_age = time.time() - session_file.stat().st_mtime
            online = file_age < 30  # Считаем онлайн если файл обновлялся менее 30 сек назад
            
            return jsonify({
                'online': online,
                'last_update': session_data.get('last_session'),
                'metrics': session_data.get('metrics', {})
            })
        else:
            return jsonify({'online': False, 'error': 'Session file not found'})
            
    except Exception as e:
        return jsonify({'online': False, 'error': str(e)})


@app.route('/api/logs')
def api_logs():
    """API для получения последних логов"""
    try:
        log_file = Path("logs/jarvis.log")
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Возвращаем последние 20 строк
            recent_logs = [line.strip() for line in lines[-20:] if line.strip()]
            return jsonify({'logs': recent_logs})
        else:
            return jsonify({'logs': ['Лог-файл не найден']})
            
    except Exception as e:
        return jsonify({'logs': [f'Ошибка чтения логов: {str(e)}']})


def run_dashboard():
    """Запускает веб-панель в отдельном потоке"""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)


if __name__ == '__main__':
    print("🌐 Запуск Jarvis Dashboard на http://127.0.0.1:5000")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        run_dashboard()
    except KeyboardInterrupt:
        print("\n👋 Dashboard остановлен")