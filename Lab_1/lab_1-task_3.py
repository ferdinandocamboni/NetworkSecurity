import os, ssl, json, secrets, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def trova_file(*filenames):
    """Cerca il primo file esistente tra i nomi dati: cartella dello script,
    cartella padre, cartella di lavoro corrente."""
    cartelle = [BASE_DIR, os.path.join(BASE_DIR, '..'), os.getcwd()]
    for cartella in cartelle:
        for filename in filenames:
            path = os.path.join(cartella, filename)
            if os.path.exists(path):
                return path
    return os.path.join(BASE_DIR, filenames[0])


cert_path = trova_file('cert.pem', 'server.crt')
key_path = trova_file('key.pem', 'server.key')
ca_path = trova_file('ca.crt')

sessions = {}
sessions_lock = threading.Lock()


class TLSHandler(BaseHTTPRequestHandler):
    # Timeout sulla connessione: evita che client lenti o "muti" blocchino un thread
    timeout = 10

    def log_message(self, format, *args):
        pass  # log silenziosi (opzionale: rimuovi per vedere le richieste)

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def send_body(self, status, body=b'', content_type=None, extra_headers=None):
        self.send_response(status)
        if content_type:
            self.send_header('Content-Type', content_type)
        for name, value in (extra_headers or []):
            self.send_header(name, value)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if body:
            self.wfile.write(body)

    def get_session_id(self):
        cookie_header = self.headers.get('Cookie')
        if not cookie_header:
            return None
        try:
            cookie = SimpleCookie(cookie_header)
        except Exception:
            return None
        if 'session_id' in cookie:
            return cookie['session_id'].value
        return None

    def extract_client_cn(self):
        try:
            client_cert = self.connection.getpeercert()
            if not client_cert or 'subject' not in client_cert:
                return None

            # 'subject' è una tupla di RDN: ((('commonName', 'nome_client'),),)
            for rdn in client_cert.get('subject', ()):
                for key, val in rdn:
                    if key == 'commonName':
                        return val
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Metodi HTTP
    # ------------------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/':
            self.send_body(200, b'200 OK\n', 'text/plain')

        elif path == '/me':
            session_id = self.get_session_id()
            with sessions_lock:
                username = sessions.get(session_id) if session_id else None
            if username is not None:
                response_data = json.dumps({'user': username}).encode('utf-8')
                self.send_body(200, response_data, 'application/json')
            else:
                self.send_body(401)

        elif path == '/whoami':
            cn = self.extract_client_cn()
            if cn:
                self.send_body(200, cn.encode('utf-8'), 'text/plain')
            else:
                self.send_body(401)

        else:
            self.send_body(404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == '/login':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
                if not isinstance(data, dict):
                    raise ValueError('JSON non valido')
                username = data.get('user')
                password = data.get('password')
            except Exception:
                self.send_body(400)
                return

            if password == 'netsec' and isinstance(username, str) and username:
                session_id = secrets.token_hex(16)
                with sessions_lock:
                    sessions[session_id] = username
                cookie_header = (
                    f'session_id={session_id}; Secure; HttpOnly; Path=/'
                )
                self.send_body(
                    200,
                    json.dumps({'status': 'ok'}).encode('utf-8'),
                    'application/json',
                    [('Set-Cookie', cookie_header)],
                )
            else:
                # Nessun Set-Cookie in caso di credenziali errate
                self.send_body(401)

        else:
            self.send_body(404)


class DiagServer(ThreadingHTTPServer):
    """ThreadingHTTPServer che stampa il motivo degli handshake TLS falliti."""

    def get_request(self):
        try:
            return super().get_request()
        except ssl.SSLError as e:
            print(f'[porta {self.server_address[1]}] handshake TLS fallito: {e}', flush=True)
            raise


def make_server(port, mtls=False):
    server = DiagServer(('0.0.0.0', port), TLSHandler)
    server.daemon_threads = True

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)

    if mtls:
        context.load_verify_locations(cafile=ca_path)
        context.verify_mode = ssl.CERT_REQUIRED

    server.socket = context.wrap_socket(server.socket, server_side=True)
    return server


def run_server_8443():
    server = make_server(8443)
    print('HTTPS Server running on port 8443...')
    server.serve_forever()


def run_server_8444():
    server = make_server(8444, mtls=True)
    print('mTLS Server running on port 8444...')
    server.serve_forever()


def stampa_file_usati():
    print(f'cert : {os.path.abspath(cert_path)}')
    print(f'key  : {os.path.abspath(key_path)}')
    print(f'ca   : {os.path.abspath(ca_path)}')
    try:
        pem = open(ca_path).read()
        der = ssl.PEM_cert_to_DER_cert(pem)
        import hashlib
        fp = hashlib.sha256(der).hexdigest().upper()
        print('ca sha256: ' + ':'.join(fp[i:i + 2] for i in range(0, len(fp), 2)))
    except Exception as e:
        print(f'ca: impossibile leggere ({e})')


if __name__ == '__main__':
    stampa_file_usati()
    thread_8443 = threading.Thread(target=run_server_8443, daemon=True)
    thread_8443.start()
    run_server_8444()
