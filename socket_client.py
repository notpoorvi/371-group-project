import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 53444)  # server IP and port

message = "Hello UDP Server"
client_socket.sendto(message.encode(), server_address)  

response, _ = client_socket.recvfrom(1024)  
print(f"Received response: {response.decode()}")

client_socket.close()
