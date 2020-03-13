import os
from time import sleep
from datetime import datetime, timedelta
from print_handler import verbose
off_command = 'echo 1 | sudo tee /sys/class/backlight/rpi_backlight/bl_power'
on_command = 'echo 0 | sudo tee /sys/class/backlight/rpi_backlight/bl_power'
last_interacted = datetime.now()
turn_on = False
power_saver_enabled = True

print = verbose

def save_timer():
    tmp = None
    global turn_on
    sleep_time = 0
    screen_off = False
    while power_saver_enabled:
        print(f'Sleep time: {sleep_time}', 'Power')
        print(f'Screen off: {screen_off}', 'Power')
        print(f'tmp: {tmp}', 'Power')
        if tmp >= last_interacted and sleep_time != 0.2:
            os.system(off_command)
            screen_off = True
            sleep_time = 0.2
        elif turn_on and not screen_off:
                os.system(on_command)
                turn_on = False
                sleep_time = 0.2
        else:
            turn_on = False
            sleep_time = (last_interacted + timedelta(0,300) - datetime.now()).total_seconds()
        if sleep_time < 0: 
            sleep_time = 0.2
        print(f'Sleeping {sleep_time} secunds.', 'Power')
        tmp = datetime.now()
        sleep(sleep_time)
    print('Powersaver stopped.', 'Power')

def set_now():
    print('Renewing last activation time.', 'Power')
    wake_up()
    global last_interacted
    last_interacted = datetime.now()

def wake_up():
    print('Screen turned on.', 'Power')
    global turn_on
    turn_on = True

def stop():
    print('Stopping powersaver.', 'Power')
    global power_saver_enabled
    power_saver_enabled = False