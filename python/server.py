from print_handler import printer, screen_handler, verbose
try:
    import RPi.GPIO as GPIO
except:
    import FakeRPi.GPIO as GPIO
import asyncio, websockets, logger, threading, sys, os, psutil, pin_controll, updater, usb_player, json
from time import sleep
from datetime import datetime, timedelta
import print_handler, inspect
from os import path, remove

ws = None
ip="127.0.0.1"
port = 6969
to_send=[]
to_print = []
File_Folder = "/var/RPS"
if os.name == "nt":
    File_Folder = "D:/Windows_stuff/var/RPS" #Change for your prefered log folder
log = logger.logger(os.path.join(File_Folder, "RaspberryPiServerLog"), True)
#flags
last_activity = last_updated = datetime.now()
clock_showing = True
muted = False
manual_room = True
USB_name=None
killswitch = False
tmp_room = False
temp_sent = False
is_connected = False
dev_mode = False
door_ignore_flag = False
door_manual_ignore_flag = False

def print_combiner(text, end='\n> ', no_log=False):
    try:
        caller = f"{inspect.getouterframes(inspect.currentframe().f_back, 2)[1][3]}->{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
    except:
        caller = f"{inspect.getouterframes(inspect.currentframe(), 2)[1][3]}"
    caller = caller.replace('<module>', 'Main')
    printer(text, caller, end)
    if not no_log:
        log.log(f'{caller} -> {text}')

print = print_combiner

def get_status():
    try:
        temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
        print(f'CPU Temperature: {temp}')
    except Exception as ex:
        print(f'Error in status check: {ex}')
    try:
        pins = controller.get_status()
        for key, value in pins.items():
            if type(value) is not list:
                print(f'{key} pin status: {value}')
            else:
                if key == 'rgb':
                    print(f'Red pin: {value[0]}%')
                    print(f'Green pin: {value[1]}%')
                    print(f'Blue pin: {value[2]}%')
                else:
                    print(f'{key} is the following: {value}')
    except Exception as ex:
        print(f'Error in status check: {ex}')

def usb_listener():
    print('USB listener started')
    USB_Dir = '/media/pi'
    failcount = 0
    global USB_name
    while True:
        try:
            if killswitch:
                break
            if failcount > 5:
                print('USB listener failed too many times, shutting off.')
                break
            drives = os.listdir(USB_Dir)
            if drives != []:
                verbose(f'Drives found: {drives}')
                for drive in drives:
                    USB_name = drive
                    controller.load(load())
                    save()
                    verbose(f'USB drive found at {drive}')
                    controller._12V()
                    usb_player.start(os.path.join(USB_Dir, drive))
                    controller.check_for_need()
                    to_send.append('music|none')
        except Exception as ex:
            failcount += 1
            if failcount == 3:
                print('Trying test path')
                USB_Dir = './test/'
            print(f'Exception: {ex}')
        finally:
            if USB_name != None:
                USB_name = None
                controller.load(load())
                print('Finally reached!')
                sleep(0.5)

def temp_checker(test=False):
    global temp_sent
    if not dev_mode:
        try:
            temp = psutil.sensors_temperatures()['cpu-thermal'][0]._asdict()['current']
            if temp > 85:
                os.system("shutdown")
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
                print(f'CPU temp: {temp} C')
                to_send.append('temp')
                temp_sent = True
            elif temp < 70 and temp_sent:
                to_send.append('close')
                temp_sent = False
            return False
        except Exception as ex:
            print(ex)
            return True

def update(_=None):
    print('Checking for updates')
    updater.update()

def timer(time, to_call, _with=None):
    print('Timer started')
    sleep(time)
    print(f'Timer finished, calling {to_call.__name__} with the following value {_with}')
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
    global manual_room
    global door_ignore_flag
    if tmp_room:
        verbose('Lights off')
        controller.room('false')
        door_ignore_flag = True
        to_send.append('room')
        to_send.append('close')
        sleep(1)
        tmp_room = False
        verbose("tmp_room set to false count down finished")
        manual_room = False

def rgb(values):
    verbose(f"RGB was called with '{values}' values.")
    rgb = values.split(',')
    pins = [controller.red, controller.green, controller.blue]
    for value, pin in zip(rgb, pins):
        try:
            controller.set_pwm(pin, int(value))
        except Exception as ex:
            print(f'Falied with the value: {value}')
            verbose(f'Exception: {ex}')

async def handler(websocket, path):
    global is_connected
    global last_activity
    global clock_showing
    external_ip = get_ip()
    while True:
        try:
            if killswitch:
                exit()
            global ws
            global tmp_room
            global temp_sent
            ws = websocket
            verbose('Incoming connection')
            is_connected = True
            controller.update_status()
            tmp = controller.status
            color = []
            for item in tmp['color']:
                color.append(hex(item).replace('0x', ''))
                if len(color[-1]) == 1:
                    color[-1] = f"0{color[-1]}"
            verbose(f"Status: {tmp}")
            verbose(f'Colors: {color}')
            if tmp['room']:
                verbose('Sending room')
                await websocket.send('room')
            if tmp['bath_tub']:
                verbose('Sending bath_tub')
                await websocket.send('bath_tub')
            if tmp['cabinet']:
                verbose('Sending cabinet')
                await websocket.send('cabinet')
            if tmp['fan']:
                verbose('Sending fan')
                await websocket.send('fan')
                temp_sent = True
            await websocket.send(f"color|{color}")
            await websocket.send(f"brightness|{tmp['brightness']}")
            await websocket.send(f"volume|{int(usb_player.volume * 100)}")
            await websocket.send("finished")
            await websocket.send(f'music|{usb_player.now_playing}')
            await websocket.send(f'ip|{external_ip}')
            await websocket.send(f'door|{"ignored" if door_manual_ignore_flag else "checked"}')
            del tmp
            del color
            while True:
                data = await websocket.recv()
                last_activity = datetime.now()
                log.log(f'Data retreaved: {data}')
                if data == 'keep lit':
                    tmp_room = False
                    verbose("tmp_room set to false, got message 'keep lit'")
                    continue
                if data == "clock_off":
                    clock_showing = False
                    continue
                data = data.split(',')
                options[data[0]](data[1])
                save()
                await ws.send('Accepted')
                if killswitch:
                    websocket.close()
                    await websocket.wait_closed()
                    exit()
        except Exception as ex:
            websocket.ws_server.unregister(websocket)
            log.log('Connection lost')
            log.log(f"Exception: {ex}")
            is_connected = False
            print('Connection lost')
            print(f'Exception: {ex}')

async def message_sender(message):
    verbose(f"Sending message '{message}'")
    await ws.send(message)

def door_callback(arg):
    global tmp_room
    global door_ignore_flag
    global last_updated
    global last_activity
    print(f"Door callback: {arg} Ignore flag: {door_ignore_flag}")
    if not door_ignore_flag and not door_manual_ignore_flag:
        if controller.status['room'] or controller.status['bath_tub'] or controller.status['cabinet']:  #Ignores the door, if it was opened/stood open with lights on
            return
        last_activity = datetime.now()
        wake()
        to_send.append('door')
        options['room']('true')
        tmp_room = True
        global door_timer_thread
        door_timer_thread = threading.Thread(target=timer, args=[60, tmp_room_check])
        door_timer_thread.start()
        print("Timer started")
        door_ignore_flag = True
        if last_updated == None or (datetime.now() - last_updated) > timedelta(hours=1):
            print('Weather updated')
            last_updated = datetime.now()
            to_send.append('update')

def restart(_=None):
    with open('Restart', 'w') as _: pass

def reboot(_=None):
    with open('Reboot', 'w') as _: pass

def wake():
    global clock_showing
    if clock_showing:
        clock_showing = False
        to_send.append("clock|none")

async def status_checker():
    global to_send
    global door_ignore_flag
    global last_activity
    global clock_showing
    now_playing = ""
    counter = 0
    temp_failed = False
    ignore_time = 0
    while True:
        try:
            if door_ignore_flag:
                if ignore_time <= 300:
                    door_ignore_flag = False
                    ignore_time = 0
                else:
                    ignore_time += 1
            elif ignore_time != 0:
                ignore_time = 0
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
                        log.log(f'Error in sending message: {ex}')
                        print(f'Error in sending message: {ex}')
            counter += 1
            if counter > 100:
                counter = 0
            if path.exists('Refresh'):
                remove('Refresh')
                to_send.append('Refresh')
            if (datetime.now() - last_activity) >= timedelta(minutes=5) and not clock_showing:
                to_send.append("clock|block")
                clock_showing = True
            sleep(0.2)
        except Exception as ex:
            log.log(f'Status checker Exception: {ex}', True)
            print(f'Exception: {ex}')

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
    try:
        if usb_player.now_playing != "none":
            verbose("USB stop calling")
            usb_player.stop()
    except: pass
    listener_loop.stop()
    sender_loop.stop()
    print('!stop')
    log.close()
    with open('KILL', 'w') as _: pass

def developer_mode():
    if temp_sent:
        controller.fan(False)
        to_send.append('fan')
        print('Fan stopped!')
    print('--------LOG START--------', no_log=True)
    for line in log.get_buffer():
        print(line.replace("\n", ''), no_log=True)
    print('------LOG END------', no_log=True)

def help(what=None):
    if what == None:
        text = """Avaleable commands:
developer - Disables the fan pin, and prints the last 5 element of the logs
emulate - Emulates something. Type in 'help emulate' for options
exit - Stops the server
help - This help message
invert - Temporrly inverts the pwm's
mute - Mutes the server output (to the console)
restart - Restart the server, swapping between developper and normal mode
rgb - Set's the rgb pwm values 0-100. The values are given in the following fassion: R,G,B
status - Reports about the pin, and temperature status
swap - Swaps the colors: R = R->B->G->R, G = G->R->B->G, B = B->G->R->B
update - Update from github
vars - Prints all of the global variables
verbose - Prints more info from runtime"""
    elif what == 'emulate':
        text = """Options:
bath_tub - Emulates the bathtub switch turning on/off
cabinet - Emulates the cabinet switch turning on/off
close - Closes the current error/message box shown
door - Emulates a door opening
fan - Turns on/off the raspberry fan
room - Emulates the lighting switch turnong on/off
Refresh - Emulates a refresh request for the webpage (from SD card)
temp - Emulates a high temperature on the pi (only for display)
update - Emulates an update request for the weather bar"""
    else:
        text = f"The selected modul '{what}' has no help page!"
    print(text)

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
            print('Status was incorrect!')
            return None
    else:
        print('No status was saved!')
        return None

def print_vars():
    from inspect import isclass
    tmp = globals()
    for key, value in tmp.items():
        if '__' not in key and key != 'tmp' and key not in ['menu', 'options', 'ws', 'seep', 'item']:
            if isinstance(value, (str, int, bool, list, dict, datetime)) or value is None:
                print(f'{key} = {value}')
            elif isinstance(value, threading.Thread):
                print(f'{key}: {value.is_alive()}')
    del tmp

def invert():
    controller.inverted = not controller.inverted
    print(f'Inverted was set to {controller.inverted}')
    controller.check_for_need

def manual_send(what):
    global to_send
    to_send.append(what)

def fan_emulator(_=None):
    global dev_mode
    dev_mode = not dev_mode
    controller.fan(dev_mode)
    manual_send('fan')

def emulate(what):
    things = {
        'door':door_callback, 
        'room':manual_send, 
        'cabinet':manual_send, 
        'bath_tub':manual_send,
        'temp':manual_send,
        'fan':fan_emulator,
        'close':manual_send,
        'Refresh':manual_send,
        'update':manual_send
        }
    if what in things:
        things[what](what)
        print('Emulated')
    else:
        print('Not a valid command!')

def room_controll(state):
    verbose(f'Room controll called with {state}')
    verbose(f'Room current status: {controller.get_status("room")}')
    global door_ignore_flag
    global manual_room
    global tmp_room
    if state == 'flag_reset':
        door_ignore_flag = False
    if state == "true":
        controller.room(state)
        manual_room = True
        door_ignore_flag = True
    elif controller.status['room']:
        controller.update_status()
        verbose(f'Status: {controller.get_status()}')
        if tmp_room:
            return
        if not manual_room:
            door_ignore_flag = False
            manual_room = True
            return
        if not (controller.get_status("bath_tub") or controller.get_status("cabinet")):
            manual_room = False
            global to_send
            if tmp_room:
                tmp_room = False
                verbose("tmp_room set to false, lights switched off, with no other lights avaleable")
                controller.room(state)
                return
            to_send.append("room_extend")
            global off_timer_thread
            off_timer_thread = threading.Thread(target=timer, args=[30, controller.room, state])
            off_timer_thread.start()
            print('Off timer started')
        else:
            controller.room(state)

def sw_ignore(what):
    if what == 'door':
        global door_manual_ignore_flag
        global to_send
        door_manual_ignore_flag = not door_manual_ignore_flag
        print('Door ignored' if door_manual_ignore_flag else 'Door endabled')
        to_send.append('door|ignored' if door_manual_ignore_flag else 'door|checked')

def get_ip():
    import socket, sys
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    del sys.modules['socket'], sys.modules['sys']
    del socket, sys
    return ip

def killer():
    if controller.get_status('room') or controller.get_status('cabinet') or controller.get_status('bath_tub'):
        death_timer = threading.Thread(target=timer, args=[1800, killer])
        death_timer.name = 'Restarter'
        death_timer.start()
    else:
        reboot()

if __name__=="__main__":
    print_handler_thread = threading.Thread(target=screen_handler)
    print_handler.name = "Printer"
    print_handler_thread.start()
    try:
        print('Server started!')
        update()
        tmp = datetime.now()
        tmp += timedelta(days=1)
        tmp = tmp.replace(hour=1, minute=0, second=0)
        tmp = (tmp - datetime.now()).total_seconds()
        print(f"Creating death timer for {tmp} seconds")
        death_timer = threading.Thread(target=timer, args=[tmp, killer])
        death_timer.name = 'Restarter'
        death_timer.start()
        print(f"Checking the '{File_Folder}' path")
        #Creating needed folders in /var
        if not os.path.exists(File_Folder):
            os.mkdir(File_Folder)
        #Global functions
        print('Setting up the global functions...')
        controller = pin_controll.controller(door_callback, load())
        if load() != None:
            if len(load()) != len(controller.status):
                print("Key error detected, reseting setup...")
        listener_loop = asyncio.new_event_loop()
        sender_loop = asyncio.new_event_loop()
        #Global functions end
        print('Setting up the mappings...')
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
            'prev': usb_player.prev,
            'ignore': sw_ignore,
            'restart':restart,
            'reboot':reboot
            }
        #Option switch board end
        #Menu
        menu = {
            "developer":developer_mode,
            "emulate":emulate,
            "exit":_exit,
            'help':help,
            'swap':controller.swap_color,
            'status':get_status, 
            "mute":print_handler.mute, 
            "update":update, 
            'verbose':print_handler.ch_verbose,
            'vars':print_vars,
            'rgb':rgb,
            'invert':invert,
            'restart':restart
        }
        #Menu end
        try:
            log.log("Main thred started!")
            print('Creating threads...')
            listener = threading.Thread(target=listener_starter)
            sender = threading.Thread(target=sender_starter)
            usb_thread = threading.Thread(target=usb_listener)
            usb_thread.name='USB'
            listener.name = "Listener"
            sender.name = "Sender"
            print('Starting up the threads...')
            listener.start()
            sender.start()
            usb_thread.start()
            lights_command = False
            print('Server started!')
            if "-d" in os.sys.argv:
                with open('Ready', 'w') as f:
                    pass
                while not killswitch:
                    text = input()
                    try:
                        if ' ' in text:
                            menu[text.split(' ')[0]](text.split(' ')[1])
                        else:
                            menu[text]()
                    except KeyError as ke:
                        print("It's not a valid command!")
                log.log('Stopping...')
            elif "-v" in os.sys.argv:
                sender.join()
            else:
                print('!stop')
                sender.join()
        except Exception as ex:
            log.log(str(ex), True)
        finally:
            log.close()
    except Exception as ex:
        log.log('Main thread error!', True)
        log.log(f"Exception: {ex}")
        print('Error in loading, trying to update...')
        print(f"Exception: {ex}")
        while True:
            update()