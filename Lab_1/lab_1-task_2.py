from http.server import HTTPServer, BaseHTTPRequestHandler
#Gestione delle richieste
class MiniHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':#Verifica del path della richiesta
            self.send_response(200)
            self.end_headers()#termina la sezione degli headers http
            self.wfile.write(b'200 OK\n')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found\n')

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MiniHandler)
    print("Server listening on port 8080...")
    server.serve_forever()