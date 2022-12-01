from enum import Enum
from time import sleep, time
from typing import List
from serial import Serial
from serial.tools import list_ports
from threading import Thread
from smdb_logger import Logger


class Animation(Enum):
    Homogane = 0
    FlashWithInverted = 1
    Breathing = 2


class ArduinoController:
    def __init__(self, logger: Logger, minimum_alive_count_over_two_seconds: int = 3):
        self.logger = logger
        self.color = []
        self.minimum_alive_count_over_two_seconds = minimum_alive_count_over_two_seconds
        self.alive_timer_miss = 0
        self.run_listener = True
        self.connection_initialized = False
        self.serial_connection = None
        self.serial_to_listen_to = None

    def is_available(self):
        return self.serial_connection is not None and self.serial_connection.is_open

    def init_connection(self) -> bool:
        available_port_data = list_ports.comports()
        for data in available_port_data:
            if "Arduino" in data.description:
                self.serial_to_listen_to = data.device
        if (self.serial_to_listen_to == None):
            self.logger.warning("No arduino port found!")
            return False
        self.logger.debug(
            f"Potential arduino port: {self.serial_to_listen_to}")
        self.serial_connection = Serial(self.serial_to_listen_to)
        try:
            self.serial_connection.open()
            self.connection_initialized = True
        except:
            self.logger.warning(
                f"Failed to open the serial connection to the arduino on port {self.serial_to_listen_to}!")
        finally:
            return self.connection_initialized

    def start_listener(self):
        self.logger.debug("Creating listener thread")
        self.th = Thread(target=self.__listener)
        self.th.name = "Arduino Listener"
        self.th.start()

    def __listener(self):
        start = time()
        count = 0
        while self.run_listener:
            if (self.serial_connection is None or (not self.serial_connection.is_open and self.connection_initialized)):
                sleep(2)
                continue
            elif (self.serial_connection is None or not self.serial_connection.is_open):
                self.init_connection()
            if (self.serial_connection.in_waiting >= 5):
                data = self.serial_connection.read(
                    self.serial_connection.in_waiting)
                self.serial_connection.reset_input_buffer()
                data = data.decode("utf-8").strip("\r\n")
                if (data != "alive"):
                    self.logger.debug(f"Incoming Data: {data}")
                count += 1
                if len(data) < 1:
                    continue
                if data[0] == 'C':
                    tmp = self.__get_rgb(data)
                    for i in range(3):
                        if tmp[i] != self.color[i]:
                            self.logger.error(
                                f"Data missmach in color: {tmp} -> {self.color}")
            if (time() - start > 2):
                if count < self.minimum_alive_count_over_two_seconds:
                    self.alive_timer_miss += 1
                else:
                    self.alive_timer_miss = 0
                if self.alive_timer_miss > 5:
                    self.logger.error(
                        f"Arduino alive is not matching set minimum of {self.minimum_alive_count_over_two_seconds}\
                        under two seconds for {self.alive_timer_miss} times")
                    self.run_listener = False
                count = 0
                start = time()

    def __get_rgb(self, data: str) -> List[int]:
        data = data.split(';')[1:]
        return [int(data[0], 16), int(data[1], 16), int(data[2], 16)]

    def set_color(self, r: int, g: int, b: int) -> bytes:
        self.color = [r, g, b]
        self.__send_serial(
            f"C;{r:0>3};{g:0>3};{b:0>3};".encode('utf-8'))

    def set_brightness(self, brightness: int) -> None:
        if (0 > brightness):
            brightness = 0
        if (brightness > 255):
            brightness = 255
        self.__send_serial(f'B;{int(brightness):0>3};'.encode('utf-8'))

    def set_animation(self, animation: Animation) -> None:
        self.__send_serial(f'A;{animation.value};'.encode('utf-8'))

    def show(self) -> None:
        self.__send_serial("S;".encode('utf-8'))

    def clear(self) -> None:
        self.__send_serial("R;".encode("utf-8"))

    def __send_serial(self, data: bytes) -> None:
        if self.serial_connection is None or not self.serial_connection.is_open:
            return
        self.serial_connection.write(data)
        self.logger.debug(f"Sending data: {data}")

    def restart_listener(self) -> None:
        self.run_listener = True
        self.start_listener()
        self.show()

    def suspend_serial(self) -> None:
        self.serial_connection.close()

    def continue_serial(self) -> None:
        self.serial_connection = Serial(self.serial_to_listen_to)

    def close_connection(self) -> None:
        self.run_listener = False
        self.th.join()
        self.serial_connection.close()
