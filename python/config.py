import json
from typing import Optional, Union
from os.path import join, exists


class Configuration:
    def __init__(self, ip: str, port: int, board_name: Optional[str], path_to_arduino_project: Optional[str], file_folder: Optional[str] = "/var/RPS", usb_dir: Optional[str] = "/media/pi"):
        self.ip = ip
        self.port = port
        self.can_update_arduino = board_name is not None and path_to_arduino_project is not None
        self.board_name = board_name
        self.path_to_arduino_project = path_to_arduino_project
        self.file_folder = file_folder
        self.usb_dir = usb_dir

    def load() -> Union["Configuration", None]:
        path = join("..", "config.conf")
        if (not exists(path)):
            return None
        with open(path, "r") as fp:
            data = json.load(fp)
        return Configuration(
            data["ip"],
            data["port"],
            data["board name"],
            data["path to arduino project"],
            data["file folder"] if "file folder" in data else None,
            data["usb dir"] if "usb dir" in data else None
        )
