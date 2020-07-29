import datetime
import os

class logger:
    def __init__(self, name, ram_mode=False):
        """
        Sets up the logger class.
        Input: name - The name of the program being logged, ram_mode - If the logger should be run in ram mode
        Output: Nothing
        Return: Nothing
        """
        self.file = "{}.lg".format(name)
        self.ram_mode = ram_mode
        if self.ram_mode:
            self.buffer = ""
        with open(self.file, "a") as f:
            f.write("OPENED AT {}\n".format(datetime.datetime.now()))     
    def log(self, string, error=False):
        """
        Logs the given event into the file. It can log Errors with an alert part in front of it.
        Input: string - The string to be written out; error - Determines, if the string contains an errorlog or not
        Output: Nothing
        Return: Nothing
        """
        if self.ram_mode:
            if error:
                self.buffer += "---ERROR OCCURED!---\n"
            self.buffer = f"{datetime.datetime.now().time()} - {string}\n"
        else:
            with open(self.file, 'a') as f:
                if error:
                    f.write("---ERROR OCCURED!---\n")
                f.write("{} - {}\n".format(datetime.datetime.now().time(), string))
    def get_buffer(self):
        """
        Returns the buffer, if exists, in an array or returns None
        """
        if self.ram_mode:
            return self.buffer.split('\n')
        else:
            return None
    def close(self):
        """
        Closes the log file.
        """
        with open(self.file, "a") as f:
            if self.ram_mode:
                f.write(self.buffer)
            f.write("CLOSED AT {}\n".format(datetime.datetime.now()))

if __name__ == "__main__":
    log = logger("test")
    log.log("test log")
    log.close()