try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO
import asyncio, websockets, writer, logger, threading, sys, os, psutil, pin_controll
from time import sleep

log = logger.logger("RaspberryPiServerLog")
main = writer.writer("RaspberryPiServer").write
listener_print = writer.writer("Listener status").write
sender_print = writer.writer("Sender status").write
temp_print = writer.writer('Temp Checker').write
ws = None
ip="127.0.0.1"
port = 6969
to_send=[]
to_print = []
link = {'Listener':listener_print, 'Sender': sender_print, 'Main':main, 'Temp':temp_print}
muted = False
killswitch = False
temp_room = False
temp_sent = False

controller = pin_controll.controller()

listener_loop = asyncio.new_event_loop()
sender_loop = asyncio.new_event_loop()


def temp_checker(test=False):
    global temp_sent
    try:
        temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
        if test and not temp_sent:
            temp = 76
        elif test:
            temp = 60
        if temp > 75 and not temp_sent:
            print(f'CPU temp: {temp}C', 'Temp')
            to_send.append('temp')
        elif temp < 70 and temp_sent:
            temp_sent = False
        return False
    except Exception as ex:
        print(ex, 'Temp')
        return True

def screen_handler():
    global to_print
    while True:
        if killswitch:
            break
        if to_print != []:
            if not muted:
                try:
                    link[to_print[0][0]](to_print[0][1])
                except Exception as ex:
                    link['Main'](ex)
            del to_print[0]

def printer(text, sender):
    global to_print
    to_print.append([sender, text])

print = printer

options = {
    'cabinet':controller.cabinet, 
    'room':controller.room, 
    'brightness':controller.brightness, 
    'bath_tub':controller.bath_tub, 
    'color':controller.color }

def timer():
    global temp_room
    global to_send
    sleep(120)
    print('Timer stopped', 'Main')
    if temp_room:
        print('Lights off', 'Main')
        options['room']('false')
        to_send.append('room')
        temp_room = False

timer_thread = threading.Thread(target=timer)

async def handler(websocket, path):
    try:
        global ws
        global temp_room
        ws = websocket
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
    print(f"Sending message '{message}'", 'Sender')
    await ws.send(message)

async def status_checker():
    global to_send
    global temp_room
    counter = 0
    temp_failed = False
    while True:
        if killswitch:
            print('Killswitch', 'Sender')
            break
        if controller.get_door_status() == True and not controller.get_status('room'):
            to_send.append('room')
            options['room']('true')
            temp_room = True
            if not timer_thread.is_alive():
                timer_thread.start()
        if counter % 10 == 0 and not temp_failed:
            temp_failed = temp_checker()
        if to_send != []:
            await message_sender(to_send[0])
            del to_send[0]
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
        print_handler = threading.Thread(target=screen_handler)
        listener.name = "Listener"
        sender.name = "Sender"
        print_handler.name = "Printer"
        listener.start()
        sender.start()
        print_handler.start()
        lights_command = False
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
                controller.room('false' if lights_command else 'true')
            elif text == 'room':
                to_send.append('room')
                options['room']('true')
                temp_room = True
            elif text == 'temp':
                temp_checker(test=True)
            elif text == 'update':
                import updater
            elif text == 'help':
                text = """Avaleable commands:
exit - Stops the server
send - Sends a response to the webpage
mute - mutes the server output (to the console)
unmute - unmutes the server output
lights - turns on/off the lights (if UI doesn't work)
room - emulates a dooropening
temp - simulates high temperatures
update - update from github (restarts the system)"""
                print(text, 'Main')
        sys.exit(0)
    except Exception as ex:
        log.log(str(ex), True)
    finally:
        log.close()