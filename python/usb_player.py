import os
from pygame import mixer

skipped = False
paused = False

def start(directory):
    global paused
    global skipped
    was_paused = False
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
    
    mixer.init()
    for item in files:
        try:
            print(f'Now playing {item}')
            mixer.music.load(item)
            mixer.music.play()
            while mixer.music.get_busy():
                if skip:
                    mixer.music.stop()
                    skipped = False
                if paused:
                    mixer.music.pause()
                elif was_paused:
                    mixer.music.unpause()
                pass
        except FileNotFoundError:
            return 0
        except Exception as ex:
            print('Exception occured during playback')
            print(f'Exception: {ex}')

def pause(a=None):
    global paused
    paused = True

def skip(a=None):
    global skipped
    skipped = True