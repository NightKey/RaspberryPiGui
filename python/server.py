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
print = print_combiner
File_Folder = "/var/RPS"
if os.name == "nt":
    File_Folder = "D:/Windows_stuff/var/RPS" #Change for your prefered log folder
#flags
muted = False
manual_room = True
USB_name=None
killswitch = False
tmp_room = False
temp_sent = False
is_connected = False
dev_mode = False
door_ignore_flag = False

def print_combiner(text, sender, end='\n> '):
    printer(text, sender, end)
    log.log(text)

def get_status():
    try:
        controller.update_status()
        temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
        print(f'CPU Temperature: {temp}', 'Main')
    except Exception as ex:
        print(f'Error in status check: {ex}', 'Main')
    try:
        pins = controller.status
        for key, value in pins.items():
            if type(value) is not list:
                print(f'{key} pin status: {value}', 'Main')
            else:
                if key == 'rgb':
                    print(f'Red pin: {value[0]}%', 'Main')
                    print(f'Green pin: {value[1]}%', 'Main')
                    print(f'Blue pin: {value[2]}%', 'Main')
                else:
                    print(f'{key} is the following: {value}', 'Main')
    except Exception as ex:
        print(f'Error in status check: {ex}', 'Main')

def usb_listener():
    print('USB listener started', 'USB')
    USB_Dir = '/media/pi'
    failcount = 0
    global USB_name
    while True:
        try:
            if killswitch:
                break
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
                    controller._12V()
                    usb_player.start(os.path.join(USB_Dir, drive))
                    controller.check_for_need()
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
                print('Finally reached!', 'USB')
                sleep(0.5)

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
    print('Checking for updates', 'Main')
    updater.update()

def timer(time, to_call, _with=None):
    verbose('Timer started', "Main")
    sleep(time)
    verbose('Timer finished', 'Main')
    if _with == None:
        to_call()
    else:
        to_call(_with)

def save():
    _to = USB_name if USB_name != None else 'status'
    controller.update_status()
    status = controller.status
    status['volume'] = usb_player.volume
    with open(f"{os.path.join(File_Folder, _to)}.json", 'w') as f:
        json.dump(status, f)

def tmp_room_check():
    global tmp_room
    global to_send
    if tmp_room:
        verbose('Lights off', 'Main')
        options['room']('false')
        to_send.append('room')
        to_send.append('close')

def rgb(values):
    verbose(f"RGB was called with '{values}' values.", 'Main')
    rgb = values.split(',')
    pins = [controller.red, controller.green, controller.blue]
    for value, pin in zip(rgb, pins):
        try:
            controller.set_pwm(pin, int(value))
        except Exception as ex:
            print(f'Falied with the value: {value}', 'Main')
            verbose(f'Exception: {ex}', 'Main')

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
                log.log(f'Data retreaved: {data}')
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
    return                  #Remove when good magnetic switch is added
    global tmp_room
    log.log(f'Door signal detected, flag: {door_ignore_flag}')
    print(arg, 'Main')
    if not door_ignore_flag:
        to_send.append('room')
        options['room']('true')
        tmp_room = True
        global timer_thread
        timer_thread = threading.Thread(target=timer, args=[120, tmp_room_check])
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
                        log.log(f'Error in sending message: {ex}', 'Sender')
                        print(f'Error in sending message: {ex}', 'Sender')
            counter += 1
            if counter > 100:
                counter = 0
            sleep(0.2)
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
    if usb_player.now_playing != "none":
        verbose("USB stop calling", 'Main')
        usb_player.stop()
    listener_loop.stop()
    sender_loop.stop()
    print('!stop', "Main")

def developer_mode():
    if temp_sent:
        controller.fan(False)
        to_send.append('fan')
        print('Fan stopped!', 'Main')
    print('--------LOG--------', 'Main')
    with open(os.path.join(File_Folder, "RaspberryPiServerLog.lg"), 'r') as f:
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
invert - temporrly inverts the pwm's
mute - mutes the server output (to the console)
rgb - set's the rgb pwm values 0-100. The values are given in the following fassion: R,G,B
status - Reports about the pin, and temperature status
update - update from github (restarts the system)
vars - Prints all of the global variables
verbose - Prints more info from runtime"""
    print(text, 'Main')

def load():
    _from = USB_name if USB_name != None else 'status'
    if os.path.exists(f"{os.path.join(File_Folder, _from)}.json"):
        try:
            with open(f"{os.path.join(File_Folder, _from)}.json", 'r') as s:
                status = json.load(s)
            usb_player.volume = status["volume"]
            del status["volume"]
            return status
        except:
            print('Status was incorrect!', 'Main')
            return None
    else:
        print('No status was saved!', 'Main')
        return None

def print_vars():
    tmp = globals()
    for key, value in tmp.items():
        if '__' not in key and key != 'tmp' and 'object' not in str(type(value)) and key not in ['menu', 'options', 'ws', 'seep']:
            print(f'{key} = {value}', 'Main')
    del tmp

def invert():
    controller.inverted = not controller.inverted
    print(f'Inverted was set to {controller.inverted}', 'Main')
    controller.check_for_need

def room_controll(state):
    verbose(f'Room controll called with {state}', 'Main')
    verbose(f'Room current status: {controller.status["room"]}', 'Main')
    global timer_thread
    if state == 'flag_reset':
        global door_ignore_flag
        door_ignore_flag = False
    if state == "true":
        controller.room(state)
        global door_ignore_flag
        door_ignore_flag = True
    elif controller.status['room']:
        controller.update_status()
        verbose(f'Status: {controller.get_status()}', 'Main')
        global manual_room
        if not manual_room:
            manual_room = True
            return
        global tmp_room
        if tmp_room:
            tmp_room = False
            return
        if not (controller.get_status("bath_tub") or controller.get_status("cabinet")):
            manual_room = False
            global to_send
            to_send.append("room_extend")
            timer_thread = threading.Thread(target=timer, args=[30, controller.room, state])
            timer_thread.start()
        else:
            controller.room(state)
            timer_thread = threading.Thread(target=timer, args=[5, controller.room, 'flag_reset'])
            timer_thread.start()


if __name__=="__main__":
    print_handler_thread = threading.Thread(target=screen_handler)
    print_handler.name = "Printer"
    print_handler_thread.start()
    try:
        print('Server started!', 'Main')
        update()
        log = logger.logger(os.path.join(File_Folder, "RaspberryPiServerLog"))
        print(f"Checking the '{File_Folder}' path", "Main")
        #Creating needed folders in /var
        if not os.path.exists(File_Folder):
            os.mkdir(File_Folder)
        #Global functions
        print('Setting up the global functions...', 'Main')
        controller = pin_controll.controller(door_callback, load())
        if load() != None:
            if len(load()) != len(controller.status):
                print("Key error detected, reseting setup...", 'Main')
        listener_loop = asyncio.new_event_loop()
        sender_loop = asyncio.new_event_loop()
        #Global functions end
        print('Setting up the mappings...', "Main")
        #Option switch board
        options = {
            'cabinet':controller.cabinet, 
            'room':room_controll, 
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
            'verbose':print_handler.ch_verbose,
            'vars':print_vars,
            'rgb':rgb,
            'invert':invert
        }
        #Menu end
        try:
            log.log("Main thred started!")
            print('Creating threads...', "Main")
            listener = threading.Thread(target=listener_starter)
            sender = threading.Thread(target=sender_starter)
            usb_thread = threading.Thread(target=usb_listener)
            usb_thread.name='USB'
            listener.name = "Listener"
            sender.name = "Sender"
            print('Starting up the threads...', 'Main')
            listener.start()
            sender.start()
            usb_thread.start()
            lights_command = False
            print('Server started!', 'Main')
            if "-d" in os.sys.argv:
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
            elif "-v" in os.sys.argv:
                sender.join()
            else:
                print('!stop', 'Main')
                sender.join()
        except Exception as ex:
            log.log(str(ex), True)
        finally:
            log.close()
    except Exception as ex:
        log.log('Main thread error!', True)
        log.log(f"Exception: {ex}")
        print('Error in loading, trying to update...', "Main")
        print(f"Exception: {ex}", 'Main')
        while True:
            update()