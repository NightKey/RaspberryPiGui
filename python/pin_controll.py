try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO

import pins
from time import sleep

pins = pins.pins()

class controller():

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(pins.lamp_pin, GPIO.OUT, initial=GPIO.LOW)            #Lampa
        GPIO.setup(pins.tub_pin, GPIO.OUT, initial=GPIO.LOW)             #Furdokad
        GPIO.setup(pins.cabinet_pin, GPIO.OUT, initial=GPIO.LOW)         #Szekreny
        GPIO.setup(pins.door_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)     #Ajto kapcsolo
        GPIO.setup(pins.red_pin, GPIO.OUT)                               #Red color
        GPIO.setup(pins.green_pin, GPIO.OUT)                               #Green color
        GPIO.setup(pins.blue_pin, GPIO.OUT)                               #Blue color
        self.red = GPIO.PWM(pins.red_pin, 60)
        self.green = GPIO.PWM(pins.green_pin, 60)
        self.blue = GPIO.PWM(pins.blue_pin, 60)
        self.status = {
            'brightness':0,
            'room':False,
            'bath_tub':False,
            'cabinet':False,
            'color':[0,0,0]
        }

    def get_door_status(self):
        return GPIO.input(pins.door_pin)

    def get_status(self, what):
        return self.status[what]

    def brightness(self, value):
        print(f"Incoming for brightness {value}", 'Listener')

    def room(self, is_on):
        is_on = (is_on == 'true')
        print("The room lights should {}be on!".format('' if (is_on) else 'not '), 'Listener')
        GPIO.output(pins.lamp_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['room'] = is_on

    def bath_tub(self, is_on):
        is_on = (is_on == 'true')
        print("The bath tub lights should {}be on!".format('' if (is_on) else 'not '), 'Listener')
        GPIO.output(pins.tub_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['room'] = is_on

    def cabinet(self, is_on):
        is_on = (is_on == 'true')
        print("The cabinet lights should {}be on!".format('' if (is_on) else 'not '), 'Listener')
        GPIO.output(pins.cabinet_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['room'] = is_on


    def color(self, color_v):
        color_v = color_v.replace('#', '')
        color_v = [int(color_v[:2], 16), int(color_v[2:4], 16), int(color_v[4:], 16)]
        print(f"The color the led's should be is #{color_v}", 'Listener')
        self.status['color'] = color_v