import subprocess
from platform import system
from version import version_info
from os import system as run
from os import path, remove
from sys import argv
from time import sleep

interpreter = 'python' if system() == 'Windows' else 'python3'
version_file = '../version'


def read_version():
    """
    Reads the version information from the 'version' file, and returns a version info.
    """
    with open(version_file, 'r') as f:
        return version_info(f.read(-1).split('\n'))


def main():
    """
    Main loop that handdles starting the server, and deciding what to do after an update.
    """
    current = read_version()
    print(f'Current version: {current}')
    arg = argv[-1] if argv[-1] != 'runner.py' else ''
    # Creates a child process with the 'server.py' script
    server = subprocess.Popen([interpreter, 'server.py', arg])
    t = True
    while server.poll() is None:  # Works while the child process runs
        try:
            if path.exists('Ready'):  # When the server is ready
                remove('Ready')
                t = False
            if path.exists('Reboot'):  # When the server requires a hardwear reboot
                remove('Reboot')
                run("sudo shutdown -r now")
            # When the server requires a restart changing it's runmode between developper and normal mode
            if path.exists('Restart'):
                remove('Restart')
                if arg == '':
                    arg = '-d'
                else:
                    arg = ''
                server.kill()
                while server.poll() is None:
                    pass
                print(
                    f"Restarting in {'developper' if arg == '-d' else 'background'} mode...")
                server = subprocess.Popen([interpreter, 'server.py', arg])
            if path.exists('KILL'):  # When the server requires to be killed by the runner
                remove('KILL')
                print("Killing the server...")
                server.terminate()
                server.kill()
            if path.exists('Update_required'):  # When an update is downloaded
                remove('Update_required')
                print('Update downloaded!')
                with open(version_file, 'r') as f:  # Reads the updated version into a variable
                    tmp = version_info(f.read(-1).split('\n'))
                ret = current.check_against(tmp)  # Gets the required action
                print(f"Required: {ret}")
                if ret == 0:
                    continue
                if ret == 1 or ret == 3:  # Restarts the server after update
                    server.kill()
                    while server.poll() is None:
                        pass
                    pip_update = subprocess.Popen(
                        [interpreter, '-m', "pip", "install", "-r", "../dependencies.txt"])
                    while pip_update.poll() is None:
                        pass
                    server = subprocess.Popen([interpreter, 'server.py', arg])
                    t = True
                    while t:
                        if path.exists('Ready'):
                            remove('Ready')
                            t = False
                            break
                if ret == 2 or ret == 3:  # Restarts the browser after update
                    while t:
                        pass
                    with open('Refresh', 'w') as f:
                        pass
                if ret == 4:  # Restarts the hardwear after update
                    print('Trying to restart')
                    run("sudo shutdown -r now")
                current = read_version()
                print(f'Current version: {current}')
        except:
            pass
        finally:
            sleep(0.2)


if __name__ == '__main__':
    # Starts the server, while required
    while True:
        main()
        print('Server killed!')
        ansv = str(input('Do you want to restart the server? ([Y]/N) ') or 'Y')
        if ansv.upper() == 'N':
            break
