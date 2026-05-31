import http.server
import socketserver
import webbrowser
import threading
import sys
import os
import json
from pathlib import Path

PORT = 8080
DIRECTORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PREVIEWABLE = {'.md', '.txt', '.json', '.tsv', '.toml'}
TREE_EXCLUDE = {'eval_logs'}
FILE_EXCLUDE = {'state.json'}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
        
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def do_GET(self):
        if self.path == '/api/tree':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            workspace = Path(DIRECTORY) / "workspace"
            tree = self._build_tree(workspace, "workspace")
            self.wfile.write(json.dumps(tree).encode())
            return

        # Legacy compat
        if self.path == '/api/files':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'[]')
            return
            
        return super().do_GET()
    
    def _build_tree(self, dir_path, rel_prefix):
        """Recursively build a file tree for the workspace."""
        result = []
        if not dir_path.exists():
            return result
        
        for item in sorted(dir_path.iterdir()):
            rel = f"/{rel_prefix}/{item.name}"
            if item.is_dir():
                if item.name in TREE_EXCLUDE:
                    continue
                children = self._build_tree(item, f"{rel_prefix}/{item.name}")
                if children:  # Only include non-empty directories
                    result.append({
                        "name": item.name,
                        "type": "dir",
                        "path": rel,
                        "children": children
                    })
            elif item.suffix.lower() in PREVIEWABLE and item.name not in FILE_EXCLUDE:
                result.append({
                    "name": item.name,
                    "type": "file",
                    "path": rel,
                    "size": item.stat().st_size
                })
        return result

    def log_message(self, format, *args):
        pass

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def start_server():
    with ReusableTCPServer(("", PORT), Handler) as httpd:
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
        while True:
            server_thread.join(1)
    except KeyboardInterrupt:
        print("\nShutting down dashboard server.")
        sys.exit(0)
