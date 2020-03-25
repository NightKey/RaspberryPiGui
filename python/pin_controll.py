try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO

import pins
from time import sleep
from print_handler import verbose

pins = pins.pins()

class controller():

    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(pins.lamp_pin, GPIO.OUT, initial=GPIO.LOW)            #Lampa
        GPIO.setup(pins.tub_pin, GPIO.OUT, initial=GPIO.LOW)             #Furdokad
        GPIO.setup(pins.cabinet_pin, GPIO.OUT, initial=GPIO.LOW)         #Szekreny
        GPIO.setup(pins.door_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   #Ajto kapcsolo
        GPIO.setup(pins.red_pin, GPIO.OUT)                               #Red color
        GPIO.setup(pins.green_pin, GPIO.OUT)                             #Green color
        GPIO.setup(pins.blue_pin, GPIO.OUT)                              #Blue color
        GPIO.setup(pins.fan_controll, GPIO.OUT)                          #Fancontroller
        self.red = GPIO.PWM(pins.red_pin, 60)
        self.green = GPIO.PWM(pins.green_pin, 60)
        self.blue = GPIO.PWM(pins.blue_pin, 60)
        self.status = {
            'brightness':0,
            'room':False,
            'bath_tub':False,
            'cabinet':False,
            'color':[0,0,0],
            'fan':False
        }
        self.update_status()

    def get_door_status(self):
        return GPIO.input(pins.door_pin)

    def get_status(self, what):
        return self.status[what]

    def update_status(self):
        self.status['room'] = GPIO.input(pins.lamp_pin)
        self.status['bath_tub'] = GPIO.input(pins.tub_pin)
        self.status['cabinet'] = GPIO.input(pins.cabinet_pin)
        self.status['fan'] = GPIO.input(pins.fan_controll)


    def brightness(self, value):
        verbose(f"Incoming for brightness {value}", 'PINS')
        self.status['brightness'] = int(value)

    def room(self, is_on):
        is_on = (is_on == 'true')
        verbose("The room lights should {}be on!".format('' if (is_on) else 'not '), 'PINS')
        GPIO.output(pins.lamp_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['room'] = GPIO.input(pins.lamp_pin)

    def bath_tub(self, is_on):
        is_on = (is_on == 'true')
        verbose("The bath tub lights should {}be on!".format('' if (is_on) else 'not '), 'PINS')
        GPIO.output(pins.tub_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['bath_tub'] = GPIO.input(pins.tub_pin)

    def cabinet(self, is_on):
        is_on = (is_on == 'true')
        verbose("The cabinet lights should {}be on!".format('' if (is_on) else 'not '), 'PINS')
        GPIO.output(pins.cabinet_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['cabinet'] = GPIO.input(pins.cabinet_pin)


    def color(self, color_v):
        color_v = color_v.replace('#', '')
        color_v = [int(color_v[:2], 16), int(color_v[2:4], 16), int(color_v[4:], 16)]
        verbose(f"The color of the led's should be #{color_v}", 'PINS')
        self.status['color'] = color_v

    def fan(self, status=None):
        if status == None:
            self.status['fan'] = not self.status['fan']
            status = self.status
        verbose("Fan pin was set to {}".format((GPIO.HIGH if status else GPIO.LOW)), 'PINS')
        GPIO.output(pins.fan_controll, (GPIO.HIGH if status else GPIO.LOW))
        self.status['fan'] = GPIO.input(pins.fan_controll)
    
    def clean(self):
        GPIO.cleanup()