import socket

HOST = '0.0.0.0'
PORT = 9001

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    # Permette di riutilizzare la porta immediatamente dopo la chiusura dello script
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Collega il socket all'indirizzo e alla porta specificati
    server_socket.bind((HOST, PORT))

    # Mette il socket in ascolto (accetta connessioni in entrata)
    server_socket.listen()
    print(f"Server in ascolto su {HOST}:{PORT}...")