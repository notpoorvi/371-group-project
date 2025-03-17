import socket
import time



# Set up the client socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Start time for RTT calculation
start_time = time.time()

# For a single message

# Send message to the server
message = "Hello UDP"
client_socket.sendto(message.encode(), ('localhost', 53444))

# Receive the response from server
response, server_address = client_socket.recvfrom(1024)
print(f"Received response: {response.decode()}")

# End time for receiving the last reply
end_time = time.time()

# Calculate RTT
rtt = (end_time - start_time) * 1000  # in milliseconds
print(f"Round-Trip Time (RTT): {rtt} ms")

# Close the socket
client_socket.close()
