import socket
import json


def server_program():
    # UDP Server that handles multiple clients (no need for threads since UDP is connectionless)
    host = socket.gethostbyname(socket.gethostname())  # Get actual IP
    port = 53444

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    print(f"UDP Server is listening on {host}:{port}")

    # Game state initialization
    GRID_SIZE = 8
    game_state = {
        f"{row},{col}": {"owner": None, "color_idx": None}
        for row in range(GRID_SIZE) for col in range(GRID_SIZE)
    }
    player_count = 0
    players = {}


    while True:
        data, client_address = server_socket.recvfrom(1024)
        message = json.loads(data.decode())
        message_type = message["type"]
        client_id = message["client_id"]
        data = message["data"]

        if message_type == "join":
            # Assign a player ID
            player_count += 1
            player_number = player_count  # Start counting players from 1
            players[client_id] = {
                "player_number": player_number,
                "client_address": client_address
            }
            print(f"Player {player_number} joined the game.")

            response = {
                "type": "start",
                "data": {
                    "color_idx": (player_number - 1),  # Assign player colors based on player_number
                    "player_count": player_count
                }
            }
            server_socket.sendto(json.dumps(response).encode(), client_address)

        elif message_type == "drawing":
            # Forward drawing data to all players without modifying game state
            for player_id, player_info in players.items():
                if player_id != client_id:  # Don't send back to the sender
                    response = {
                        "type": "drawing",
                        "data": data
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])

        elif message_type == "leave":
            # Handle player leaving
            if client_id in players:
                player_info = players.pop(client_id)
                player_count -= 1
                print(f"Player {player_info['player_number']} left the game.")

                # Optionally, update other players about the departure
                for player_id, player_info in players.items():
                    response = {
                        "type": "game_state",
                        "data": {
                            "game_board": game_state,
                            "player_count": player_count
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])

        else:
            # Unknown message type
            print(f"Received unknown message type from {client_address}: {message_type}")



if __name__ == '__main__':
    server_program()
