from os import system as run
from os import remove
from sys import stderr

def update():   #Trys to download an update, and alerts the runner, if the update was successfull
    run('git pull > update.lg')
    with open('update.lg', 'r') as f:
        c = f.read(-1).split('\n')
    remove('update.lg')
    if len(c) > 2:
       with open('Update_required', 'w') as f:
                pass

if __name__=='__main__':
    update()