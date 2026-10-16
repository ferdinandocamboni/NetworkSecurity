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
            data = conn.recv(1024).decode('utf-8').strip()

            if data.upper() == "PING":
                conn.sendall(b"PONG\n")
                print("Ricevuto: PING -> Risposto: PONG")
            else:
                conn.sendall(b"Errore: Invia 'PING'\n")




if __name__ == "__main__":
    try:
        avvia_server_ping()
    except KeyboardInterrupt:
        print("\nChiusura del server in corso...")