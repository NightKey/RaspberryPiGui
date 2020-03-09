import os
from pygame import mixer

def start(directory):
    print('Player called')
    files = []
    for (dirpath, _, filenames) in os.walk(directory):
        for file in filenames:
            files.append(os.path.join(dirpath, file))
    print('Got all files')
    for i, filename in enumerate(filenames):
        if filename.split('.')[-1].lower() not in ['mp3', 'waw', 'wma']:
            del files[i]
    print('Sorted for audio files')
    for item in files:
        try:
            mixer.init()
            print(f'Now playing {item}')
            mixer.music.load(item)
            mixer.music.play()
            while mixer.music.get_busy():
                pass
        except FileNotFoundError:
            return 0
        except Exception as ex:
            print('Exception occured during playback')
            print(f'Exception: {ex}')