import writer

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

def verbose(text, sender):
    if is_verbose:
        print(text, sender)

def printer(text, sender):
    global to_print
    to_print.append([sender, text])

def screen_handler():
    global to_print
    while True:
        if to_print != []:
            if not muted:
                try:
                    link[to_print[0][0]](to_print[0][1])
                except Exception as ex:
                    link['Main'](ex)
            del to_print[0]