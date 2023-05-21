import json
from typing import Union


class Configuration:
    def __init__(self, ip: str, port: int, board_name: Union[str, None], path_to_arduino_IDE: Union[str, None], path_to_arduino_project: Union[str, None]):
        self.ip = ip
        self.port = port
        self.can_update_arduino = board_name is not None and path_to_arduino_IDE is not None and path_to_arduino_project is not None
        self.board_name = board_name
        self.path_to_arduino_IDE = path_to_arduino_IDE
        self.path_to_arduino_project = path_to_arduino_project

    def load() -> "Configuration":
        with open("..\config.conf", "r") as fp:
            data = json.load(fp)
        return Configuration(data["ip"], data["port"], data["board name"], data["path to arduino IDE"], data["path to arduino project"])