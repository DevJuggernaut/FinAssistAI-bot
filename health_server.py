from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import json
import os
from database.config import PORT

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'status': 'healthy',
                'service': 'finassistai-bot',
                'message': 'Bot is running'
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Вимикаємо логування HTTP запитів
        pass

def start_health_server():
    """Запускає простий HTTP сервер для health check"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        return server
    except Exception as e:
        # Якщо не вдається запустити сервер, це не критично
        print(f"Warning: Could not start health server: {e}")
        return None
