from os import system as run
from os import remove
import urllib.request
import urllib.parse
import urllib.error
from version import version_info


def check_version(current: version_info) -> bool:
    url = r"https://raw.githubusercontent.com/NightKey/RaspberryPiGui/master/version"
    response = urllib.request.urlopen(url)
    version = version_info(response.read().decode('UTF-8').split('\n'))
    if (current.check_against(version) > 0):
        return True
    else:
        return False


# Trys to download an update, and alerts the runner, if the update was successfull
def update(current: version_info):
    if (not check_version(current)):
        return
    run('git pull > update.lg')
    with open('update.lg', 'r') as f:
        c = f.read(-1).split('\n')
    remove('update.lg')
    if len(c) > 2:
        with open('Update_required', 'w') as f:
            pass


if __name__ == '__main__':
    update()
