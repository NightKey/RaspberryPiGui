class writer():
    """Writes out the given input to the screen, with some formatting.
    The caller is the name of the caller program, or whatever was given in the init phase.
    """
    import os
    
    def __init__(self, caller):
        self.caller = caller
    
    def write(self, txt, dest=os.sys.stdout, end='\n'):
        from datetime import datetime
        dest.write("\r[{} @ {}]: {}{}".format(self.caller.upper(), datetime.now(), txt, end))