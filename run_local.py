import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

from api.generate import handler as ApiHandler

class LocalHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="public", **kwargs)

    def do_POST(self):
        if self.path == "/api/generate":
            # Delegate to the Vercel serverless function logic
            ApiHandler.do_POST(self)
        else:
            self.send_error(404, "Not Found")

    def do_OPTIONS(self):
        if self.path == "/api/generate":
            ApiHandler.do_OPTIONS(self)
        else:
            self.send_response(200)
            self.end_headers()

    # The underlying api.generate logic expects _send_error on self
    def _send_error(self, code, message):
        ApiHandler._send_error(self, code, message)

if __name__ == "__main__":
    # Ensure working directory is correct
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = 8000
    print(f"Server starting -> http://localhost:{port}")
    httpd = HTTPServer(('', port), LocalHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down locally...")
