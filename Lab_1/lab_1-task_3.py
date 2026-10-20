import os, ssl, json, secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie

# Recupera il percorso della cartella attuale (Lab_1)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cert_path = os.path.join(BASE_DIR, '..', 'cert.pem')
key_path = os.path.join(BASE_DIR, '..', 'key.pem')
ca_path = os.path.join(BASE_DIR, '..', 'ca.crt')

sessions = {}


class TLSHandler(BaseHTTPRequestHandler):

    def send_json(self, status_code, data):

        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response_bytes)

    def get_session_user(self):

        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None

        cookie = SimpleCookie(cookie_header)
        if "session_id" in cookie:
            session_id = cookie["session_id"].value
            return sessions.get(session_id)
        return None

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"200 OK\n")

        elif self.path == "/me":
            user = self.get_session_user()
            if user:
                self.send_json(200, {"user": user})
            else:
                self.send_json(401, {"error": "Unauthorized"})

        else:
            self.send_json(404, {"error": "Not Found"})

    def do_POST(self):
        if self.path == "/login":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))
                user = data.get("user")
                password = data.get("password")
            except Exception:
                self.send_json(400, {"error": "Bad Request"})
                return

            if password == "netsec" and user and isinstance(user, str):

                session_id = secrets.token_hex(16)
                sessions[session_id] = user

                self.send_response(200)

                self.send_header(
                    "Set-Cookie", f"session_id={session_id}; Secure; HttpOnly; Path=/")

                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"message": "Logged in"}).encode("utf-8"))
            else:

                self.send_json(401, {"error": "Unauthorized"})

        else:
            self.send_json(404, {"error": "Not Found"})


if __name__ == '__main__':
  server = HTTPServer(('0.0.0.0', 8443), TLSHandler)

  context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  # Uso dei percorsi dinamici calcolati in alto
  context.load_cert_chain(certfile=cert_path, keyfile=key_path)

  server.socket = context.wrap_socket(server.socket, server_side=True)

  print('HTTPS Server listening on port 8443...')
  server.serve_forever()