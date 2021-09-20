import datetime
import os

class logger:
    def __init__(self, name, ram_mode=False, maximum_chunk_size_byte=-1):
        """
        Sets up the logger class.
        Input: 
            name - The name of the program being logged
            ram_mode - If the logger should be run in ram mode
            maximum_chunk_size_byte - The maximum size one log file should take in bytes. If -1 it won't breake the logs into multiple files
        Output: Nothing
        Return: Nothing
        """
        self.file = "{}.lg".format(name)
        self.maximum_chunk_size_byte = maximum_chunk_size_byte
        self.ram_mode = ram_mode
        if self.ram_mode:
            self.buffer = []
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
                self.buffer.append("---ERROR OCCURED!---\n")
            self.buffer.append(f"{datetime.datetime.now().time()} - {string}\n")
        else:
            with open(self.file, 'a') as f:
                if error:
                    f.write("---ERROR OCCURED!---\n")
                f.write("{} - {}\n".format(datetime.datetime.now().time(), string))
        if len(self.buffer) > 500:
            self.dump_buffer()
    def dump_buffer(self):
        with open(self.file, 'a') as f:
            for line in self.buffer:
                f.write(line)
        self.buffer = []
    def get_buffer(self):
        """
        Returns the buffer, if exists, in an array or returns None
        """
        if self.ram_mode:
            return self.buffer
        else:
            return None
    def close(self):
        """
        Closes the log file.
        """
        with open(self.file, "a") as f:
            if self.ram_mode:
                self.dump_buffer()
            f.write("CLOSED AT {}\n".format(datetime.datetime.now()))
    def file_size_check(self):
        """
        Depending on the file size, will archive the old one and create a new one
        """
        if (self.maximum_chunk_size_byte != -1 and os.path.getsize(f"{self.name}.lg") > self.maximum_chunk_size_byte):
            if (os.path.getsize(f"{self.name}.lg") > self.maximum_chunk_size_byte*10):
                os.remove(f"{self.name}.lg")
            else:
                os.rename(f"{self.name}.lg", f"{self.name}-{datetime.date().isoformat()}.lg")
            with open(self.file, "w") as f:
                f.write("OPENED AT {}\n".format(datetime.datetime.now()))

if __name__ == "__main__":
    log = logger("test")
    log.log("test log")
    log.close()