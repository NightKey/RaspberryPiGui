try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO  # pip install git+https://github.com/sn4k3/FakeRPi

from pins import *
from time import sleep
from smdb_logger import Logger
from arduino_connector import ArduinoController, Animation


class controller():

    def __init__(self, door_callback, logger, board_name, _initial=None, _inverted=False, _12V=False):
        self.logger: Logger = logger
        self.arduino = ArduinoController(logger, board_type=board_name)
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(pins.lamp_pin.value, GPIO.OUT,
                   initial=GPIO.LOW)  # Lamp
        GPIO.setup(pins.tub_pin.value, GPIO.OUT,
                   initial=GPIO.LOW)  # Bathtub leds
        GPIO.setup(pins.cabinet_pin.value, GPIO.OUT,
                   initial=GPIO.LOW)  # cabinet leds
        GPIO.setup(pins.chassis_fan.value, GPIO.OUT,
                   initial=GPIO.LOW)  # Fancontroller
        GPIO.setup(pins.cpu_fan.value, GPIO.OUT,
                   initial=GPIO.LOW)  # CPUFan
        GPIO.setup(pins._12V.value, GPIO.OUT,
                   initial=GPIO.HIGH)  # 12 V Powersuply
        GPIO.setup(pins.door_pin.value, GPIO.IN,
                   pull_up_down=GPIO.PUD_DOWN)  # Door switch
        GPIO.add_event_detect(pins.door_pin.value, GPIO.BOTH,
                              door_callback, bouncetime=150)  # Door interrupt
        self.inverted = _inverted
        self._12V_ = _12V
        self.status = {
            'brightness': 0,
            'room': False,
            'bath_tub': False,
            'cabinet': False,
            'fan': False,
            "rgb": [0, 0, 0],
            '12V': False,
            'PWM': False
        }
        self.arduino.init_connection()
        self.arduino.start_listener()
        self.arduino.clear()
        if _initial != None:
            self.load(_initial)
        self.arduino.set_color(
            self.status["rgb"][0], self.status["rgb"][1], self.status["rgb"][2])

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
        self.logger.debug(f"Incoming for brightness {value}")
        brightness = self.translate(int(value), 1, 100, 0, 255)
        self.logger.debug(f"Translated brightness: {brightness}")
        self.status['brightness'] = brightness
        self.arduino.set_brightness(brightness)

    def room(self, is_on):
        is_on = (is_on == 'true')
        self.logger.debug(
            f"The room lights should be {'on' if is_on else 'off'}!")
        GPIO.output(pins.lamp_pin.value, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['room'] = is_on

    def bath_tub(self, is_on):
        is_on = (is_on == 'true')
        self.logger.debug(
            f"The bath tub lights should be {'on' if is_on else 'off'}!")
        GPIO.output(pins.tub_pin.value, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['bath_tub'] = is_on
        self.arduino.show()

    def cabinet(self, is_on):
        is_on = (is_on == 'true')
        self.logger.debug(
            f"The cabinet lights should be {'on' if is_on else 'off'}!")
        GPIO.output(pins.cabinet_pin.value, (GPIO.HIGH if is_on else GPIO.LOW))
        self.status['cabinet'] = is_on
        self.arduino.show()

    def color(self, color_v):
        color_v = color_v.replace('#', '')
        color_v = [int(color_v[:2], 16), int(
            color_v[2:4], 16), int(color_v[4:], 16)]
        self.logger.debug(f"The color of the led's should be #{color_v}")
        self.status['rgb'] = color_v
        self.arduino.set_color(color_v[0], color_v[1], color_v[2])

    def fan(self, status=None, selector=pins.chassis_fan):
        if status == None and selector == pins.chassis_fan:
            self.status['fan'] = not self.status['fan']
            status = self.status['fan']
        self.logger.debug("Fan pin was set to {}".format(
            (GPIO.HIGH if status else GPIO.LOW)))
        self.logger.debug("Selected fan: {}".format(selector.name))
        GPIO.output(selector.value,
                    (GPIO.HIGH if status else GPIO.LOW))
        if selector == pins.chassis_fan:
            self.status['fan'] = status

    def animate(self, animation: int):
        self.arduino.set_animation(Animation(animation))

    def clean(self):
        GPIO.cleanup()
        self.arduino.close_connection()
