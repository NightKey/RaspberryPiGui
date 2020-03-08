from os import system as run
from os import remove


def main():
    run('git pull --> update.lg')
    with open('update.lg', 'r') as f:
        c = f.read(-1).split('\n')
    remove('update.lg')
    if len(c) > 2:
        run('sudo shutdown -r now')

if __name__=='__main__':
    main()