import socket

def server_program():
    # UDP Server that handles multiple clients (no need for threads since UDP is connectionless)
    host = socket.gethostbyname(socket.gethostname())  # Get actual IP
    port = 53444

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    print(f"UDP Server is listening on {host}:{port}")

    counter = 0;
    while True:
        data, client_address = server_socket.recvfrom(1024) 
        message = data.decode()
        
        if message == "Hello UDP Server":
            server_socket.sendto(str(counter).encode(), client_address)
            counter+=1;
        
        print(f"Received from {client_address}: {message}")

        response = "Hello UDP client"
        server_socket.sendto(response.encode(), client_address)

if __name__ == '__main__':
    server_program()
