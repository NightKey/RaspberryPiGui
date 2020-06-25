import writer
from time import sleep

main = writer.writer("RaspberryPiServer").write
listener_print = writer.writer("Listener Status").write
sender_print = writer.writer("Sender Status").write
temp_print = writer.writer('Temp Checker').write
USB = writer.writer('USB Listener').write
PINS = writer.writer('PIN controller').write
link = {'Listener':listener_print, 'Sender': sender_print, 'Main':main, 'Temp':temp_print, 'USB':USB, 'PINS':PINS}
to_print = []
muted = False
is_verbose = False
def verbose(text, sender, end='\n> '):
    if is_verbose:
        to_print.append([sender, text, end])

def mute():
    global muted
    muted = not muted

def ch_verbose():
    global is_verbose
    is_verbose = not is_verbose
    printer(f'Verbose set to {is_verbose}', 'Main')

def printer(text, sender, end='\n> '):
    global to_print
    to_print.append([sender, text, end])

def screen_handler():
    global to_print
    while True:
        if to_print != []:
            if to_print[0][1] == "!stop":
                print(r'Closing Print function...', end='')
                break
            if not muted:
                try:
                    link[to_print[0][0]](to_print[0][1], end=to_print[0][2])
                except Exception as ex:
                    link['Main'](ex)
            del to_print[0]