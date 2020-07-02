import subprocess
from platform import system
from version import version_info
from os import system as run
from os import path, remove
from sys import argv
from time import sleep

interpreter = 'python' if system() == 'Windows' else 'python3'
current = None

def read_version():
    global current
    with open('../version', 'r') as f:
        current = version_info(f.read(-1).split('\n'))

def main():
    read_version()
    print(f'Current version: {current}')
    arg = argv[-1] if argv[-1] != 'runner.py' else ''
    server = subprocess.Popen([interpreter, 'server.py', arg])
    t = True
    while server.poll() is None:
        try:
            if path.exists('Ready'):
                remove('Ready')
                t = False
            if path.exists('Reboot'):
                remove('Reboot')
                run("sudo shutdown -r now")
            if path.exists('Restart'):
                remove('Restart')
                if arg == '':
                    arg = '-d'
                else:
                    arg = ''
                server.kill()
                while server.poll() is None:
                    pass
                print(f"Restarting in {'developper' if arg == '-d' else 'background'} mode...")
                server = subprocess.Popen([interpreter, 'server.py', arg])
            if path.exists('KILL'):
                remove('KILL')
                server.kill()
            if path.exists('Update_required'):
                remove('Update_required')
                print('Updated!')
                with open('../version', 'r') as f:
                    tmp = version_info(f.read(-1).split('\n'))
                ret = current.check_against(tmp)
                print(f"Required: {ret}")
                if ret == 0:
                    continue
                if ret == 1 or ret == 3:
                    server.kill()
                    while server.poll() is None:
                        pass
                    server = subprocess.Popen([interpreter, 'server.py', arg])
                    t = True
                    while t:
                        if path.exists('Ready'):
                            remove('Ready')
                            t = False
                            break
                if ret == 2 or ret == 3:
                    while t:
                        pass
                    with open('Refresh', 'w') as f:
                        pass
                if ret == 4:
                    print('Trying to restart')
                    run("sudo shutdown -r now")
                read_version()
                print(f'Current version: {current}')
        except:
            pass
        finally:
            sleep(0.2)

if __name__ == '__main__':
    while True:
        main()
        print('Server killed!')
        ansv = str(input('Do you want to restart the server? ([Y]/N) ') or 'Y')
        if ansv.upper() == 'N':
            break