import socket
import pygame
from threading import Thread, Lock, main_thread, current_thread
import random
import json
import sys
import numpy as np

# send message to the server
def send_message(message_type, data=None):
    # format and send message to server
    message = {
        "type": message_type,
        "client_id": client_id,
        "data": data or {}
    }
    message_str = json.dumps(message)
    # send message
    client_socket.sendto(message_str.encode(), server_address)

pygame.init()

# TODO: replace 'localhost' with the actual ip of the server'
HOST = 'localhost'
PORT = 53444
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = (HOST, PORT)  # server IP and port
client_id = random.randint(1000, 9999)  # unique client ID

# setting up display
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
BOARD_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT) - 100 #500
pygame.display.set_caption(f"Deny and Conquer: Player {client_id}")
    
# color definitions 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

PLAYER_COLORS = [
    (255, 0, 0),    # Red
    (0, 255, 255),  # Cyan
    (0, 255, 0),    # Green
    (255, 0, 255),  # Pink
]

# setting up the grid size
GRID_SIZE = 8
SQUARE_SIZE = BOARD_SIZE // GRID_SIZE #62
GRID_TOP_LEFT_X = (SCREEN_WIDTH - BOARD_SIZE) // 2 #150
GRID_TOP_LEFT_Y = (SCREEN_HEIGHT - BOARD_SIZE) // 2 #50
PEN_THICKNESS = 5

# game state variables, updated when receiving messages from server
game_state = {} # which player owns which square
drawing_state = {} # which squares are being drawn on
player_count = 0 # no. of players playing
pixel_count = 0 # no. of pixels colored
my_color_idx = 0  # will be set from server message
my_color = PLAYER_COLORS[0]  # default, will be updated
font = pygame.font.SysFont(None, 26)
running = True # flag to control the receiver thread
winning_text = "" # text to display at the end of the game
player_scores = {
    "Red": 0,
    "Cyan": 0,
    "Green": 0,
    "Pink": 0
}

# cursor settings (draw a circle at the mouse position with radius 6)
show_cursor = True
cursor_radius = 6

# function to draw the cursor
def draw_cursor():
    if show_cursor:
        mouse_pos = pygame.mouse.get_pos()
        # draw cursor only if within the grid area
        if (GRID_TOP_LEFT_X <= mouse_pos[0] < GRID_TOP_LEFT_X + BOARD_SIZE and 
            GRID_TOP_LEFT_Y <= mouse_pos[1] < GRID_TOP_LEFT_Y + BOARD_SIZE):
            
            # draw the colored circle
            pygame.draw.circle(screen, my_color, mouse_pos, cursor_radius)
            # draw a black border
            pygame.draw.circle(screen, BLACK, mouse_pos, cursor_radius, 1)

# receive messages from the server
def receive_message():
    global game_state, drawing_state, player_count, my_color_idx, my_color, player_scores, game_running, winning_text
    
    while running:
        try:
            client_socket.settimeout(0.5)
            data, _ = client_socket.recvfrom(4096)
            message = json.loads(data.decode())
            
            # check the message type of each message from the server
            if message["type"] == "start": # new player joined
                my_color_idx = message["data"]["color_idx"] # index of the color assigned to the player
                my_color = PLAYER_COLORS[my_color_idx] # get the color
                player_count = message["data"]["player_count"] # number of players playing
                print(f"Connected as player {client_id} with color {my_color} (index {my_color_idx})")
                print(f"Number of players playing the game: {player_count}")
            
            # if the server is full, exit
            elif message["type"] == "max_player_count_reached":
                sys.exit("Failed to join the game, server reached max player count")
            
            # current game state, which player owns which square ...
            elif message["type"] == "game_state":
                game_state = message["data"]["game_board"] # current game state
                player_count = message["data"]["player_count"] # number of players playing
                player_scores = message["data"]["color_scores"] # current scores of each player
                if "drawing" in message["data"]: # drawing state
                    drawing_state = message["data"]["drawing"]
            
            # updated when a player owns a square by coloring it more than 50%
            elif message["type"] == "square_owned":
                row = message["data"]["row"] # row of the square
                col = message["data"]["col"] # column of the square
                owner_id = message["data"]["owner_id"] # id of the player who owns the square
                color_idx = message["data"]["color_idx"] # index of the color assigned to the player
                score = message["data"]["score"] # score of the player who owns the square

                # map color index to color
                color_map = {
                    0: "Red",
                    1: "Cyan",
                    2: "Green",
                    3: "Pink"
                }

                player_color = color_map[color_idx]  # get the player name
                player_scores[player_color] = score # update the player's score
                
                # update the game state
                if str(row) not in game_state:
                    game_state[str(row)] = {}
                
                game_state[str(row)][str(col)] = {
                    "owner": owner_id,
                    "color_idx": color_idx
                }
            
            # updated when a player starts drawing on a square
            elif message["type"] == "start_drawing":
                row = message["data"]["row"] # row of the square
                col = message["data"]["col"] # column of the square
                drawer_id = message["data"]["drawer_id"] # id of the player who is drawing
                color_idx = message["data"]["color_idx"] # index of the color assigned to the player
                
                if str(row) not in drawing_state:
                    drawing_state[str(row)] = {}
                
                drawing_state[str(row)][str(col)] = {
                    "drawer_id": drawer_id,
                    "color_idx": color_idx,
                    "surface": pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                }
                drawing_state[str(row)][str(col)]["surface"].fill((255, 255, 255, 0))
            
            # updated when a player ends drawing on a square
            elif message["type"] == "drawing":
                row = message["data"]["row"] # row of the square
                col = message["data"]["col"] # column of the square
                start = message["data"]["start"] # start position of the line
                end = message["data"]["end"] # end position of the line
                color_idx = message["data"]["color_idx"] # index of the color assigned to the player
                thickness = message["data"].get("thickness", PEN_THICKNESS) # thickness of the line
                
                # draw the line on the surface of the square
                if str(row) in drawing_state and str(col) in drawing_state[str(row)]:
                    surface = drawing_state[str(row)][str(col)]["surface"]
                    pygame.draw.line(surface, PLAYER_COLORS[color_idx], start, end, thickness)
                    
            # updated when a player ends drawing on a square
            elif message["type"] == "end_game":
                game_running = False
                winning_text = message["data"]["winner"]
        
        except socket.timeout:
            continue    
        
        # handle any exceptions that may occur
        except Exception as e:
            if running:
                print(f"Error receiving message: {e}")

def draw_scores():
    score_x = 20  # X position for the scores
    score_y = 20  # Starting Y position
    spacing = 30  # Space between scores

    for i, (player, score) in enumerate(player_scores.items()):
        score_text = font.render(f"{player}: {score}", True, "black")
        screen.blit(score_text, (score_x, score_y + i * spacing))  # Display score

def draw_curr_board():
    try:
        # background
        screen.fill(WHITE)

        # Scores
        draw_scores()
        screen.blit(font.render(f"{winning_text}", True, "black"), (360, 20))

        # drawing 8 by 8 Grid
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                # calculate the position of the square
                x = GRID_TOP_LEFT_X + col * SQUARE_SIZE
                y = GRID_TOP_LEFT_Y + row * SQUARE_SIZE
                
                square_color = WHITE
                # check if square is owned
                if str(row) in game_state and str(col) in game_state[str(row)]:
                    color_idx = game_state[str(row)][str(col)]["color_idx"]
                    # square_color = PLAYER_COLORS[color_idx]
                    if color_idx is not None:
                        square_color = PLAYER_COLORS[color_idx]
                
                # draw the square
                pygame.draw.rect(
                    screen, 
                    square_color, 
                    (x, y, SQUARE_SIZE, SQUARE_SIZE)
                )
                # draw the border
                pygame.draw.rect(
                    screen, 
                    BLACK, 
                    (x, y, SQUARE_SIZE, SQUARE_SIZE), 
                    1  
                )
                
                # draw squares being drawn on by other players
                if str(row) in drawing_state and str(col) in drawing_state[str(row)]:
                    drawer_id = drawing_state[str(row)][str(col)]["drawer_id"]
                    if drawer_id != client_id:  # only draw others drawings
                        drawer_surface = drawing_state[str(row)][str(col)].get("surface")
                        if drawer_surface:
                            screen.blit(drawer_surface, (x, y))

        # if we're currently drawing, show our drawing
        if drawing_in_progress and drawing_surface and current_square:
            row, col = current_square
            x = GRID_TOP_LEFT_X + col * SQUARE_SIZE
            y = GRID_TOP_LEFT_Y + row * SQUARE_SIZE
            screen.blit(drawing_surface, (x, y)) # draw the current drawing surface

        # draw the cursor (circle only if cursor in grid area)
        draw_cursor()

        if current_thread() is main_thread():
            # update the display
            pygame.display.flip()
    
    except Exception as e:
        print(f"Error in draw_curr_board: {e}")

# global variables for drawing
drawing_in_progress = False
drawing_surface = None
drawing_pixels = None
current_square = None
last_Pos = None
total_pixels = 0

# function to determine which grid square the mouse is in
def get_grid_position(mouse_pos):
    x, y = mouse_pos
    # check if the mouse is within the grid area
    if (GRID_TOP_LEFT_X <= x < GRID_TOP_LEFT_X + BOARD_SIZE and 
        GRID_TOP_LEFT_Y <= y < GRID_TOP_LEFT_Y + BOARD_SIZE):
        # calculate the row and column
        col = int((x - GRID_TOP_LEFT_X) // (BOARD_SIZE / GRID_SIZE))
        row = int((y - GRID_TOP_LEFT_Y) // (BOARD_SIZE / GRID_SIZE))
        return row, col
    return None, None

def start_drawing(square):
    global drawing_in_progress, current_square, drawing_surface, drawing_pixels, pixel_count, total_pixels, last_Pos
    row, col = square
    
    # check if the square is already owned or being drawn on
    if (str(row) in game_state and str(col) in game_state[str(row)] and game_state[str(row)][str(col)]["owner"] is not None) or \
    (str(row) in drawing_state and str(col) in drawing_state[str(row)]):
        return False
    
    # set up drawing
    drawing_in_progress = True
    current_square = (row, col)
    drawing_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
    drawing_surface.fill((255, 255, 255, 0))  # transparent
    
    drawing_pixels = np.zeros((SQUARE_SIZE, SQUARE_SIZE), dtype=bool)
    pixel_count = 0
    total_pixels = SQUARE_SIZE * SQUARE_SIZE
    last_Pos = None
    
    # notify server the player is starting to draw
    send_message("start_drawing", {
        "row": row,
        "col": col
    })
    return True

def continue_drawing(pos):
    global pixel_count, drawing_pixels, last_Pos
    
    if not drawing_in_progress or not current_square:
        return
    
    # get the current square based on the mouse position
    row, col = current_square
    square_x = GRID_TOP_LEFT_X + col * SQUARE_SIZE
    square_y = GRID_TOP_LEFT_Y + row * SQUARE_SIZE
    
    # get relative position within the square
    rel_x = pos[0] - square_x
    rel_y = pos[1] - square_y
    
    # check if position is within the square
    if 0 <= rel_x < SQUARE_SIZE and 0 <= rel_y < SQUARE_SIZE:
        current_pos = (rel_x, rel_y)
        
        if last_Pos:
            # draw line between last position and current position
            pygame.draw.line(drawing_surface, my_color, last_Pos, current_pos, PEN_THICKNESS)
            
            # send drawing data to server
            send_message("drawing", {
                "row": row,
                "col": col,
                "start": last_Pos,
                "end": current_pos,
                "thickness": PEN_THICKNESS
            })
            
            # mark pixels as drawn (for fill percentage tracking)
            dx = current_pos[0] - last_Pos[0]
            dy = current_pos[1] - last_Pos[1]
            steps = max(abs(dx), abs(dy)) + 1
            
            # calculate the number of pixels to fill
            if steps > 1:
                for i in range(steps):
                    t = i / (steps - 1)
                    x = int(last_Pos[0] + t * dx)
                    y = int(last_Pos[1] + t * dy)
                    
                    for ox in range(-PEN_THICKNESS, PEN_THICKNESS + 1):
                        for oy in range(-PEN_THICKNESS, PEN_THICKNESS + 1):
                            if ox*ox + oy*oy <= PEN_THICKNESS*PEN_THICKNESS:
                                px, py = x + ox, y + oy
                                if 0 <= px < SQUARE_SIZE and 0 <= py < SQUARE_SIZE and not drawing_pixels[py, px]:
                                    drawing_pixels[py, px] = True
                                    pixel_count += 1
        else:
            # if it's the first point, draw a circle
            pygame.draw.circle(drawing_surface, my_color, current_pos, PEN_THICKNESS)
        
        last_Pos = current_pos

def end_drawing():
    global drawing_in_progress, current_square, drawing_surface, drawing_pixels
    
    if not drawing_in_progress or not current_square:
        return
    
    row, col = current_square
    # calculate the fill percentage
    fill_percentage = (pixel_count / total_pixels) * 100
    
    # update local drawing state
    if str(row) not in drawing_state:
        drawing_state[str(row)] = {}
    
    # send the fill percentage to the server
    send_message("end_drawing", {
        "row": row,
        "col": col,
        "fill_percentage": fill_percentage
    })
    
    # reset drawing state
    drawing_in_progress = False
    current_square = None
    drawing_surface = None
    drawing_pixels = None

game_running = True
game_closed_manually = False
# send message to server to join the game
send_message("join")

# Use thread to not freeze the application
receiver_thread = Thread(target=receive_message, daemon=True)
receiver_thread.start()

# Game loop (keeps the game running)
draw_curr_board()
clock = pygame.time.Clock()

while game_running:
    clock.tick(60)
    # check for events
    for event in pygame.event.get():
        # if the window is closed, exit
        if event.type == pygame.QUIT:
            game_running = False
            game_closed_manually = True
        
        # if mouse is down, start drawing
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not drawing_in_progress:
                pos = pygame.mouse.get_pos()
                grid_pos = get_grid_position(pos)
                if grid_pos[0] is not None:
                    start_drawing(grid_pos)
        
        # if mouse is moving, continue drawing
        elif event.type == pygame.MOUSEMOTION and drawing_in_progress:
            continue_drawing(pygame.mouse.get_pos())
        
        # if mouse is up, end drawing
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and drawing_in_progress:
            end_drawing()
    
    # draw the board every frame
    draw_curr_board()

if drawing_in_progress:
    end_drawing()

show_game_over_screen = True
if not game_closed_manually:
    while show_game_over_screen:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                show_game_over_screen = False
        draw_curr_board()
running = False
receiver_thread.join(timeout=1.0)
send_message("leave")
client_socket.close()
pygame.quit()