import os
import threading
import time
from clients.app.client import Battleship
from clients.app.game_processes import *

grpc_host = os.getenv('GRPC_HOST', 'localhost')
grpc_port = os.getenv('GRPC_PORT', '50051')

playing = threading.Event()
playing.set()

battleship = Battleship(grpc_host=grpc_host, grpc_port=grpc_port)
myBoard = Board()
myBoard.Generation()
lastGuess = ''


@battleship.on()
def begin():
    print('Game started!')


@battleship.on()
def start_turn():
    global lastGuess
    s = input('Where do you want to attack? > ')
    while not validationCheck(s)[0]:
        print(f"{validationCheck(s)[1]}! Please Try Again.")
        s = input("Where do you want to attack? > ")
    lastGuess = s
    battleship.attack(s)


@battleship.on()
def hit():
    myBoard.Guess(lastGuess, True)
    print("\n > You hit something!")


@battleship.on()
def miss():
    myBoard.Guess(lastGuess, False)
    print('\n > Aww.. You missed!')


@battleship.on()
def win():
    myBoard.Guess(lastGuess, True)
    print('> Yay! You won!')
    playing.clear()


@battleship.on()
def lose():
    print('> Aww... You lost...')
    playing.clear()


@battleship.on()
def attack(vector):
    print(f'Shot received at {vector}!')
    x, y = myBoard.AttackCheck(vector)
    if x:
        print(f"They've struck your {y.code}!")
        if myBoard.CheckLives():
            battleship.defeat()
        else:
            battleship.hit()
    else:
        battleship.miss()


print('Waiting for the game to start...')
battleship.join()
while playing.is_set():
    time.sleep(1.0)
