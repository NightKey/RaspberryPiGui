import writer, inspect
from time import sleep

output = writer.writer()
to_print = []
muted = False
is_verbose = False
def verbose(text, caller=None, end='\n> '):
    """
    Only prints when verbose is set to true    
    """
    if is_verbose:
        if caller is None:
            try:
                caller = f"{inspect.getouterframes(inspect.currentframe().f_back, 2)[1][3]}->{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
            except:
                caller = f"{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
        to_print.append([caller, text, end])

def mute():
    """
    Mutes all output
    """
    global muted
    muted = not muted

def ch_verbose():   #Changes the verbose state
    global is_verbose
    is_verbose = not is_verbose
    printer(f'Verbose set to {is_verbose}', 'Main')

def printer(text, caller=None, end='\n> '): 
    """
    Adds the given text and caller to the 'to_print' variable
    """
    global to_print
    if caller is None:
        try:
            caller = f"{inspect.getouterframes(inspect.currentframe().f_back, 2)[1][3]}->{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
        except:
            caller = f"{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
    to_print.append([caller, text, end])

def screen_handler():
    """
    Prints to stdout with a well formated style:
    [CALLER_PARENT/CALLER @ TIME]: text - Output created by writer program
    """
    global to_print
    while True:
        if to_print != []:
            if to_print[0][1] == "!stop":
                print(r'Closing Print function...', end='\n')
                break
            if not muted:
                try:
                    output.write(to_print[0][1], to_print[0][0], end=to_print[0][2])
                except Exception as ex:
                    output.write(f'{type(ex)} --> {ex}', 'Print handler Error')
            del to_print[0]