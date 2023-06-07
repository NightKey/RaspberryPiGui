from enum import Enum
from time import sleep, time
from typing import List
from serial import Serial
from serial.tools import list_ports
from threading import Thread
from smdb_logger import Logger
from platform import system
from os import path
from os import system as run
import subprocess


class Animation(Enum):
    Homogane = 0
    FlashWithInverted = 1
    Breathing = 2


class ArduinoStatus(Enum):
    Ready = 0
    Updating = 1
    Verifying = 2
    VerificationFailed = 3
    UploadFailed = 4
    NotConnected = 5


class ArduinoReturnCodes(Enum):
    Success = 0
    Build_Or_Upload_Failed = 1
    Sketch_Not_Found = 2
    Invalid_Commandline_Option = 3
    Preference_Does_Not_Exist = 4


class ArduinoException(Exception):
    def __init__(self, return_code: ArduinoReturnCodes, status: ArduinoStatus) -> None:
        self.message = f"Exception in Updating the Arduino board: {status.name}. Return code: {return_code.name.replace('_', ' ')}({return_code.value})"


class ArduinoCLIStatusCode(Enum):
    Completed = 0
    Installed = 1
    Downloaded = 2
    NotInstalled = 3
    CantBeInstalled = 4  # On Windows


class ArduinoCLIStatus:
    cli_install_command = "curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh"
    user_path_file = "~/.bashrc"
    cli_path_origin = "~/arduino-cli"
    cli_path_sub_dir = "bin"
    status_file_path = "../arduinoCLIStatusFile"

    def __init__(self, status_code: ArduinoCLIStatusCode = ArduinoCLIStatusCode.NotInstalled) -> None:
        self.status_code = status_code

    def set_status(self, status_code: ArduinoCLIStatusCode):
        self.status_code = status_code
        self.to_file()

    def __eq__(self, __value: object) -> bool:
        if (isinstance(__value, ArduinoCLIStatusCode)):
            return self.status_code == __value
        if (isinstance(__value, ArduinoCLIStatus)):
            return self.status_code == __value.status_code
        raise ValueError(
            f"Right hand side '{type(__value)}' is not type of 'ArduinoCLIStatus' not 'ArduinoCLIStatusCode'")

    def __ne__(self, __value: object) -> bool:
        return not self == __value

    def to_file(self) -> None:
        with open(ArduinoCLIStatus.status_file_path, 'w') as fp:
            fp.write(str(self.status_code.value))

    @staticmethod
    def from_file() -> "ArduinoCLIStatus":
        cli_status: ArduinoCLIStatus = None
        if (system() == 'Windows'):
            cli_status = ArduinoCLIStatus(ArduinoCLIStatusCode.CantBeInstalled)
        if (not path.exists(ArduinoCLIStatus.status_file_path)):
            cli_status = ArduinoCLIStatus()
        with open(ArduinoCLIStatus.status_file_path, 'r') as fp:
            val = fp.read(-1)
            cli_status = ArduinoCLIStatus(ArduinoCLIStatusCode(int(val)))
        cli_status.to_file()
        return cli_status


class ArduinoController:
    def __init__(self, logger: Logger, minimum_alive_count_over_two_seconds: int = 3, board_type: str = "arduino:avr:micro"):
        self.logger = logger
        self.minimum_alive_count_over_two_seconds = minimum_alive_count_over_two_seconds
        self.alive_timer_miss = 0
        self.run_listener = True
        self.connection_initialized = False
        self.serial_connection = None
        self.serial_to_listen_to = None
        self.color = [0, 0, 0]
        self.brightness = 0
        self.animation = Animation.Homogane
        self.status = ArduinoStatus.NotConnected
        self.board_type = board_type
        self.logger.debug("Creating CLI status")
        self.cli_status = ArduinoCLIStatus.from_file()
        self.listener_status = ArduinoStatus.NotConnected
        if (self.status not in [ArduinoCLIStatusCode.CantBeInstalled, ArduinoCLIStatusCode.Completed]):
            self.logger.debug("Installing CLI")
            self.install_cli()

    def install_cli(self):
        if (self.cli_status == ArduinoCLIStatusCode.Completed):
            return
        if (self.cli_status == ArduinoCLIStatusCode.NotInstalled):
            self.__download_cli()
        if (self.cli_status == ArduinoCLIStatusCode.Downloaded):
            self.__install_cli()
        if (self.cli_status == ArduinoCLIStatusCode.Installed):
            self.__setup_cli()

    def __download_cli(self):
        subprocess.call(
            f"mkdir {ArduinoCLIStatus.cli_path_origin} && cd {ArduinoCLIStatus.cli_path_origin} && {ArduinoCLIStatus.cli_install_command}", shell=True)
        self.cli_status.set_status(ArduinoCLIStatusCode.Downloaded)

    def __install_cli(self):
        with open(ArduinoCLIStatus.user_path_file, "a") as fp:
            fp.write(
                f"\nexport PATH=$PATH:{ArduinoCLIStatus.cli_path_origin}/{ArduinoCLIStatus.cli_path_sub_dir}")
        self.cli_status.set_status(ArduinoCLIStatusCode.Installed)
        run("sudo reboot")

    def __setup_cli(self):
        subprocess.call(["arduino-cli", "config", "init"])
        subprocess.call(["arduino-cli", "core", "install",
                        ":".join(self.board_type.split(":")[:-1])])
        subprocess.call(["arduino-cli", "lib", "install", "FastLED"])
        self.cli_status.set_status(ArduinoCLIStatusCode.Completed)

    def is_available(self):
        return self.status in [ArduinoStatus.Ready, ArduinoStatus.Verifying, ArduinoStatus.Updating]

    def init_connection(self) -> bool:
        try:
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
            if (not self.serial_connection.is_open):
                self.serial_connection.open()
            self.connection_initialized = True
            if (self.serial_connection.is_open):
                self.status = ArduinoStatus.Ready
        except Exception as ex:
            self.logger.warning(
                f"Failed to open the serial connection to the arduino on port {self.serial_to_listen_to}!")
            self.logger.error(f"Exception: {ex}")
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
            try:
                if ((self.connection_initialized and self.connection_initialized is None) or self.status in [ArduinoStatus.Updating, ArduinoStatus.Verifying]):
                    self.listener_status = ArduinoStatus.Updating
                    sleep(2)
                    continue
                elif (self.serial_connection is None or not self.serial_connection.is_open):
                    self.listener_status = ArduinoStatus.NotConnected
                    sleep(10)
                    if (not self.init_connection()):
                        continue
                    self.set_color(*self.color)
                    self.set_brightness(self.brightness)
                    self.set_animation(self.animation)
                self.listener_status = ArduinoStatus.Ready
                if (self.serial_connection.in_waiting >= 5):
                    data = self.serial_connection.read(
                        self.serial_connection.in_waiting)
                    self.serial_connection.reset_input_buffer()
                    data = data.decode("utf-8").strip("\r\n")
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
                        self.status = ArduinoStatus.Ready
                    if self.alive_timer_miss > 5:
                        self.logger.error(
                            f"Arduino alive is not matching set minimum of {self.minimum_alive_count_over_two_seconds}\
                            under two seconds for {self.alive_timer_miss} times")
                        self.status = ArduinoStatus.NotConnected
                        self.run_listener = False
                    count = 0
                    start = time()
            except IOError as ex:
                self.logger.debug(ex)
                self.serial_connection.close()
                self.serial_connection = None
                self.connection_initialized = False
                self.status = ArduinoStatus.NotConnected
                self.logger.info("Arduino disconnected!")

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
        self.brightness = brightness
        self.__send_serial(f'B;{int(brightness):0>3};'.encode('utf-8'))

    def set_animation(self, animation: Animation) -> None:
        self.__send_serial(f'A;{animation.value};'.encode('utf-8'))
        self.animation = animation

    def show(self) -> None:
        self.__send_serial("S;".encode('utf-8'))

    def clear(self) -> None:
        self.__send_serial("R;".encode("utf-8"))
        self.color = [0, 0, 0]

    def __send_serial(self, data: bytes) -> None:
        if self.serial_connection is None or not self.serial_connection.is_open:
            return
        self.serial_connection.write(data)
        self.logger.debug(f"Sending data: {data}")

    def restart_listener(self) -> None:
        self.run_listener = True
        self.start_listener()
        self.show()

    def suspend_serial(self, status: ArduinoStatus = ArduinoStatus.NotConnected) -> None:
        self.logger.info(
            f"Suspending serial communication on port '{self.serial_to_listen_to}'")
        self.status = status
        self.logger.debug("Waiting on listener...")
        while self.listener_status != ArduinoStatus.Updating:
            sleep(1)
        self.serial_connection.close()
        self.logger.debug("Connection closed!")

    def continue_serial(self) -> None:
        self.logger.info(
            f"Continuing serial communication on port '{self.serial_to_listen_to}'")
        if (self.serial_connection is None):
            self.serial_connection = Serial(self.serial_to_listen_to)
        self.serial_connection.open()
        self.status = ArduinoStatus.Ready

    def update_program(self, path_to_folder: str) -> None:
        # Refferences for the update function:
        # - https://github.com/arduino/Arduino/blob/ide-1.5.x/build/shared/manpage.adoc
        # - https://forum.arduino.cc/t/reprograming-arduino-without-ide/325938
        # - https://forum.arduino.cc/t/upload-sketches-directly-from-geany/286641/2
        # Installation URL: https://www.arduino.cc/en/software
        # Installation URL 2: https://siytek.com/arduino-cli-raspberry-pi/
        try:
            self.logger.info("Updating Arduino")
            self.suspend_serial(ArduinoStatus.Verifying)
            arduino_command = f"arduino-cli $ACTION $PORT -b {self.board_type} {path_to_folder}"

            self.run_update(arduino_command.replace(
                "$ACTION", "compile").replace("$PORT ", ""), ArduinoStatus.VerificationFailed)  # arduino-cli compile -b arduino:avr:micro ~/TMP/RaspberryPiGui_Arduino/ArduinoScetch

            self.status = ArduinoStatus.Updating
            self.run_update(arduino_command.replace(
                "$ACTION", "upload").replace("$PORT", f"-p {self.serial_to_listen_to}"), ArduinoStatus.UploadFailed)  # arduino-cli upload -p /dev/ttyACM0 -b arduino:avr:micro ~/TMP/RaspberryPiGui_Arduino/ArduinoScetch

        except ArduinoException as AEx:
            self.logger.error(AEx)
        finally:
            self.continue_serial()

    def run_update(self, string: str, fail_status: ArduinoStatus) -> None:
        self.logger.info(f"Running command: {string}")
        return_code = subprocess.call(string.split(" "))
        if return_code != 0:
            raise ArduinoException(
                ArduinoReturnCodes(return_code), fail_status)

    def close_connection(self) -> None:
        self.run_listener = False
        self.th.join()
        self.serial_connection.close()


if __name__ == "__main__":
    logger = Logger(".TEST.log", clear=True,
                    level="DEBUG", log_to_console=True)
    test = ArduinoController(logger)
    test.init_connection()
    logger.header("Listener start")
    test.start_listener()
    try:
        while True:
            sleep(1)
    finally:
        test.close_connection()
