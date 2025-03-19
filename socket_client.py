import socket
import pygame
pygame.init()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('142.58.219.181', 53444)  # server IP and port
# to get the server IP (same as client IP since running on local host, check print output of server program)

# Setting up display
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
BOARD_SIZE = min(SCREEN_WIDTH, SCREEN_HEIGHT) - 100
pygame.display.set_caption("Whiteboard")



message = "Hello UDP Server"
client_socket.sendto(message.encode(), server_address)
    
#Color definations 
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

#Setting up the grid size
GRID_SIZE = 8
SQUARE_SIZE = BOARD_SIZE // GRID_SIZE
GRID_TOP_LEFT_X = (SCREEN_WIDTH - BOARD_SIZE) // 2
GRID_TOP_LEFT_Y = (SCREEN_HEIGHT - BOARD_SIZE) // 2

#Background
screen.fill(WHITE)

#Drawing 8 by 8 Grid
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

# Game loop (keeps the game running)
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
client_socket.close()
