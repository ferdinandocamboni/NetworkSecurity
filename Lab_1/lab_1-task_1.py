import socket

HOST = '0.0.0.0'
PORT = 9001
kv_store = {}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Permette di riutilizzare la porta immediatamente dopo la chiusura dello script
    server_socket.bind((HOST, PORT))# Collega il socket all'indirizzo e alla porta specificati
    server_socket.listen()# Mette il socket in ascolto
    print(f"Server in ascolto su {HOST}:{PORT}...")

    while True:
        conn, addr = server_socket.accept()
        with conn:
            print(f"Connessione ricevuta da: {addr}")
            while True:
                raw_data = conn.recv(1024)
                # Se raw_data è vuoto, il client ha chiuso la connessione
                if not raw_data:
                    print(f"Connessione chiusa da: {addr}")
                    break
                    # Usiamo rstrip() per rimuovere solo gli \n e \r finali, non gli spazi in mezzo
                data = raw_data.decode('utf-8').rstrip()

                if not data:
                    continue

                parti_comando = data.split(' ')
                comando = parti_comando[0].upper()
# Gestione dei comandi - command management
                #PING
                if data.upper() == "PING":
                    conn.sendall(b"PONG\n")
                    print("Ricevuto: PING -> Risposto: PONG")

                #ECHO
                elif data.upper().startswith("ECHO "):
                    # split(' ', 1) divide la stringa al MASSIMO 1 volta al primo spazio
                    parti = data.split(' ', 1)
                    testo = parti[1]  # Prende tutto il testo dopo il primo spazio
                    conn.sendall(f"{testo}\n".encode('utf-8')) # Inviamo il testo indietro codificandolo in byte
                    print(f"Ricevuto: ECHO -> Risposto: {testo}")

                # 3. SET <key> <value>
                elif data.upper().startswith("SET ") or data.upper() == "SET":
                    # Divide al massimo in 3 parti: ["SET", "chiave", "valore intero"]
                    parti = data.split(' ', 2)

                    if len(parti) < 3:
                        # Manca la chiave o il valore
                        conn.sendall(b"ERR\n")
                        print("Ricevuto: SET non valido -> Risposto: ERR")
                    else:
                        chiave = parti[1]
                        valore = parti[2]
                        kv_store[chiave] = valore
                        conn.sendall(b"OK\n")
                        print(f"Ricevuto: SET {chiave} -> Risposto: OK")

                # 4. GET <key>
                elif data.upper().startswith("GET ") or data.upper() == "GET":
                    # Divide al massimo in 2 parti: ["GET", "chiave"]
                    parti = data.split(' ', 1)

                    if len(parti) < 2:
                        # Manca la chiave
                        conn.sendall(b"ERR\n")
                        print("Ricevuto: GET non valido -> Risposto: ERR")
                    else:
                        chiave = parti[1]
                        if chiave in kv_store:
                            valore = kv_store[chiave]
                            conn.sendall(f"{valore}\n".encode('utf-8'))
                            print(f"Ricevuto: GET {chiave} -> Risposto: {valore}")
                        else:
                            conn.sendall(b"NOT_FOUND\n")
                            print(f"Ricevuto: GET {chiave} -> Risposto: NOT_FOUND")
                #ERR
                else:
                    conn.sendall(b"ERR\n")
                    print(f"Ricevuto comando non valido ({data}) -> Risposto: ERR")