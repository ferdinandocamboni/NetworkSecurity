import os, ssl, json, secrets, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from urllib.parse import urlparse
# Recupera il percorso della cartella attuale (Lab_1)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cert_path = os.path.join(BASE_DIR, '..', 'cert.pem')
key_path = os.path.join(BASE_DIR, '..', 'key.pem')
ca_path = os.path.join(BASE_DIR, '..', 'ca.crt')

sessions = {}

class TLSHandler(BaseHTTPRequestHandler):

  def get_session_id(self):

    cookie_header = self.headers.get('Cookie')
    if not cookie_header:
      return None
    cookie = SimpleCookie(cookie_header)
    if 'session_id' in cookie:
      return cookie['session_id'].value
    return None

  def extract_client_cn(self):

    try:
      client_cert = self.connection.getpeercert()
      if not client_cert:
        return None

      for rdn in client_cert.get('subject', ()):
        for key, value in rdn:
          if key == 'commonName':
            return value
    except Exception:
      pass
    return None

  def do_GET(self):
    path = urlparse(self.path).path

    if path == '/':
      self.send_response(200)
      self.end_headers()
      self.wfile.write(b'200 OK\n')

    elif path == '/me':
      session_id = self.get_session_id()
      if session_id and session_id in sessions:
        username = sessions[session_id]
        response_data = json.dumps({'user': username}).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response_data)
      else:
        self.send_response(401)
        self.end_headers()

    elif path == '/whoami':
      cn = self.extract_client_cn()
      if cn:
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(cn.encode('utf-8'))
      else:
        # Se acceduto senza certificato mTLS valido
        self.send_response(401)
        self.end_headers()

    else:
      self.send_response(404)
      self.end_headers()

  def do_POST(self):
    path = urlparse(self.path).path

    if path == '/login':
      try:
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8'))
        username = data.get('user')
        password = data.get('password')
      except Exception:
        self.send_response(400)
        self.end_headers()
        return

      if password == 'netsec' and username:
        session_id = secrets.token_hex(16)
        sessions[session_id] = username

        cookie_header = (
            f'session_id={session_id}; Secure; HttpOnly; Path=/'
        )

        self.send_response(200)
        self.send_header('Set-Cookie', cookie_header)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
      else:
        self.send_response(401)
        self.end_headers()

    else:
      self.send_response(404)
      self.end_headers()

def run_server_8443():

  server = HTTPServer(('0.0.0.0', 8443), TLSHandler)
  context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  context.load_cert_chain(certfile=cert_path, keyfile=key_path)
  server.socket = context.wrap_socket(server.socket, server_side=True)
  print('HTTPS Server running on port 8443...')
  server.serve_forever()

def run_server_8444():

  server = HTTPServer(('0.0.0.0', 8444), TLSHandler)
  context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  context.load_cert_chain(certfile=cert_path, keyfile=key_path)

  # Configurazione verifica certificato client tramite CA
  context.load_verify_locations(cafile=ca_path)
  context.verify_mode = ssl.CERT_REQUIRED

  server.socket = context.wrap_socket(server.socket, server_side=True)
  print('mTLS Server running on port 8444...')
  server.serve_forever()

if __name__ == '__main__':

  thread_8443 = threading.Thread(target=run_server_8443, daemon=True)
  thread_8443.start()

  run_server_8444()