import asyncio
import websockets
from websockets.legacy.server import WebSocketServerProtocol
from smdb_logger import Logger, LEVEL
from pins import pins
from version import version_info
import threading
import os
import psutil
import pin_controll
import updater
import usb_player
import json
from time import sleep
from datetime import datetime, timedelta
from config import Configuration
from os import path, remove

ws = None
config: Configuration = None
to_send = []
to_print = []
File_Folder = "/var/RPS"
if os.name == "nt":
    File_Folder = "E:/Windows_stuff/var/RPS"  # Change for your prefered log folder
logger = Logger("RaspberryPiServerLog.log", File_Folder, level=LEVEL.INFO,
                storage_life_extender_mode=True, max_logfile_size=200, max_logfile_lifetime=730, use_caller_name=True, use_file_names=True, log_to_console=True)
temp_logger = Logger("Temperatures.log", storage_life_extender_mode=True,
                     max_logfile_size=200, max_logfile_lifetime=730, use_caller_name=True, use_file_names=True, log_to_console=False)
# flags
last_activity = last_updated = datetime.now()
clock_showing = True
muted = False
manual_room = True
USB_name = None
killswitch = False
tmp_room = False
temp_sent = False
is_connected = False
dev_mode = False
door_ignore_flag = False
door_manual_ignore_flag = False
door_wait_timer = 1  # Time to wait after detecting a falling edge in the door sensore
door_open = False


def periodic_flusher():
    logger.debug("Flushed!")
    logger.flush_buffer()
    new_timer = threading.Thread(target=timer, args=[7200, periodic_flusher])
    new_timer.name = "Periodic flush timer"
    new_timer.start()


def temp_flusher():
    logger.debug("Flushed!")
    temp_logger.flush_buffer()
    new_timer = threading.Thread(target=timer, args=[14800, temp_flusher])
    new_timer.name = "Periodic flush timer"
    new_timer.start()


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
                logger.warning(
                    'USB listener failed too many times, shutting off.')
                break
            drives = os.listdir(USB_Dir)
            if drives != []:
                logger.debug(f'Drives found: {drives}')
                for drive in drives:
                    USB_name = drive
                    controller.load(load())
                    save()
                    logger.debug(f'USB drive found at {drive}')
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
            temp = psutil.sensors_temperatures(
            )['cpu-thermal'][0]._asdict()['current']
            temp_logger.info(temp)
            if temp > 85:
                os.system("shutdown")
            if temp > 70:
                controller.fan(True, pins.cpu_fan)
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
    updater.update(version)
    if (config.can_update_arduino):
        logger.info("Arduino can be updated")
        if updater.update_arduino(config.path_to_arduino_project):
            controller.arduino.update_program(config.path_to_arduino_project)
    logger.info("Update finished")


def timer(time, to_call, _with=None):
    print('Timer started')
    sleep(time)
    print(
        f'Timer finished, calling {to_call.__name__} with the following value {_with}')
    if _with == None:
        to_call()
    else:
        to_call(_with)


def save():
    _to = USB_name if USB_name != None else 'status'
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
        logger.debug('Lights off')
        controller.room('false')
        door_ignore_flag = True
        to_send.append('room')
        to_send.append('close')
        sleep(1)
        tmp_room = False
        logger.debug("tmp_room set to false count down finished")
        manual_room = False


def rgb(values):
    logger.debug(f"RGB was called with '{values}' values.")
    rgb = values.split(',')
    pins = [controller.red, controller.green, controller.blue]
    for value, pin in zip(rgb, pins):
        try:
            controller.set_pwm(pin, int(value))
        except Exception as ex:
            print(f'Falied with the value: {value}')
            logger.debug(f'Exception: {ex}')


async def handler(websocket: WebSocketServerProtocol, path):
    global is_connected
    global last_activity
    global clock_showing
    external_ip = get_ip()
    try:
        if killswitch:
            exit()
        global ws
        global tmp_room
        global temp_sent
        ws = websocket
        logger.debug('Incoming connection')
        is_connected = True
        tmp = controller.status
        color = tmp['rgb']
        logger.debug(f"Status: {tmp}")
        logger.debug(f'Colors: {color}')
        if tmp['room']:
            logger.debug('Sending room')
            await websocket.send('room')
        if tmp['bath_tub']:
            logger.debug('Sending bath_tub')
            await websocket.send('bath_tub')
        if tmp['cabinet']:
            logger.debug('Sending cabinet')
            await websocket.send('cabinet')
        if tmp['fan']:
            logger.debug('Sending fan')
            await websocket.send('fan')
            temp_sent = True
        await websocket.send(f"color|{color}")
        await websocket.send(f"brightness|{tmp['brightness']}")
        await websocket.send(f"volume|{int(usb_player.volume * 100)}")
        await websocket.send("finished")
        await websocket.send(f'music|{usb_player.now_playing}')
        await websocket.send(f'ip|{external_ip}')
        await websocket.send(f'version|{version}')
        await websocket.send(f'door|{"ignored" if door_manual_ignore_flag else "checked"}')
        del tmp
        del color
        while True:
            data = await websocket.recv()
            last_activity = datetime.now()
            logger.debug(f'Data retreaved: {data}')
            if data == 'keep lit':
                tmp_room = False
                logger.debug("tmp_room set to false, got message 'keep lit'")
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
        logger.error('Connection lost')
        logger.error(f"Exception: {ex}")
        is_connected = False
        print('Connection lost')
        print(f'Exception: {ex}')


async def message_sender(message):
    logger.debug(f"Sending message '{message}'")
    await ws.send(message)


def door_callback(arg):
    if controller.get_door_status():
        door_close_callback()
    else:
        door_open_callback()


def door_close_callback():
    global door_open
    if not door_open:
        return
    sleep(door_wait_timer)
    if not controller.get_door_status():
        return
    door_open = False


def door_open_callback():
    global tmp_room
    global door_ignore_flag
    global last_updated
    global last_activity
    global door_open
    if door_ignore_flag or door_manual_ignore_flag or door_open:
        return
    sleep(door_wait_timer)
    # Ignores the door, if it was opened/stood open with lights on
    if controller.get_door_status() or controller.status['room'] or controller.status['bath_tub'] or controller.status['cabinet']:
        return
    last_activity = datetime.now()
    wake()
    to_send.append('door')
    door_open = True
    options['room']('true')
    tmp_room = True
    global door_timer_thread
    door_timer_thread = threading.Thread(
        target=timer, args=[60, tmp_room_check])
    door_timer_thread.start()
    print("Timer started")
    door_ignore_flag = True
    if last_updated == None or (datetime.now() - last_updated) > timedelta(hours=1):
        print('Weather updated')
        last_updated = datetime.now()
        to_send.append('update')


def restart(_=None):
    with open('Restart', 'w') as _:
        pass


def reboot(_=None):
    with open('Reboot', 'w') as _:
        pass


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
                        logger.error(f'Error in sending message: {ex}')
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
            logger.error(f'Status checker Exception: {ex}', True)
            print(f'Exception: {ex}')


def sender_starter():
    logger.debug("Sender started")
    asyncio.set_event_loop(sender_loop)
    sender_loop.run_until_complete(status_checker())
    sender_loop.run_forever()
    exit(0)


def listener_starter():
    logger.debug("Listener started")
    asyncio.set_event_loop(listener_loop)
    start_server = websockets.serve(handler, config.ip, config.port)
    listener_loop.run_until_complete(start_server)
    listener_loop.run_forever()
    exit(0)


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
    print(f"The door value is {controller.get_door_status()}")


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


def set_animation(animation):
    controller.animate(int(animation))


def emulate(what):
    things = {
        'door': door_open_callback,
        'room': manual_send,
        'cabinet': manual_send,
        'bath_tub': manual_send,
        'temp': manual_send,
        'fan': fan_emulator,
        'close': manual_send,
        'Refresh': manual_send,
        'update': manual_send
    }
    if what in things:
        things[what](what)
        print('Emulated')
    else:
        print('Not a valid command!')


def room_controll(state):
    logger.debug(f'Room controll called with {state}')
    logger.debug(f'Room current status: {controller.get_status("room")}')
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
        logger.debug(f'Status: {controller.get_status()}')
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
                logger.debug(
                    "tmp_room set to false, lights switched off, with no other lights avaleable")
                controller.room(state)
                return
            to_send.append("room_extend")
            global off_timer_thread
            off_timer_thread = threading.Thread(
                target=timer, args=[30, controller.room, state])
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
        to_send.append(
            'door|ignored' if door_manual_ignore_flag else 'door|checked')


def get_ip():
    import socket
    import sys
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


if __name__ == "__main__":
    version = version_info(
        os.sys.argv[os.sys.argv.index("--version") + 1].split('|'))
    print("Loading configuration")
    config = Configuration.load()
    try:
        print('Server started!')
        periodic_flusher()
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
        # Creating needed folders in /var
        if not os.path.exists(File_Folder):
            os.mkdir(File_Folder)
        # Global functions
        print('Setting up the global functions...')
        controller = pin_controll.controller(
            door_callback, logger, config.board_name, load())
        if load() != None:
            if len(load()) != len(controller.status):
                print("Key error detected, reseting setup...")
        door_open = not controller.get_door_status()
        listener_loop = asyncio.new_event_loop()
        sender_loop = asyncio.new_event_loop()
        # Global functions end
        # Option switch board
        options = {
            'cabinet': controller.cabinet,
            'room': room_controll,
            'brightness': controller.brightness,
            'bath_tub': controller.bath_tub,
            'color': controller.color,
            'update': update,
            'skip': usb_player.skip,
            'pause': usb_player.pause,
            'volume': usb_player.set_volume,
            'prev': usb_player.prev,
            'ignore': sw_ignore,
            'restart': restart,
            'reboot': reboot
        }
        # Option switch board end
        try:
            logger.info("Main thred started!")
            logger.debug('Creating threads...')
            listener = threading.Thread(target=listener_starter)
            sender = threading.Thread(target=sender_starter)
            usb_thread = threading.Thread(target=usb_listener)
            usb_thread.name = 'USB'
            listener.name = "Listener"
            sender.name = "Sender"
            logger.debug('Starting up the threads...')
            listener.start()
            sender.start()
            usb_thread.start()
            logger.info('Server started!')
            temp_flusher()
            if "-d" in os.sys.argv:
                logger.set_level(LEVEL.DEBUG)
            if "-v" in os.sys.argv:
                sender.join()
        except Exception as ex:
            logger.error(str(ex), True)
        finally:
            logger.flush_buffer()
    except Exception as ex:
        logger.error('Main thread error!', True)
        logger.error(f"Exception: {ex}")
        print('Error in loading, trying to update...')
        print(f"Exception: {ex}")
        logger.flush_buffer()
        while True:
            update()
