from enum import Enum


class pins(Enum):
    """This class contains all of the pin numbers the different things will be connected to.
    """
    lamp_pin = 5
    cabinet_pin = 7
    tub_pin = 6
    door_pin = 10
    chassis_fan = 19
    cpu_fan = 26
    _12V = 9
