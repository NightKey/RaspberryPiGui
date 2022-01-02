from enum import Enum

class pins(Enum):
    """This class contains all of the pin numbers the different things will be connected to.
    """
    lamp_pin = 5
    cabinet_pin = 7
    tub_pin = 6
    door_pin = 10
    green_pin = 13
    red_pin = 12
    blue_pin = 23
    fan_controll = 19
    _12V = 9

class encoder():
    """This class contains the rotory encoder's different pin numbers.
    """
    def __init__(self):
        self.turn_left = -1
        self.turn_right = -1
        self.push = -1