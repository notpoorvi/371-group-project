import socket
import pygame
from threading import Thread, Lock
import random
import json

# send message to the server
def send_message(message_type, data=None):
    # format and send message to server
    message = {
        "type": message_type,
        "client_id": client_id,
        "data": data or {}
    }
    message_str = json.dumps(message)
    client_socket.sendto(message_str.encode(), server_address)


# receive messages from the server
def receive_message():
    while True:
        data, _ = client_socket.recvfrom(4096)
        message = json.loads(data.decode())
        if message["type"] == "start":
            my_color = PLAYER_COLORS[message["data"]["color_idx"]]
            player_count = message["data"]["player_count"]
            print(f"Connected as player {client_id} with color {my_color}")
            print(f"Number of players playing the game: {player_count}")

        # current game state, which player owns which square ...
        elif message["type"] == "game_state":
            game_state = message["data"]["game_board"]
            player_count = message["data"]["player_count"]
            drawing_state = message["data"].get("drawing", {})

        # updated when a player owns a square by coloring it more than 50%
        elif message["type"] == "square_owned":
            row = message["data"]["row"]
            col = message["data"]["col"]
            owner_id = message["data"]["owner_id"]
            color_idx = message["data"]["color_idx"]
            game_state[str(row)][str(col)] = {
                "owner": owner_id,
                "color_idx": color_idx
            }

        elif message["type"] == "drawing":
            start = message["data"]["start"]
            end = message["data"]["end"]
            color_idx = message["data"]["color_idx"]
            draw_color = PLAYER_COLORS[color_idx]

            # Draw the received line
            pygame.draw.line(screen, draw_color, start, end, PEN_THICKNESS)
            pygame.display.flip()  # Refresh the screen to show updated drawing

        # more message types go here ...


pygame.init()

HOST = socket.gethostbyname(socket.gethostname())
# if not running on local host, change above to be the output of the server program
PORT = 53444
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (HOST, PORT)  # server IP and port
# to get the server IP (same as client IP since running on local host, check print output of server program)
client_id = random.randint(1000, 9999)  # unique client ID

# Setting up display
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
BOARD_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT) - 100
pygame.display.set_caption(f"Deny and Conquer: Player {client_id}")

# gets the player number and uses it to assign a player color.
# breaks if it goes above 4 because there are only 4 PLAYER_COLORS
send_message("join")
Thread(target=receive_message, daemon=True).start() # Use thread to not freeze the application

# Color definitions 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

PLAYER_COLORS = [
    (255, 0, 0),    # Red
    (0, 255, 255),  # Cyan
    (0, 255, 0),    # Green
    (255, 0, 255),  # Pink
]
#my_color = PLAYER_COLORS[playerNumber]
my_color = PLAYER_COLORS[0] # for testing

# Setting up the grid size
GRID_SIZE = 8
SQUARE_SIZE = BOARD_SIZE // GRID_SIZE
GRID_TOP_LEFT_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
GRID_TOP_LEFT_Y = (SCREEN_HEIGHT - BOARD_SIZE) // 2
PEN_THICKNESS = 5
# game state variables, updated when receiving messages from server
game_state = {} # which player owns which square
drawing_state = {} # which squares are being drawn on
player_count = 0 # no. of players playing
pixel_count = 0 # no. of pixels colored
color_idx = 0
font = pygame.font.SysFont(None, 26)


# Background
screen.fill(WHITE)

# Drawing 8 by 8 Grid
for row in range(GRID_SIZE):
    for col in range(GRID_SIZE):
        x = GRID_TOP_LEFT_X + col * SQUARE_SIZE
        y = GRID_TOP_LEFT_Y + row * SQUARE_SIZE
        pygame.draw.rect(
            screen, 
            WHITE, 
            (x, y, SQUARE_SIZE, SQUARE_SIZE)
        )
        pygame.draw.rect(
            screen, 
            BLACK, 
            (x, y, SQUARE_SIZE, SQUARE_SIZE), 
            1  
        )

# Update the display
pygame.display.flip()

# send message to server to join the game
send_message("join")

# Game loop (keeps the game running)
last_Pos = None
running = True
clock = pygame.time.Clock()
while running:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    mouseDown = pygame.mouse.get_pressed()[0]
    if mouseDown:
        pos = pygame.mouse.get_pos()
        xPos = pos[0]
        yPos = pos[1]
        if xPos < x+SQUARE_SIZE-1 and yPos < y+SQUARE_SIZE-1 and xPos > GRID_TOP_LEFT_X and yPos > GRID_TOP_LEFT_Y:
            if not last_Pos:
                pygame.draw.line(screen, my_color, pos, pos, 1)
            else:
                pygame.draw.line(screen, my_color, last_Pos, pos, 1)

            # Send drawing data to server with pixel coordinates
            drawing_data = {
                "start": last_Pos if last_Pos else pos,
                "end": pos,
                "color_idx": PLAYER_COLORS.index(my_color)
            }
            send_message("drawing", drawing_data)


            last_Pos = pos


        else:
            last_Pos = None
    else:
        last_Pos = None
    pygame.display.flip()

send_message("leave")
pygame.quit()
client_socket.close()