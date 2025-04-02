import socket
import json
from threading import Thread, Lock

def server_program():
    host = '0.0.0.0' # to listen on all network interfaces
    port = 53444

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))

    MAX_PLAYERS = 4
    curr_players = 0

    print(f"UDP Server is listening on {host}:{port}")

    # Game state initialization
    GRID_SIZE = 8
    game_state = {}  # initialize as dict of dicts
    for row in range(GRID_SIZE):
        game_state[str(row)] = {}
        for col in range(GRID_SIZE):
            game_state[str(row)][str(col)] = {"owner": None, "color_idx": None}
            
    drawing_state = {}  # track which squares are being drawn
    player_count = 0
    players = {}
    player_scores = {
        "Red": 0,
        "Cyan": 0,
        "Green": 0,
        "Pink": 0
    }

    while True:
        data, client_address = server_socket.recvfrom(1024)
        message = json.loads(data.decode())
        message_type = message["type"]
        client_id = message["client_id"]
        data = message["data"]

        if message_type == "join":
            # assign a player ID and color
            if client_id not in players:
                curr_players += 1
                if curr_players > MAX_PLAYERS:
                    print("Player count exceeded!")
                    response = {
                        "type": "max_player_count_reached",
                        "data": None
                    }
                    server_socket.sendto(json.dumps(response).encode(), client_address)
                    continue
                
                player_count += 1
                players[client_id] = {
                    "player_number": player_count - 1,
                    "client_address": client_address,
                    "color_idx": (player_count - 1) % 4,  # cycle through 4 colors
                    "score": 0,
                }
                print(f"Player {client_id} joined the game with color index {players[client_id]['color_idx']}.")

                response = {
                    "type": "start",
                    "data": {
                        "color_idx": players[client_id]["color_idx"],
                        "player_count": player_count
                    }
                }
                server_socket.sendto(json.dumps(response).encode(), client_address)
                
                # send current game state to the new player
                game_state_response = {
                    "type": "game_state",
                    "data": {
                        "game_board": game_state,
                        "player_count": player_count,
                        "drawing": drawing_state,
                        "color_scores": player_scores
                    }
                }
                server_socket.sendto(json.dumps(game_state_response).encode(), client_address)

        elif message_type == "start_drawing":
            row = data.get("row")
            col = data.get("col")
            
            # mark square as being drawn
            if str(row) not in drawing_state:
                drawing_state[str(row)] = {}
            
            drawing_state[str(row)][str(col)] = {
                "drawer_id": client_id,
                "color_idx": players[client_id]["color_idx"]
            }
            
            # broadcast to all players about the drawing
            for player_id, player_info in players.items():
                response = {
                    "type": "start_drawing",
                    "data": {
                        "row": row,
                        "col": col,
                        "drawer_id": client_id,
                        "color_idx": players[client_id]["color_idx"]
                    }
                }
                server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])

        elif message_type == "drawing":
            # forward drawing data with pen thickness
            start = data.get("start")
            end = data.get("end")
            thickness = data.get("thickness", 5)
            row = data.get("row")
            col = data.get("col")
            
            for player_id, player_info in players.items():
                if player_id != client_id:  # Don't send back to the sender
                    response = {
                        "type": "drawing",
                        "data": {
                            "start": start,
                            "end": end,
                            "thickness": thickness,
                            "color_idx": players[client_id]["color_idx"],
                            "row": row,
                            "col": col
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])

        elif message_type == "end_drawing":
            row = data.get("row")
            col = data.get("col")
            fill_percentage = data.get("fill_percentage", 0)
            color_idx = players[client_id]["color_idx"]
            
            # remove from drawing state
            if str(row) in drawing_state and str(col) in drawing_state[str(row)]:
                del drawing_state[str(row)][str(col)]
            
            # if fill percentage is more than 50, claim the square
            if fill_percentage >= 50:
                game_state[str(row)][str(col)] = {
                    "owner": client_id,
                    "color_idx": color_idx
                }
                players[client_id]["score"] += 1
                player_scores[list(player_scores.keys())[color_idx]] += 1
                
                # broadcast to all players about the ownership of square
                for player_id, player_info in players.items():
                    response = {
                        "type": "square_owned",
                        "data": {
                            "row": row,
                            "col": col,
                            "owner_id": client_id,
                            "color_idx": color_idx,
                            "score": players[client_id]["score"],
                            "color_scores": player_scores
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])
            
            # update all players with game state
            for player_id, player_info in players.items():
                response = {
                    "type": "game_state",
                    "data": {
                        "game_board": game_state,
                        "player_count": player_count,
                        "drawing": drawing_state,
                        "color_scores": player_scores
                    }
                }
                server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])
                
            free_squares = 64 - player_scores["Red"] - player_scores["Cyan"] - player_scores["Green"] - player_scores["Pink"]
            temp_player_scores = player_scores.copy()
            first_place = max(temp_player_scores, key=temp_player_scores.get)
            temp_player_scores[first_place] = -99999
            second_place = max(temp_player_scores, key=temp_player_scores.get)
            temp_player_scores[second_place] = -99999
            third_place = max(temp_player_scores, key=temp_player_scores.get)
            temp_player_scores[third_place] = -99999
            fourth_place = max(temp_player_scores, key=temp_player_scores.get)
    
            if player_scores[second_place] + free_squares < player_scores[first_place]:
                for player_id, player_info in players.items():
                    response = {
                        "type": "end_game",
                        "data": {
                            "winner": first_place+" Wins!"
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])
            elif player_scores[second_place] == player_scores[first_place] and \
            player_scores[second_place] == player_scores[third_place] and \
            player_scores[second_place] == player_scores[fourth_place] and free_squares == 0:
                for player_id, player_info in players.items():
                    response = {
                        "type": "end_game",
                        "data": {
                            "winner": "Tie between Red, Cyan, Green, and Pink"
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])
            elif player_scores[second_place] == player_scores[first_place] and \
            player_scores[second_place] == player_scores[third_place] and free_squares == 0:
                for player_id, player_info in players.items():
                    response = {
                        "type": "end_game",
                        "data": {
                            "winner": "Tie between "+first_place+", "+second_place+", and "+third_place
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])
            elif player_scores[second_place] == player_scores[first_place] and free_squares == 0:
                for player_id, player_info in players.items():
                    response = {
                        "type": "end_game",
                        "data": {
                            "winner": "Tie between "+first_place+" and "+second_place
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])
            
        elif message_type == "leave":
            # handle player leaving
            if client_id in players:
                player_info = players.pop(client_id)
                player_count -= 1
                print(f"Player {client_id} left the game.")
                curr_players -= 1
                # Optionally, update other players about the departure
                for player_id, player_info in players.items():
                    response = {
                        "type": "game_state",
                        "data": {
                            "game_board": game_state,
                            "player_count": player_count,
                            "drawing": drawing_state,
                            "color_scores": player_scores
                        }
                    }
                    server_socket.sendto(json.dumps(response).encode(), player_info["client_address"])

        else:
            # unknown message type
            print(f"Received unknown message type from {client_address}: {message_type}")

if __name__ == '__main__':
    server_program()