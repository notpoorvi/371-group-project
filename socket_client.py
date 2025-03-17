import socket

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('142.58.219.181', 53444)  # server IP and port
# to get the server IP (same as client IP since running on local host, check print output of server program)

message = "Hello UDP Server"
client_socket.sendto(message.encode(), server_address)  

response, _ = client_socket.recvfrom(1024)  
print(f"Received response: {response.decode()}")

client_socket.close()
