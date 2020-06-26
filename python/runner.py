import subprocess
from platform import system
from version import version_info
from os import system as run
from os import path, remove

interpreter = 'python' if system() == 'Windows' else 'python3'
current = None

def read_version():
    global current
    with open('../version', 'r') as f:
        current = version_info(f.read(-1).split('\n'))
print(f'Current version: {current}')
server = subprocess.Popen([interpreter, 'server.py'])
while server.poll() is None:
    if path.exists('Ready'):
        remove('Ready')
    if path.exists('Update_required'):
        remove('Update_required')
        print('Updated!')
        with open('../version', 'r') as f:
            tmp = version_info(f.read(-1).split('\n'))
        ret = current.check_against(tmp)
        if ret == 0:
            continue
        if ret == 1 or ret == 3:
            server.kill()
            while server.poll() is None:
                pass
            server = subprocess.Popen([interpreter, 'server.py'])
            t = True
            while t:
                try:
                    for line in server.stdout:
                        if path.exists('Ready'):
                            remove('Ready')
                            t = False
                            break
                except TypeError:
                    pass
        if ret == 2 or ret == 3:
            with open('Refresh', 'w') as f:
                pass
        if ret == 4:
            run("sudo shutdown -r now")
        read_version()
        print(f'Current version: {current}')