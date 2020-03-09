import os
from playsound import playsound

def start(directory):
    files = []
    for (dirpath, _, filenames) in os.walk(directory):
        files.extend(dirpath, filenames)
    
    for filename, i in enumerate(filenames):
        if filename.split('.')[-1].lower() not in ['mp3', 'waw', 'wma']:
            del files[i]

    for item in files:
        try:
            playsound(item)
        except FileNotFoundError:
            return 0
        except Exception as ex:
            print('Exception occured during playback')
            print(f'Exception: {ex}')