import socket
import threading


# Dictionary to track connected players
players = {}

# Disconnect message "break"

def handle_client(server_socket, player_address):
    while True:
        try:
            data, addr = server_socket.recvfrom(1024)
            message = data.decode()

            if message == "break":
                print(f"Player {addr} disconnected.")
                del players[addr]

                # Shutdown the server if no players remain
                if len(players) == 0:
                    print("All players disconnected. Shutting down server...")
                    server_socket.close()
                    return

                break

            print(f"Received from {addr}: {message}")

            # Send response
            response = "You are connected to server Game"
            server_socket.sendto(response.encode(), addr)

        except Exception as e:
            print(f"Error handling {addr}: {e}")
            break

# Broadcast message from orignated to server to all clients
def broadcast_message(server_socket, message):
    for player_addr in players:
        server_socket.sendto(message.encode(), player_addr)        

def server_program():
    host = socket.gethostname()
    port = 5888


    # Set up the server as UDP using IPV4
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Bind host address and port together
    server_socket.bind((host, port))

    
    print("Waiting for players...")

    # Since it is UDP, no connection stablishment

    while len(players) < 2:
        try:
            data, addr = server_socket.recvfrom(1024) # Data, address from player
            
            if addr not in players:
                players[addr] = True  # Track the new player, Addr -> True
                print(f"Player from {addr} connected.")
                # Create a thread to handle that player specifc messages without freezing application
                threading.Thread(target=handle_client, args=(server_socket, addr)).start() 

            # Start game logic once 2+ players have joined
            if len(players) >= 2:
                print("Minimum players connected. Starting the game...") # Replace this 

        except Exception as e:
            print(f"Error: {e}")
    
    print("Game started! Waiting for additional players...")

    server_socket.close()

if __name__ == '__main__':
    server_program()