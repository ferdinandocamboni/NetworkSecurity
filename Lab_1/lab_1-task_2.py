from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
#Gestione delle richieste
class MiniHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        if self.path == '/':#Verifica del path della richiesta
            self.send_response(200)
            self.end_headers()#termina la sezione degli headers http
            self.wfile.write(b'200 OK\n')

        elif path == '/echo':
            msg_text = query_params.get('msg', [''])[0]
            response_data = json.dumps({'msg': msg_text})
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(response_data.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found\n')

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MiniHandler)
    print("Server listening on port 8080...")
    server.serve_forever()