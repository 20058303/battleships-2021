shipDictionary = {      # Just a dictionary for reference
    "A": {
        "Name": "Aircraft Carrier",
        "Quantity": 1,
        "Size": 5
    },
    "B": {
        "Name": "Battleship",
        "Quantity": 1,
        "Size": 4
    },
    "S": {
        "Name": "Submarine",
        "Quantity": 3,
        "Size": 3
    },
    "C": {
        "Name": "Cruiser",
        "Quantity": 1,
        "Size": 3
    },
    "D": {
        "Name": "Destroyer",
        "Quantity": 2,
        "Size": 2
    },
    "P": {
        "Name": "Patrol Boat",
        "Quantity": 2,
        "Size": 1
    }
}


def validationCheck(_s):
    """Validates a string input in the format of 'A1' to 'J10'"""
    if 64 < ord(_s[0].upper()) < 75 and len(_s[1:]) < 3:
        try:
            if 0 < int(_s[1:]) < 11:
                return True, 'Valid Input'  # Passes
            else:
                return False, 'Invalid Number'
        except ValueError:
            return False, 'Invalid Input'
    else:
        return False, 'Invalid Input'


class Board:
    def __init__(self):
        """
        The main object container for all player relevant functions and checks.
        """
        self.grid = []
        self.ships = []
        self.shipsToPlace = ['A1', 'B1', 'S1', 'S2', 'S3', 'C1', 'D1', 'D2', 'P1', 'P2']

        self.enemyGrid = []

    def Generation(self):
        """Generates the board, containing the cells, and beginning the ship placement process."""
        for _i in range(10):
            _x = chr(65 + _i)
            for _y in range(1, 11):
                self.grid.append(Cell(_x+str(_y)))
                self.enemyGrid.append(Cell(_x+str(_y)))
        print(self)

        for ship in self.shipsToPlace:
            self.PlaceShip(ship)

    def PlaceShip(self, code):
        """Prompts the user to place a ship, verifying it's placement with previously placed ships.
        @param code: The ID code reference for the ship.
        """
        _name = shipDictionary.get(code[0]).get('Name')
        _length = shipDictionary.get(code[0]).get('Size')
        _pos = input(f"Place your {_name} #{code[1]} (Size: {_length}) using 'A1' to 'J10' > ").upper()
        while not validationCheck(_pos)[0]:
            print(f"{validationCheck(_pos)[1]}! Please Try Again.")
            _pos = input(f"Place your {_name} #{code[1]} > ").upper()
        _ori = input(f"Do you want to place your {_name} Horizontally? [Y/N] > ").upper()
        while _ori not in ['Y', 'N', 'YES', 'NO']:
            _ori = input("Please type either 'Y' or 'N' >").upper()
        if _ori in ['Y', 'YES']:
            _ori = True
        else:
            _ori = False

        x, y = self.CheckPositions(_pos, _ori, _length)
        if not x:
            print(f"Unable to place your ship, {y}!")
            self.PlaceShip(code)
        else:
            self.ships.append(Ship(self, code, self.CheckPositions(_pos, _ori, _length)[1]))
            print(self)

    def AttackCheck(self, _string):
        """Checks an individual position for a ship, will refactor later for hit/miss
        @param _string: Position Identifier, such as 'A1' to 'J10'
        @return: Returns True if the position-checked Cell contains a ship, returns the ship instance too
        """
        _pos = int(str(ord(_string[0].upper()) - 65) + str(int(_string[1:]) - 1))
        # Converts position string into a cell position, eg; C2 becomes 21
        if self.grid[_pos].owner is not None:
            self.grid[_pos].state = 0
            self.grid[_pos].owner.lives = self.grid[_pos].owner.lives - 1
            return True, self.grid[_pos].owner
        else:
            return False, self.grid[_pos].owner

    def EndStateCheck(self):
        """Checks if game over conditions are met.
        @return: Returns True if all ships are destroyed. Returns False if a ship is still alive.
        """
        for ship in self.ships:
            if ship.lives > 0:
                return False
        return True

    def Guess(self, _string, isHit):
        """Takes the player's last known guess visually represents it on the enemy board."""
        _pos = int(str(ord(_string[0]) - 65) + str(int(_string[1:]) - 1))
        if isHit:
            self.enemyGrid[_pos].state = 0
        else:
            self.enemyGrid[_pos].state = 3

    def CheckPositions(self, _string, _orientation, _length):
        """Checks several positions based on the position, orientation and length of the user's choice, to allow for
        ship placement.
        @return: Returns True if the ship can be placed in those spaces, along with an array containing the spaces to
         pass onto the ship object during it's creation. False if it cannot be placed in any of the positions, letting
         the user know exactly which ship it overlaps with."""
        success_array = []
        _pos = [int(str(ord(_string[0]) - 65)), int(str(int(_string[1:]) - 1))]
        if _orientation:
            if (_pos[1] + _length) > 10:
                return False, "Out of bounds"
            for i in range(_length):
                _p = int(str(_pos[0]) + str(_pos[1]+i))
                if self.grid[_p].owner is not None:
                    return False, f"Cannot overlap with {self.grid[_p].owner.code}"
                else:
                    success_array.append(_p)
            return True, success_array
        else:
            if (_pos[0] + _length) > 10:      # if (_pos[0] % 10) > _length+1
                return False, "Out of bounds"
            for i in range(_length):
                _p = int(str(_pos[0]+i) + str(_pos[1]))
                if self.grid[_p].owner is not None:
                    return False, f"Cannot overlap with {self.grid[_p].owner.code}"
                else:
                    success_array.append(_p)
            return True, success_array

    def drawEnemyBoard(self):
        """Draws the enemy grid, visualizing the hits and misses the player has made."""
        s = '\nEnemy Board > \n\n    ╔═[1 ]═[2 ]═[3 ]═[4 ]═[5 ]═[6 ]═[7 ]═[8 ]═[9 ]═[10]═╗    \n[A ]║ '
        for x in range(100):
            if (x % 10 == 0) and (x != 0):
                s += f"║[{chr((65+int((x/10)))-1)} ] \n[{chr(65+int((x/10)))} ]║ "
            if self.enemyGrid[x].state == 0:
                s += f"[XX] "
            elif self.enemyGrid[x].state == 3:
                s += "[OO] "
            else:
                s += "[  ] "
        s += "║[J ] \n    ╚═[1 ] [2 ] [3 ] [4 ] [5 ] [6 ] [7 ] [8 ] [9 ] [10]═╝\n"
        return s

    def __str__(self):
        """Draws the player grid, visualizing their ship placements, along with any hits or misses the enemy has made"""
        s = '\nYour Board > \n\n    ╔═[1 ]═[2 ]═[3 ]═[4 ]═[5 ]═[6 ]═[7 ]═[8 ]═[9 ]═[10]═╗    \n[A ]║ '
        for x in range(100):
            if (x % 10 == 0) and (x != 0):
                s += f"║[{chr((65+int((x/10)))-1)} ] \n[{chr(65+int((x/10)))} ]║ "
            if self.grid[x].owner is not None:
                if self.grid[x].state == 1:
                    s += f"[{self.grid[x].owner.code}] "
                else:
                    s += f"[XX] "
            else:
                s += "[  ] "
        s += "║[J ] \n    ╚═[1 ] [2 ] [3 ] [4 ] [5 ] [6 ] [7 ] [8 ] [9 ] [10]═╝\n"
        return s


class Cell:
    def __init__(self, name):
        """A simple container that can hold a reference of a ship"""
        self.name = name
        self.state = -1      # 0 is destroyed, 1 is active, -1 is empty
        self.owner = None

    def __str__(self):
        return self.name


class Ship:
    def __init__(self, board_reference, code, positions):
        """A ship object to allow for instantiation and relationships between the grid and unique ship instances."""
        self.parent = board_reference
        self.code = code
        self.lives = len(positions)

        for position in positions:
            self.parent.grid[position].owner = self
            self.parent.grid[position].state = 1
