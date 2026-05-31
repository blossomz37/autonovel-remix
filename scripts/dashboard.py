import http.server
import socketserver
import webbrowser
import threading
import sys
import os

PORT = 8080
DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import json
from pathlib import Path

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        
    def end_headers(self):
        # Add CORS headers so we don't run into issues if testing locally
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def do_GET(self):
        if self.path == '/api/files':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            files = []
            workspace = Path(DIRECTORY) / "workspace"
            
            # Scan lore
            lore_dir = workspace / "lore"
            if lore_dir.exists():
                for f in lore_dir.glob("*.md"):
                    files.append({"name": f.name, "path": f"/workspace/lore/{f.name}", "group": "Lore"})
                for f in lore_dir.glob("*.txt"):
                    files.append({"name": f.name, "path": f"/workspace/lore/{f.name}", "group": "Lore"})
            
            # Scan chapters
            chap_dir = workspace / "chapters"
            if chap_dir.exists():
                for f in sorted(chap_dir.glob("*.md")):
                    files.append({"name": f.name, "path": f"/workspace/chapters/{f.name}", "group": "Chapters"})
            
            self.wfile.write(json.dumps(files).encode())
            return
            
        return super().do_GET()

    # Suppress console logging for every poll request to keep terminal clean
    def log_message(self, format, *args):
        pass

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Dashboard server running at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    url = f"http://localhost:{PORT}/auto-novel-progress.html"
    print(f"Opening {url} in your browser...")
    webbrowser.open(url)
    
    try:
        # Keep main thread alive so server thread can run
        while True:
            server_thread.join(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard server.")
        sys.exit(0)
