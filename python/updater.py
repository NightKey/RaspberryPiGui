from os import system as run
import os


def main():
    if os.path.exists('RaspberryPiServerLog.lg'):
        os.rename('RaspberryPiServerLog.lg', '/tmp/RaspberryPiServerLog.lg')
    if os.path.exists('status.json'):
        os.rename('status.json', '/tmp/status.json')
    c = update()
    if os.path.exists('/tmp/RaspberryPiServerLog.lg'):
        os.rename('/tmp/RaspberryPiServerLog.lg', 'RaspberryPiServerLog.lg')
    if os.path.exists('/tmp/status.json'):
        os.rename('/tmp/status.json', 'status.json')
    if len(c) > 2:
        run('sudo shutdown -r now')

def update():
    run('git pull > update.lg')
    with open('update.lg', 'r') as f:
        c = f.read(-1).split('\n')
    os.remove('update.lg')
    return c

if __name__=='__main__':
    main()