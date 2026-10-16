import socket

HOST = '0.0.0.0'
PORT = 9001

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

                if data.upper() == "PING":
                    conn.sendall(b"PONG\n")
                    print("Ricevuto: PING -> Risposto: PONG")
                elif data.upper().startswith("ECHO "):
                    # split(' ', 1) divide la stringa al MASSIMO 1 volta al primo spazio
                    parti = data.split(' ', 1)
                    testo = parti[1]  # Prende tutto il testo dopo il primo spazio

                    # Inviamo il testo indietro codificandolo in byte
                    conn.sendall(f"{testo}\n".encode('utf-8'))
                    print(f"Ricevuto: ECHO -> Risposto: {testo}")

                else:
                    conn.sendall(b"ERR\n")
                    print(f"Ricevuto comando non valido ({data}) -> Risposto: ERR")