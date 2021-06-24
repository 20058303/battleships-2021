# Battleships Game Client (App\Client)

## Overview
The game client has been rewritten to allow for digitalized ship placement as well as automatic validation of hits,
misses and end states while being built upon the basic networking capabilities already existing within the game client.

### main.py 

The client main.py allows both the sending and recieving of messages over a network between players, while drawing
of both their own game board and a version of the enemy's game board (containing only hits and misses). The main.py
client also allows the player to place their ships before connecting to the network.

### game_processes.py 

This handles the bulk of game logic, such as validating the player's inputs, handling the grid logic along with each
cell contained within the grid and it's connected ship instances. 

### Game play

#### Initialization
Upon the game being opened, the players are prompted to place each of their ships one by one until all ships are
successfully contained within the battlefield. To do this, the player must first type in the position they'd like
their ship to be placed in, from anywhere between A1 to J10, and then whether they'd like the ship to be orientated
vertically or horizontally.

Once all ships have been successfully placed, the server should connect both clients and the game will begin.

### Main Game Loop
From here, each player has a chance to try and guess where the other player's ships are. They do so by providing a
position, much like before, with A1 to J10. The server then sends that position over to the enemy client which will
then validate whether or not there is a ship located in that coordinate. If so, the enemy client sends back a confirmation
(or confirmation of a miss) and a relevant symbol is drawn on the current player's version of the enemy's board with an X
or an O.

### End Game State
The game progresses until the point where one player's ships have all been destroyed or sunk. Once this occurs, the player
with ships remaining is declared the winner and the game is concluded.
