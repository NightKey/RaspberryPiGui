import asyncio, websockets, writer, logger, threading, sys

log = logger.logger("RaspberryPiServerLog")
main = writer.writer("RaspberryPiServer").write
listener_print = writer.writer("Listener_status").write
sender_print = writer.writer("Sender_status").write
ws = None
ip="127.0.0.1"
port = 6969
to_send=[]
to_print = []
link = {'Listener':listener_print, 'Sender': sender_print, 'Main':main}
muted = False
killswitch = False


listener_loop = asyncio.new_event_loop()
sender_loop = asyncio.new_event_loop()

def screen_handler():
    global to_print
    while True:
        if killswitch:
            break
        if to_print != []:
            if not muted:
                out = link[to_print[0][0]]
                out(to_print[0][1])
            del to_print[0]

def printer(text, sender):
    global to_print
    to_print.append([sender, text])

print = printer

def brightness(value):
    print(f"Incoming for brightness {value}", 'Listener')

def room(is_on):
    is_on = (is_on == 'true')
    print("The room lights should {}be on!".format('' if (is_on) else 'not '), 'Listener')

def bath_tub(is_on):
    is_on = (is_on == 'true')
    print("The bath tub lights should {}be on!".format('' if (is_on) else 'not '), 'Listener')

def cabinet(is_on):
    is_on = (is_on == 'true')
    print("The cabinet lights should {}be on!".format('' if (is_on) else 'not '), 'Listener')

def color(color):
    print(f"The color the led's should be is #{color}", 'Listener')

options = {'cabinet':cabinet, 'room':room, 'brightness':brightness, 'bath_tub':bath_tub, 'color':color}

async def handler(websocket, path):
    try:
        global ws
        ws = websocket
        await websocket.send("Connected!")
        while True:
            data = await websocket.recv()
            data = data.split(',')
            options[data[0]](data[1])
            await ws.send('Accepted')
    except:
        log.log('Connection lost')
        print('Connection lost', 'Listener')

async def message_sender(message):
    print(f"Sending message '{message}'", 'Sender')
    await ws.send(message)

async def status_checker():
    global to_send
    while True:
        if killswitch:
            print('Killswitch', 'Sender')
            break
        if to_send != []:
            await message_sender(to_send[0])
            del to_send[0]
    await message_sender('kill')

def sender_starter():
    log.log("Sender started")
    asyncio.set_event_loop(sender_loop)
    sender_loop.run_until_complete(status_checker())
    sender_loop.run_forever()
    exit(0)

def listener_starter():
    log.log("Listener started")
    asyncio.set_event_loop(listener_loop)
    start_server = websockets.serve(handler, ip, port)
    listener_loop.run_until_complete(start_server)
    listener_loop.run_forever()
    exit(0)

if __name__=="__main__":
    try:        
        log.log("Main thred started!")
        listener = threading.Thread(target=listener_starter)
        sender = threading.Thread(target=sender_starter)
        print_handler = threading.Thread(target=screen_handler)
        listener.name = "Listener"
        sender.name = "Sender"
        print_handler.name = "Printer"
        listener.start()
        sender.start()
        print_handler.start()
        while True:
            text = input()
            if text == 'exit':
                log.log("Stopped by user")
                killswitch = True
                listener_loop.stop()
                sender_loop.stop()
                break
            elif 'send ' in text:
                to_send.append(text.replace("send ", ''))
            elif text == 'mute':
                muted = True
            elif text == 'unmute':
                muted = False
            elif text == 'lights':
                to_send.append('lights')
            elif text == 'help':
                text = """Avaleable commands:
exit - Stops the server
send - Sends a response to the webpage
mute - mutes the server output (to the console)
unmute - unmutes the server output
lights - emulates a dooropening"""
                print(text, 'Main')
        sys.exit(0)
    except Exception as ex:
        log.log(str(ex), True)
    finally:
        log.close()