import writer, inspect
from time import sleep

output = writer.writer()
to_print = []
muted = False
is_verbose = False
def verbose(text, caller=None, end='\n> '):
    if is_verbose:
        if caller is None:
            try:
                caller = f"{inspect.getouterframes(inspect.currentframe().f_back, 2)[1][3]}->{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
            except:
                caller = f"{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
        to_print.append([caller, text, end])

def mute():
    global muted
    muted = not muted

def ch_verbose():
    global is_verbose
    is_verbose = not is_verbose
    printer(f'Verbose set to {is_verbose}', 'Main')

def printer(text, caller=None, end='\n> '):
    global to_print
    if caller is None:
        try:
            caller = f"{inspect.getouterframes(inspect.currentframe().f_back, 2)[1][3]}->{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
        except:
            caller = f"{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
    to_print.append([caller, text, end])

def screen_handler():
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