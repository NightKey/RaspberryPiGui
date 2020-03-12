try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO
import asyncio, websockets, logger, threading, sys, os, psutil, pin_controll, updater, usb_player
from time import sleep
from print_handler import printer, screen_handler, verbose
import print_handler

print = printer

log = logger.logger("RaspberryPiServerLog")
ws = None
ip="127.0.0.1"
port = 6969
to_send=[]
to_print = []
muted = False
killswitch = False
temp_room = False
temp_sent = False

controller = pin_controll.controller()
listener_loop = asyncio.new_event_loop()
sender_loop = asyncio.new_event_loop()

def get_status():
    try:
        temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
        pins = controller.status
        print(f'CPU Temperature: {temp}', 'Main')
        for key, value in pins:
            print(f'{key} pin status: {value}', 'Main')
    except Exception as ex:
        print(f'Error in status check: {ex}', 'Main')

def usb_listener():
    print('USB listener started', 'USB')
    while True:
        try:
            drives = os.listdir('/media/pi')
            verbose(f'Drives found: {drives}', 'USB')
            if drives != []:
                for drive in drives:
                    verbose(f'USB drive found at {drive}', 'USB')
                    to_send.append('music')
                    usb_player.start(os.path.join('/media/pi', drive))
                    to_send.append('music')
        except Exception as ex:
            print(f'Exception: {ex}', 'USB')

def temp_checker(test=False):
    global temp_sent
    try:
        temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
        if test and not temp_sent:
            temp = 76
        elif test:
            temp = 60
        if temp > 75 and not temp_sent:
            print(f'CPU temp: {temp} C', 'Temp')
            to_send.append('temp')
        elif temp < 70 and temp_sent:
            temp_sent = False
        return False
    except Exception as ex:
        print(ex, 'Temp')
        return True

def update(nothing=None):
    updater.main()

options = {
    'cabinet':controller.cabinet, 
    'room':controller.room, 
    'brightness':controller.brightness, 
    'bath_tub':controller.bath_tub, 
    'color':controller.color,
    'update':update,
    'skip':usb_player.skip,
    'pause':usb_player.pause,
    'volume':usb_player.set_volume,
    'prev': usb_player.prev }

def timer():
    global temp_room
    global to_send
    sleep(120)
    verbose('Timer stopped', 'Main')
    if temp_room:
        verbose('Lights off', 'Main')
        options['room']('false')
        to_send.append('room')
    temp_room = False

timer_thread = threading.Thread(target=timer)

async def handler(websocket, path):
    try:
        global ws
        global temp_room
        ws = websocket
        verbose('Incoming connection', 'Listener')
        await websocket.send("Connected!")
        while True:
            data = await websocket.recv()
            data = data.split(',')
            options[data[0]](data[1])
            if data[0] == "room" and temp_room:
                temp_room = False
            await ws.send('Accepted')
    except Exception as ex:
        log.log('Connection lost')
        print('Connection lost', 'Listener')
        print(f'Exception: {ex}', 'Listener')

async def message_sender(message):
    verbose(f"Sending message '{message}'", 'Sender')
    await ws.send(message)

async def status_checker():
    global to_send
    global temp_room
    counter = 0
    temp_failed = False
    while True:
        if killswitch:
            exit()
        if controller.get_door_status() == True and not controller.get_status('room'):
            to_send.append('room')
            options['room']('true')
            temp_room = True
            if not timer_thread.is_alive():
                timer_thread.start()
        if counter % 10 == 0 and not temp_failed:
            temp_failed = temp_checker()
        if to_send != []:
            try:
                await message_sender(to_send[0])
                del to_send[0]
            except Exception as ex:
                print(f'Error in sending message: {ex}', 'Sender')
        counter += 1
        if counter > 100:
            counter = 0

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
        print_handler_thread = threading.Thread(target=screen_handler)
        usb_thread = threading.Thread(target=usb_listener)
        usb_thread.name='USB'
        listener.name = "Listener"
        sender.name = "Sender"
        print_handler.name = "Printer"
        listener.start()
        sender.start()
        print_handler_thread.start()
        usb_thread.start()
        lights_command = False
        while True:
            text = input()
            if text == 'exit':
                log.log("Stopped by user")
                killswitch = True
                listener_loop.stop()
                sender_loop.stop()
                print_handler_thread._stop()
                break
            elif 'send ' in text:
                to_send.append(text.replace("send ", ''))
            elif text == 'mute':
                print_handler.muted = True
            elif text == 'unmute':
                print_handler.muted = False
            elif text == 'lights':
                controller.room('false' if lights_command else 'true')
            elif text == 'room':
                to_send.append('room')
                options['room']('true')
                temp_room = True
            elif text == 'temp':
                temp_checker(test=True)
            elif text == 'update':
                update()
            elif text == 'status':
                get_status()
            elif text == 'verbose':
                print_handler.is_verbose = not print_handler.is_verbose
            elif text == 'help':
                text = """Avaleable commands:
exit - Stops the server
send - Sends a response to the webpage
status - Reports about the pin, and temperature status
mute - mutes the server output (to the console)
unmute - unmutes the server output
lights - turns on/off the lights (if UI doesn't work)
room - emulates a dooropening
temp - simulates high temperatures
update - update from github (restarts the system)
verbose - Prints more info from runtime """
                print(text, 'Main')
        sys.exit(0)
    except Exception as ex:
        log.log(str(ex), True)
    finally:
        log.close()