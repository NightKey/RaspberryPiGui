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

        GPIO.setup(pins.lamp_pin, GPIO.OUT, initial=GPIO.HIGH)            #Lampa
        GPIO.setup(pins.tub_pin, GPIO.OUT, initial=GPIO.HIGH)             #Furdokad
        GPIO.setup(pins.cabinet_pin, GPIO.OUT, initial=GPIO.HIGH)         #Szekreny
        GPIO.setup(pins.door_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   #Ajto kapcsolo
        GPIO.setup(pins.red_pin, GPIO.OUT)                               #Red color
        GPIO.setup(pins.green_pin, GPIO.OUT)                             #Green color
        GPIO.setup(pins.blue_pin, GPIO.OUT)                              #Blue color
        GPIO.setup(pins.fan_controll, GPIO.OUT)                          #Fancontroller
        self.red = GPIO.PWM(pins.red_pin, 100)
        self.green = GPIO.PWM(pins.green_pin, 100)
        self.blue = GPIO.PWM(pins.blue_pin, 100)
        self.red.start(0)
        self.green.start(0)
        self.blue.start(0)
        self.status = {
            'brightness':0,
            'room':False,
            'bath_tub':False,
            'cabinet':False,
            'color':[0,0,0],
            'fan':False,
            'red':0,
            'green':0,
            'blue':0
        }
        self.update_status()

    def get_door_status(self):
        return GPIO.input(pins.door_pin)

    def get_status(self, what):
        return self.status[what]

    def update_status(self):
        self.status['room'] = not bool(GPIO.input(pins.lamp_pin))
        self.status['bath_tub'] = not bool(GPIO.input(pins.tub_pin))
        self.status['cabinet'] = not bool(GPIO.input(pins.cabinet_pin))
        self.status['fan'] = not bool(GPIO.input(pins.fan_controll))

    def translate(self, value, inmin, inmax, outmin, outmax):
        """
        Translates the value from range inmin - inmax into the range outmin - outmax. Returns an integer!
        Input: Value - The value to be translated; inmin, inmax - The input value's minimum, and maximum possible value; outmin, outmax - The return values minimum and maximum possible value.
        Output: Nothing
        Return: Float rounded to 2 digits. The value is between outmin and outmax, and is the translated value of the input value.
        """
        inspan = inmax - inmin
        outspan = outmax - outmin
        scaled = float(value - inmin) / float(inspan)
        return round(outmin + (scaled * outspan), 2)

    def brightness(self, value):
        verbose(f"Incoming for brightness {value}", 'PINS')
        self.status['brightness'] = int(value)
        self.set_leds()

    def set_leds(self):
        try:
            self.status['red'] = (self.translate(self.status['color'][0], 0, 255, 0, 100) / self.translate(self.status['brightness'], 0, 12, 0, 100))
        except:
            self.status['red'] = 0
        finally:
            self.red.ChangeDutyCycle(self.status['red'])
        try:
            self.status['green'] = (self.translate(self.status['color'][1], 0, 255, 0, 100) / self.translate(self.status['brightness'], 0, 12, 0, 100))
        except:
            self.status['green'] = 0
        finally:
            self.green.ChangeDutyCycle(self.status['green'])
        try:
            self.status['blue'] = (self.translate(self.status['color'][2], 0, 255, 0, 100) / self.translate(self.status['brightness'], 0, 12, 0, 100))
        except:
            self.status['blue'] = 0
        finally:
            self.blue.ChangeDutyCycle(self.status['blue'])

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
        if not self.status['cabinet']:
            if not is_on:
                self.red.ChangeDutyCycle(0)
                self.green.ChangeDutyCycle(0)
                self.blue.ChangeDutyCycle(0)
            else:
                self.set_leds()

    def cabinet(self, is_on):
        is_on = (is_on == 'true')
        verbose("The cabinet lights should {}be on!".format('' if (is_on) else 'not '), 'PINS')
        GPIO.output(pins.cabinet_pin, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['cabinet'] = GPIO.input(pins.cabinet_pin)
        if not self.status['bath_tub']:
            if not is_on:
                self.red.ChangeDutyCycle(0)
                self.green.ChangeDutyCycle(0)
                self.blue.ChangeDutyCycle(0)
            else:
                self.set_leds()

    def color(self, color_v):
        color_v = color_v.replace('#', '')
        color_v = [int(color_v[:2], 16), int(color_v[2:4], 16), int(color_v[4:], 16)]
        verbose(f"The color of the led's should be #{color_v}", 'PINS')
        self.status['color'] = color_v
        self.set_leds()

    def fan(self, status=None):
        if status == None:
            self.status['fan'] = not self.status['fan']
            status = self.status
        verbose("Fan pin was set to {}".format((GPIO.HIGH if status else GPIO.LOW)), 'PINS')
        GPIO.output(pins.fan_controll, (GPIO.HIGH if status else GPIO.LOW))
        self.status['fan'] = GPIO.input(pins.fan_controll)
    
    def clean(self):
        GPIO.cleanup()