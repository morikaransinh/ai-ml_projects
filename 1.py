import pygame
import socket
import cv2
import numpy as np
import threading
import pickle
import struct

# ------------- SOCKET SETUP -------------
HOST = "0.0.0.0"
PORT = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("Waiting for client to connect...")
conn, addr = server.accept()
print("Connected:", addr)

# ------------- PYGAME SETUP -------------
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Player variables
x, y = 350, 250
speed = 8

# Movement state
move = None

# ------------- RECEIVE INPUT THREAD -------------
def receive_input():
    global move
    while True:
        try:
            data = conn.recv(1024).decode()
            if data:
                move = data
        except:
            break

threading.Thread(target=receive_input, daemon=True).start()

# ------------- MAIN LOOP -------------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    # Move player
    if move == "left":  x -= speed
    if move == "right": x += speed
    if move == "up":    y -= speed
    if move == "down":  y += speed

    # Draw frame
    screen.fill((30, 30, 30))
    pygame.draw.rect(screen, (0, 255, 0), (x, y, 50, 50))
    pygame.display.flip()

    # Capture frame
    frame = pygame.surfarray.array3d(screen)
    frame = np.rot90(frame)
    frame = cv2.flip(frame, 1)

    # Encode frame
    _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
    data = pickle.dumps(buffer)
    message = struct.pack("Q", len(data)) + data

    # Send frame
    try:
        conn.sendall(message)
    except:
        break

    clock.tick(30)
