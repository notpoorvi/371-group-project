import socket
import threading

def handle_client(client_socket):
    # This function is responsible for handling each client connection.
    # It sends a greeting message to the client and then closes the connection.
    client_socket.send(b"Hello, Client!")
    client_socket.close()

while True:
    # The server continuously listens for incoming client connections.
    client_socket, addr = server_socket.accept()
    # When a new client connects, a new thread is created to handle the client.
    client_thread = threading.Thread(target=handle_client, args=(client_socket,))
    client_thread.start()

def server_program():
    host = socket.gethostname()
    port = 5888


    # Set up the server as UDP using IPV4
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind host address and port together
    server_socket.bind((host, port))

    socket.setblocking(False)

    # Configure how many clients the server can listen simultaneously (4)
    server_socket.listen(4) # Fours players
    conn, address = server_socket.accept()  # accept new connection
    print("Connection from: " + str(address))

   
    while True:

        data = conn.recv(1024).decode()
    
        if  data == "break":
            break  # Break loop if client disconnects
        print(f"Received: {message}")

        # Send response
        response = "ack at you UDP"
        server_socket.sendto(response.encode(), client_address)


    # Close the socket
    server_socket.close()

if __name__ == '__main__':
    server_program()