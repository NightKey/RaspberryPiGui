try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO #pip install git+https://github.com/sn4k3/FakeRPi

from pins import *
from time import sleep
from print_handler import verbose

class controller():

    def __init__(self, door_callback, _initial=None, _inverted=False, _12V=False):
        """Some text"""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(pins.lamp_pin.value, GPIO.OUT, initial=GPIO.LOW)                               #Lamp
        GPIO.setup(pins.tub_pin.value, GPIO.OUT, initial=GPIO.LOW)                                #Bathtub leds
        GPIO.setup(pins.cabinet_pin.value, GPIO.OUT, initial=GPIO.LOW)                            #cabinet leds
        GPIO.setup(pins.fan_controll.value, GPIO.OUT, initial=GPIO.LOW)                           #Fancontroller
        GPIO.setup(pins.red_pin.value, GPIO.OUT)                                                  #Red color
        GPIO.setup(pins.green_pin.value, GPIO.OUT)                                                #Green color
        GPIO.setup(pins.blue_pin.value, GPIO.OUT)                                                 #Blue color
        GPIO.setup(pins._12V.value, GPIO.OUT, initial=GPIO.HIGH)                                  #12 V Powersuply
        GPIO.setup(pins.door_pin.value, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)                      #Door switch
        GPIO.add_event_detect(pins.door_pin.value, GPIO.FALLING, door_callback, bouncetime=150)   #Door interrupt
        self.red = GPIO.PWM(pins.red_pin.value, 100)
        self.green = GPIO.PWM(pins.green_pin.value, 100)
        self.blue = GPIO.PWM(pins.blue_pin.value, 100)
        self.inverted = _inverted
        self._12V_=_12V
        self.status = {
            'brightness':0,
            'room':False,
            'bath_tub':False,
            'cabinet':False,
            'color':[0,0,0],
            'fan':False,
            'red':0,
            'green':0,
            'blue':0,
            "rgb":[0,0,0],
            '12V':False,
            'PWM': False
        }
        if _initial != None:
            self.load(_initial)

    def load(self, value):
        if value != None:
            if len(value) == len(self.status):
                value['room'], value['bath_tub'], value['cabinet'], value['fan'] = False, False, False, False
                self.status = value
            self.bath_tub(str(value['bath_tub']).lower())
            self.cabinet(str(value['cabinet']).lower())
            self.room(str(value['room']).lower())

    def read(self, pin, times, delay):
        tmp = 0
        for _ in range(times):
            tmp += GPIO.input(pin)
            sleep(delay)
        return tmp

    def get_status(self, what=None):
        if what == None:
            return self.status
        return self.status[what]

    def _12V(self):
        if self._12V_:
            GPIO.output(pins._12V.value, GPIO.HIGH)
            self.status['12V'] = True

    def check_for_need(self):
        if not self.status['12V']:
            if self.status['room'] or self.status['room'] or self.status['room']:
                GPIO.output(pins._12V.value, GPIO.HIGH)
                self.status['12V'] = True
        else:
            if not self.status['room'] or not self.status['room'] or not self.status['room']:
                GPIO.output(pins._12V.value, GPIO.LOW)
                self.status['12V'] = False

    def get_door_status(self):
        return bool(GPIO.input(pins.door_pin.value))

    def swap_color(self):
        tmp = self.red
        self.red = self.blue
        self.blue = self.green
        self.green = tmp

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
        verbose(f"Incoming for brightness {value}")
        self.status['brightness'] = int(value)
        self.set_leds()

    def set_leds(self):
        try:
            _min = 100 if self.inverted else 0
            _max = 0 if self.inverted else 100
            if self.status['bath_tub'] or self.status['cabinet']:
                if not self.status['PWM']:
                    self.red.start(0)
                    self.green.start(0)
                    self.blue.start(0)
                    self.status['PWM'] = True
                self.red.ChangeDutyCycle(self.translate(self.status["brightness"], -1, 13, _min, _max))
                self.green.ChangeDutyCycle(self.translate(self.status["brightness"], -1, 13, _min, _max))
                self.blue.ChangeDutyCycle(self.translate(self.status["brightness"], -1, 13, _min, _max))
                return
                try:
                    self.status['red'] = self.translate(self.status['color'][0]/self.status['brightness'], 0, 255, _min, _max)
                    if self.status['red'] > 1:
                        self.status['red'] = 1.0/self.status['red']
                except:
                    if self.inverted:
                        self.status['red'] = 100
                    else:
                        self.status['red'] = 0
                finally:
                    self.red.ChangeDutyCycle(self.status['red'])
                try:
                    self.status['green'] = self.translate(self.status['color'][1]/self.status['brightness'], 0, 255, _min, _max)
                    if self.status['green'] > 1:
                        self.status['green'] = 1.0/self.status['green']
                except:
                    if self.inverted:
                        self.status['green'] = 100
                    else:
                        self.status['green'] = 0
                finally:
                    self.green.ChangeDutyCycle(self.status['green'] * 100)
                try:
                    self.status['blue'] = self.translate(self.status['color'][2]/self.status['brightness'], 0, 255, _min, _max)
                    if self.status['blue'] > 1:
                        self.status['blue'] = 1.0/self.status['blue']
                except:
                    if self.inverted:
                        self.status['blue'] = 100
                    else:
                        self.status['blue'] = 0
                finally:
                    self.blue.ChangeDutyCycle(self.status['blue'] * 100)
                self.check_for_need()
            else:
                if self.status['PWM']:
                    self.red.stop()
                    self.green.stop()
                    self.blue.stop()
                    self.status['PWM'] = False
                self.check_for_need()
        except Exception as ex:
            verbose(f"Exception while setting led color: {ex}")

    def set_pwm(self, pin, value):
        pin.ChangeDutyCycle(value)

    def room(self, is_on):
        is_on = (is_on == 'true')
        verbose("The room lights should {}be on!".format('' if (is_on) else 'not '))
        GPIO.output(pins.lamp_pin.value, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['room'] = is_on
        self.check_for_need()

    def bath_tub(self, is_on):
        is_on = (is_on == 'true')
        verbose("The bath tub lights should {}be on!".format('' if (is_on) else 'not '))
        GPIO.output(pins.tub_pin.value, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['bath_tub'] = is_on
        self.set_leds()

    def cabinet(self, is_on):
        is_on = (is_on == 'true')
        verbose("The cabinet lights should {}be on!".format('' if (is_on) else 'not '))
        GPIO.output(pins.cabinet_pin.value, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['cabinet'] = is_on
        self.set_leds()

    def color(self, color_v):
        color_v = color_v.replace('#', '')
        color_v = [int(color_v[:2], 16), int(color_v[2:4], 16), int(color_v[4:], 16)]
        verbose(f"The color of the led's should be #{color_v}")
        self.status['color'] = color_v
        self.set_leds()

    def fan(self, status=None):
        if status == None:
            self.status['fan'] = not self.status['fan']
            status = self.status
        verbose("Fan pin was set to {}".format((GPIO.HIGH if status else GPIO.LOW)))
        GPIO.output(pins.fan_controll.value, (GPIO.HIGH if status else GPIO.LOW))
        self.status['fan'] = status
    
    def clean(self):
        GPIO.cleanup()