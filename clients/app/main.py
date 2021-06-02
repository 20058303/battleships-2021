import os
import time
import threading
from sense_hat import SenseHat


sense = SenseHat()
grpc_host = os.getenv('GRPC_HOST', 'localhost')
grpc_port = os.getenv('GRPC_PORT', '50051')

c = {
    "o": [0,0,0],
    "r": [255,0,0],
    "b": [0,0,255],
    "g": [0,255,0],
    "y": [255,255,0],
    "p": [0,255,255]
}

messages = {
    "started": sense.show_message("Game Start!", text_colour=c["r"]),
    "win": sense.show_message("You win!", text_colour=c["y"]),
    "lose": sense.show_message("You lose :(", text_colour=c["p"]),
    "turn": sense.show_message("Your turn!", text_colour=c["b"]),
    "hit": [
        c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],
        c["o"],c["r"],c["o"],c["o"],c["o"],c["o"],c["r"],c["o"],
        c["o"],c["o"],c["r"],c["o"],c["o"],c["r"],c["o"],c["o"],
        c["o"],c["o"],c["o"],c["r"],c["r"],c["o"],c["o"],c["o"],
        c["o"],c["o"],c["o"],c["r"],c["r"],c["o"],c["o"],c["o"],
        c["o"],c["o"],c["r"],c["o"],c["o"],c["r"],c["o"],c["o"],
        c["o"],c["r"],c["o"],c["o"],c["o"],c["o"],c["r"],c["o"],
        c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],
    ],
    "miss": [
        c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],
        c["o"],c["o"],c["o"],c["b"],c["b"],c["o"],c["o"],c["o"],
        c["o"],c["o"],c["b"],c["o"],c["o"],c["b"],c["o"],c["o"],
        c["o"],c["b"],c["o"],c["o"],c["o"],c["o"],c["b"],c["o"],
        c["o"],c["b"],c["o"],c["o"],c["o"],c["o"],c["b"],c["o"],
        c["o"],c["o"],c["b"],c["o"],c["o"],c["b"],c["o"],c["o"],
        c["o"],c["o"],c["o"],c["b"],c["b"],c["o"],c["o"],c["o"],
        c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],c["o"],
    ]
}

playing = threading.Event()
playing.set()

# battleship = Battleship(grpc_host=grpc_host, grpc_port=grpc_port)


@battleship.on()
def begin():
