from http.server import HTTPServer, BaseHTTPRequestHandler

class MiniHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'200 OK\n')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found\n')

    # Return 404 for non-GET methods
    def send_error(self, code, message=None, explain=None):
        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MiniHandler)
    print("Server listening on port 8080...")
    server.serve_forever()