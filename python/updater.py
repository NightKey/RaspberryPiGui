from os import system as run
import os


def main():
    if os.path.exists('RaspberryPiServerLog.lg'):
        os.rename('RaspberryPiServerLog.lg', '/tmp/RaspberryPiServerLog.lg')
    update()
    if os.path.exists('/tmp/RaspberryPiServerLog.lg'):
        os.rename('/tmp/RaspberryPiServerLog.lg', 'RaspberryPiServerLog.lg')

def update():
    run('git pull > update.lg')
    with open('update.lg', 'r') as f:
        c = f.read(-1).split('\n')
    os.remove('update.lg')
    if len(c) > 2:
        run('sudo shutdown -r now')

if __name__=='__main__':
    main()