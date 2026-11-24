import ssl, json, secrets, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie

sessions = {}

class HTTPSHandler(BaseHTTPRequestHandler):

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'200 OK\n')
            return

        if self.path == '/me':
            cookie_header = self.headers.get("Cookie", "")

            cookies = SimpleCookie()
            cookies.load(cookie_header)

            session_cookie = cookies.get("session")

            if session_cookie is None:
                self.send_json(401, {"error": "Unauthorized"})
                return

            token = session_cookie.value
            user = sessions.get(token)

            if user is None:
                self.send_json(401, {"error": "Unauthorized"})
                return

            self.send_json(200, {"user": user})
            return

        self.send_json(404, {"error": "Not Found"})

    def do_POST(self):
        if self.path != '/login':
            self.send_json(404, {"error": "Not Found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                self.send_json(400, {"error": "Invalid JSON"})
                return
        except json.JSONDecodeError:
            self.send_json(400, {"error": "Invalid JSON"})
            return

        user = data.get("user")
        password = data.get("password")

        if not isinstance(user, str) or not user or password != "netsec":
            self.send_json(401, {"error": "Unauthorized"})
            return

        token = secrets.token_urlsafe(32)
        sessions[token] = user

        response = json.dumps({"user": user}).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.send_header(
            "Set-Cookie",
            f"session={token}; Path=/; Secure; HttpOnly; SameSite=Strict"
        )
        self.end_headers()

        self.wfile.write(response)

class MTLSHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path != '/whoami':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found\n')
            return

        # Get the client certificate
        cert = self.connection.getpeercert()

        # Extract the Common Name (CN)
        common_name = None

        for rdn in cert.get('subject', ()):
            for key, value in rdn:
                if key == 'commonName':
                    common_name = value

        if common_name is None:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'Client certificate has no CN\n')
            return

        # Return the client certificate CN
        body = common_name.encode('utf-8')

        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

server = HTTPServer(('0.0.0.0', 8443), HTTPSHandler)

context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

context.load_cert_chain(
    certfile='certs/server.crt',
    keyfile='certs/server.key'
)

server.socket = context.wrap_socket(
    server.socket,
    server_side=True
)

print("HTTPS server listening on port 8443")

# Create the mTLS server
server_8444 = HTTPServer(
    ('0.0.0.0', 8444),
    MTLSHandler
)

# Create TLS context for client authentication
context_8444 = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

# Load the server certificate
context_8444.load_cert_chain(
    certfile='certs/server.crt',
    keyfile='certs/server.key'
)

# Load the CA that can authenticate clients
context_8444.load_verify_locations(
    cafile='certs/ca.crt'
)

# Require a valid client certificate
context_8444.verify_mode = ssl.CERT_REQUIRED

# Enable TLS on port 8444
server_8444.socket = context_8444.wrap_socket(
    server_8444.socket,
    server_side=True
)
print("mTLS server listening on port 8444")

# Start HTTPS server on port 8443 in a separate thread
threading.Thread(
    target=server.serve_forever,
    daemon=True
).start()

# Start mTLS server on port 8444
server_8444.serve_forever()

