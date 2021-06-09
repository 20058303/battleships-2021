shipDictionary = {
    "AircraftCarrier": {
        "Code": "A",
        "Quantity": 1,
        "Size": 5
    },
    "BattleShip": {
        "Code": "B",
        "Quantity": 1,
        "Size": 4
    },
    "Submarine": {
        "Code": "S",
        "Quantity": 3,
        "Size": 3
    },
    "Cruiser": {
        "Code": "C",
        "Quantity": 1,
        "Size": 3
    },
    "Destroyer": {
        "Code": "D",
        "Quantity": 2,
        "Size": 2
    },
    "PatrolBoat": {
        "Code": "P",
        "Quantity": 2,
        "Size": 1
    }
}

shipGrid = []

for x in range(10):
    for y in range(10):
        shipGrid.append([x, y])


class Cell:
    def __init__ (self, x, y, code):
        self.x = x
        self.y = y
        self.code = code
        self.destroyed = False

def AddToGrid(x,y, orientation, code):
    pass


def GridDisplay(_):
    s = ""
    for n in range(100):
        if n > 1 and n % 10 == 0:
            s += "\n"
        s += f"[{}]"
    return s


print(shipDictionary.get("AircraftCarrier").get("Size"))
print(GridDisplay(shipGrid))