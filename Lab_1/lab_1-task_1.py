import socket
import threading

HOST = '0.0.0.0'
PORT = 9001
kv_store = {}
kv_lock = threading.Lock()

def gestisci_client(conn, addr):
    print(f"Connessione ricevuta da: {addr}")
    buffer = ""

    with conn:
        while True:
            raw_data = conn.recv(1024)

            # Se raw_data è vuoto, il client ha chiuso la connessione
            if not raw_data:
                print(f"Connessione chiusa da: {addr}")
                break

            # Aggiungiamo i byte ricevuti al buffer del client
            buffer += raw_data.decode('utf-8', errors='ignore')

            # FRAMING: Processa tutti i comandi completati da un newline (\n)
            while "\n" in buffer:
                # Separa la prima riga dal resto del buffer
                line, buffer = buffer.split("\n", 1)

                # Rimuove eventuali ritorni a capo Windows (\r)
                data = line.strip('\r')

                if not data:
                    continue

                # 1. PING
                if data.upper() == "PING":
                    conn.sendall(b"PONG\n")
                    print(f"[{addr}] Ricevuto: PING -> Risposto: PONG")

                # 2. ECHO
                elif data.upper().startswith("ECHO "):
                    parti = data.split(' ', 1)
                    testo = parti[1]
                    conn.sendall(f"{testo}\n".encode('utf-8'))
                    print(f"[{addr}] Ricevuto: ECHO -> Risposto: {testo}")

                # 3. SET <key> <value>
                elif data.upper().startswith("SET ") or data.upper() == "SET":
                    parti = data.split(' ', 2)
                    if len(parti) < 3:
                        conn.sendall(b"ERR\n")
                        print(f"[{addr}] Ricevuto: SET non valido -> Risposto: ERR")
                    else:
                        chiave = parti[1]
                        valore = parti[2]
                        # Accesso in scrittura protetto da Lock
                        with kv_lock:
                            kv_store[chiave] = valore
                        conn.sendall(b"OK\n")
                        print(f"[{addr}] Ricevuto: SET {chiave} -> Risposto: OK")

                # 4. GET <key>
                elif data.upper().startswith("GET ") or data.upper() == "GET":
                    parti = data.split(' ', 1)
                    if len(parti) < 2:
                        conn.sendall(b"ERR\n")
                        print(f"[{addr}] Ricevuto: GET non valido -> Risposto: ERR")
                    else:
                        chiave = parti[1]
                        # Accesso in lettura protetto da Lock
                        with kv_lock:
                            valore = kv_store.get(chiave)

                        if valore is not None:
                            conn.sendall(f"{valore}\n".encode('utf-8'))
                            print(f"[{addr}] Ricevuto: GET {chiave} -> Risposto: {valore}")
                        else:
                            conn.sendall(b"NOT_FOUND\n")
                            print(f"[{addr}] Ricevuto: GET {chiave} -> Risposto: NOT_FOUND")

                # Comando sconosciuto
                else:
                    conn.sendall(b"ERR\n")
                    print(f"[{addr}] Ricevuto comando non valido ({data}) -> Risposto: ERR")

def avvia_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server in ascolto su {HOST}:{PORT}...")

        while True:
            conn, addr = server_socket.accept()
            # CONCORRENZA: Crea un nuovo thread per ogni client connesso
            client_thread = threading.Thread(
                target=gestisci_client,
                args=(conn, addr),
                daemon=True
            )
            client_thread.start()

if __name__ == "__main__":
    try:
        avvia_server()
    except KeyboardInterrupt:
        print("\nChiusura del server in corso...")