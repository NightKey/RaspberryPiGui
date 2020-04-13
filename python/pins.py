class pins():
    """This class contains all of the pin numbers the different things will be connected to.
    """
    def __init__(self):
        self.lamp_pin = 5
        self.cabinet_pin = 7
        self.tub_pin = 6
        self.door_pin = 4
        self.green_pin = 13
        self.red_pin = 12
        self.blue_pin = 23
        self.fan_controll = 19

class encoder():
    """This class contains the rotory encoder's different pin numbers.
    """
    def __init__(self):
        self.turn_left = -1
        self.turn_right = -1
        self.push = -1