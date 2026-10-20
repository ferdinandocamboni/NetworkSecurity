from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

notes_db = {}
next_id = 1
#Gestione delle richieste
class MiniHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):

        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response_bytes)

    def send_empty_response(self, status_code):
        self.send_response(status_code)
        self.end_headers()

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
            self.send_json(200, {"msg": msg_text})

        elif path in ('/notes', '/notes/'):
            # GET su /notes senza ID non è supportato -> 405
            self.send_json(405, {"error": "Method Not Allowed"})

        elif path.startswith('/notes/'):
            raw_id = path[len('/notes/'):]

            # Controllo ID numerico e presenza nota
            if not raw_id.isdigit():
                self.send_json(404, {"error": "Not Found"})
                return

            note_id = int(raw_id)
            if note_id not in notes_db:
                self.send_json(404, {"error": "Not Found"})
                return

            self.send_json(200, {"id": note_id, "text": notes_db[note_id]})

        else:
            self.send_json(404, {"error": "Not Found"})

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path in ('/notes', '/notes/'):
            # 1. Verifica Content-Type
            content_type = self.headers.get('Content-Type', '')
            if content_type.split(';')[0].strip().lower() != 'application/json':
                self.send_json(415, {"error": "Unsupported Media Type"})
                return

            # 2. Lettura e parsing del body JSON
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
            except (ValueError, json.JSONDecodeError):
                self.send_json(400, {"error": "Bad Request"})
                return

            # 3. Validazione struttura: deve essere dict, avere 'text' e 'text' deve essere stringa
            if not isinstance(data, dict) or 'text' not in data or not isinstance(data['text'], str):
                self.send_json(400, {"error": "Bad Request"})
                return

            # 4. Creazione nota
            global next_id
            note_id = next_id
            notes_db[note_id] = data['text']
            next_id += 1

            self.send_json(201, {"id": note_id})

        elif path.startswith('/notes/'):
            # POST su /notes/<id> non è permesso -> 405
            self.send_json(405, {"error": "Method Not Allowed"})

        else:
            self.send_json(404, {"error": "Not Found"})

    def do_DELETE(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path in ('/notes', '/notes/'):
            # DELETE su /notes senza ID -> 405
            self.send_json(405, {"error": "Method Not Allowed"})

        elif path.startswith('/notes/'):
            raw_id = path[len('/notes/'):]

            if not raw_id.isdigit():
                self.send_json(404, {"error": "Not Found"})
                return

            note_id = int(raw_id)
            if note_id not in notes_db:
                self.send_json(404, {"error": "Not Found"})
                return

            del notes_db[note_id]
            self.send_empty_response(204)

        else:
            self.send_json(404, {"error": "Not Found"})

    def do_PUT(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path.startswith('/notes'):
            self.send_json(405, {"error": "Method Not Allowed"})
            return

        self.send_json(404, {"error": "Not Found"})



if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8080), MiniHandler)
    print("Server listening on port 8080...")
    server.serve_forever()