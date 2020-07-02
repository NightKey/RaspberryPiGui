class writer():
    """Writes out the given input to the screen, with some formatting.
    The caller is the name of the caller program, or whatever was given in the init phase.
    """
    import os

    def write(self, txt, caller, dest=os.sys.stdout, end='\n'):
        from datetime import datetime
        dest.write("\r[{} @ {}]: {}{}".format(caller.upper(), datetime.now(), txt, end))