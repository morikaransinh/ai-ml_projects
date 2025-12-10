import socket
import cv2
import pickle
import struct
import pygame
import numpy as np

print("Starting client...")

SERVER_IP = "127.0.0.1"   # Local testing
PORT = 9999

try:
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((SERVER_IP, PORT))
    print("Connected to server!")
except Exception as e:
    print("Connection failed:", e)
    input("Press Enter to exit...")
    exit()

pygame.init()
pygame.display.set_mode((300, 200))
clock = pygame.time.Clock()

data = b""
payload_size = struct.calcsize("Q")

while True:
    try:
        # ---- Receive video ----
        while len(data) < payload_size:
            packet = client.recv(4096)
            if not packet:
                break
            data += packet

        packed_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("Q", packed_size)[0]

        while len(data) < msg_size:
            data += client.recv(4096)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        img = cv2.imdecode(frame, cv2.IMREAD_COLOR)

        cv2.imshow("Cloud Game Stream", img)

        # ---- Send key input ----
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            client.send(b"left")
        elif keys[pygame.K_RIGHT]:
            client.send(b"right")
        elif keys[pygame.K_UP]:
            client.send(b"up")
        elif keys[pygame.K_DOWN]:
            client.send(b"down")

        if cv2.waitKey(1) == 27:
            break

        clock.tick(60)

    except Exception as e:
        print("Error:", e)
        break

cv2.destroyAllWindows()
