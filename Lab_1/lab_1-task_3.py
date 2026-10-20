import os
import ssl
from http.server import BaseHTTPRequestHandler, HTTPServer

# Recupera il percorso della cartella attuale (Lab_1)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

cert_path = os.path.join(BASE_DIR, '..', 'cert.pem')
key_path = os.path.join(BASE_DIR, '..', 'key.pem')
ca_path = os.path.join(BASE_DIR, '..', 'ca.crt')


class TLSHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    if self.path == '/':
      self.send_response(200)
      self.end_headers()
      self.wfile.write(b'200 OK\n')
    else:
      self.send_response(404)
      self.end_headers()


if __name__ == '__main__':
  server = HTTPServer(('0.0.0.0', 8443), TLSHandler)

  context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  # Uso dei percorsi dinamici calcolati in alto
  context.load_cert_chain(certfile=cert_path, keyfile=key_path)

  server.socket = context.wrap_socket(server.socket, server_side=True)

  print('HTTPS Server listening on port 8443...')
  server.serve_forever()