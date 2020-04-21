from print_handler import printer, screen_handler, verbose
try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO
import asyncio, websockets, logger, threading, sys, os, psutil, pin_controll, updater, usb_player, json
from time import sleep
import print_handler

ws = None
ip="127.0.0.1"
port = 6969
to_send=[]
to_print = []
print = printer
#flags
muted = False
USB_name=None
killswitch = False
tmp_room = False
temp_sent = False
is_connected = False
dev_mode = False

def get_status():
    try:
        controller.update_status()
        temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
        pins = controller.status
        print(f'CPU Temperature: {temp}', 'Main')
        for key, value in pins.items():
            print(f'{key} pin status: {value}', 'Main')
    except Exception as ex:
        print(f'Error in status check: {ex}', 'Main')

def usb_listener():
    print('USB listener started', 'USB')
    USB_Dir = '/media/pi'
    failcount = 0
    global USB_name
    while True:
        try:
            if failcount > 5:
                print('USB listener failed too many times, shutting off.', 'USB')
                break
            drives = os.listdir(USB_Dir)
            if drives != []:
                verbose(f'Drives found: {drives}', 'USB')
                for drive in drives:
                    USB_name = drive
                    controller.load(load())
                    save()
                    verbose(f'USB drive found at {drive}', 'USB')
                    usb_player.start(os.path.join(USB_Dir, drive))
                    to_send.append('music|none')
        except Exception as ex:
            failcount += 1
            if failcount == 3:
                print('Trying test path', 'USB')
                USB_Dir = './test/'
            print(f'Exception: {ex}', 'USB')
        finally:
            if USB_name != None:
                USB_name = None
                controller.load(load())

def temp_checker(test=False):
    global temp_sent
    if not dev_mode:
        try:
            temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
            if temp > 60 and not controller.status['fan']:
                controller.fan(True)
                to_send.append('fan')
            elif temp < 40 and controller.status['fan']:
                controller.fan(False)
                to_send.append('fan')
            if test and not temp_sent:
                temp = 76
            elif test:
                temp = 60
            if temp > 75 and not temp_sent:
                print(f'CPU temp: {temp} C', 'Temp')
                to_send.append('temp')
                temp_sent = True
            elif temp < 70 and temp_sent:
                temp_sent = False
            return False
        except Exception as ex:
            print(ex, 'Temp')
            return True

def update(_=None):
    updater.main()

def timer():
    global tmp_room
    global to_send
    sleep(120)
    verbose('Timer stopped', 'Main')
    if tmp_room:
        verbose('Lights off', 'Main')
        options['room']('false')
        to_send.append('room')
    tmp_room = False

def save():
    _to = USB_name if USB_name != None else 'status'
    controller.update_status()
    status = controller.status
    with open(f"{_to}.json", 'w') as f:
        json.dump(status, f)

async def handler(websocket, path):
    global is_connected
    while True:
        try:
            if killswitch:
                exit()
            global ws
            global tmp_room
            global temp_sent
            ws = websocket
            verbose('Incoming connection', 'Listener')
            is_connected = True
            controller.update_status()
            tmp = controller.status
            color = []
            for item in tmp['color']:
                color.append(hex(item).replace('0x', ''))
                if len(color[-1]) == 1:
                    color[-1] = f"0{color[-1]}"
            verbose(f"Status: {tmp}", 'Listener')
            verbose(f'Colors: {color}', 'Listener')
            if tmp['room']:
                verbose('Sending room', 'Listener')
                await websocket.send('room')
            if tmp['bath_tub']:
                verbose('Sending bath_tub', 'Listener')
                await websocket.send('bath_tub')
            if tmp['cabinet']:
                verbose('Sending cabinet', 'Listener')
                await websocket.send('cabinet')
            if tmp['fan']:
                verbose('Sending fan', 'Listener')
                await websocket.send('fan')
                temp_sent = True
            await websocket.send(f"color|{color}")
            await websocket.send(f"brightness|{tmp['brightness']}")
            await websocket.send(f"volume|{int(usb_player.volume * 100)}")
            await websocket.send("finished")
            await websocket.send(f'music|{usb_player.now_playing}')
            del tmp
            del color
            while True:
                data = await websocket.recv()
                data = data.split(',')
                options[data[0]](data[1])
                if data[0] == "room" and tmp_room:
                    tmp_room = False
                save()
                await ws.send('Accepted')
                if killswitch:
                    exit()
        except Exception as ex:
            log.log('Connection lost')
            log.log(f"Exception: {ex}")
            is_connected = False
            print('Connection lost', 'Listener')
            print(f'Exception: {ex}', 'Listener')

async def message_sender(message):
    verbose(f"Sending message '{message}'", 'Sender')
    await ws.send(message)

def door_callback(arg):
    global tmp_room
    print(arg, 'Main')
    if not controller.get_status("room"):
        to_send.append('room')
        options['room']('true')
        tmp_room = True
        global timer_thread
        timer_thread = threading.Thread(target=timer)
        timer_thread.start()

async def status_checker():
    global to_send
    now_playing = ""
    counter = 0
    temp_failed = False
    while True:
        try:
            if killswitch:
                exit()
            if counter % 10 == 0 and not temp_failed:
                temp_failed = temp_checker()
            if usb_player.playing:
                if now_playing != usb_player.now_playing:
                    now_playing = usb_player.now_playing
                    to_send.append(f'music|{now_playing}')
            if to_send != []:
                if is_connected:
                    try:
                        await message_sender(to_send[0])
                        del to_send[0]
                    except Exception as ex:
                        print(f'Error in sending message: {ex}', 'Sender')
            counter += 1
            if counter > 100:
                counter = 0
        except Exception as ex:
            log.log(f'Status checker Exception: {ex}', True)
            print(f'Exception: {ex}', 'Sender')

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

def _exit():
    global killswitch
    log.log("Stopped by user")
    killswitch = True
    listener_loop.stop()
    sender_loop.stop()

def developer_mode():
    if temp_sent:
        controller.fan(False)
        to_send.append('fan')
        print('Fan stopped!', 'Main')
    print('--------LOG--------', 'Main')
    with open("RaspberryPiServerLog.lg", 'r') as f:
        tmp = f.read(-1)
    tmp = tmp.split('\n')
    for line in tmp[-7:-1]:
        print(line, 'Main')
    print('------LOG END------', 'Main')
    del tmp

def help():
    text = """Avaleable commands:
developer - Disables the fan pin, and prints the last 5 element of the logs
exit - Stops the server
help - This help message
mute - mutes the server output (to the console)
status - Reports about the pin, and temperature status
update - update from github (restarts the system)
verbose - Prints more info from runtime"""
    print(text, 'Main')

def load():
    _from = USB_name if USB_name != None else 'status'
    if os.path.exists(f"{_from}.json"):
        with open(f"{_from}.json", 'r') as s:
            status = json.load(s)
        return status
    else:
        print('No status was saved!', 'Main')
        return None

if __name__=="__main__":
    update()
    #Global functions
    controller = pin_controll.controller(door_callback, load())
    listener_loop = asyncio.new_event_loop()
    sender_loop = asyncio.new_event_loop()
    log = logger.logger("RaspberryPiServerLog")
    #Global functions end
    #Option switch board
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
        'prev': usb_player.prev
        }
    #Option switch board end
    #Menu
    menu = {
        "developer":developer_mode,
        "exit":_exit,
        'help':help, 
        'status':get_status, 
        "mute":print_handler.mute, 
        "update":update, 
        'verbose':print_handler.ch_verbose
    }
    #Menu end
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
        while not killswitch:
            text = input()
            try:
                if ' ' in text:
                    menu[text.split(' ')[0]](text.split(' ')[1])
                else:
                    menu[text]()
            except KeyError as ke:
                print("It's not a valid command!", 'Main')
        sys.exit(0)
    except Exception as ex:
        log.log(str(ex), True)
    finally:
        log.close()