import os
from pygame import mixer

skipped = False
previous = False
paused = False
volume = 1.0

def start(directory):
    global paused
    global skipped
    global previous
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
    i = 0
    while i < len(files):
        try:
            item = files[i]
            i+=1
            print(f'Now playing {item}')
            mixer.music.load(item)
            mixer.music.set_volume(volume)
            mixer.music.play()
            while True:
                if mixer.music.get_volume() != volume:
                    mixer.music.set_volume(volume)
                if not mixer.music.get_busy() and not paused:
                    break
                if skipped:
                    mixer.music.stop()
                    skipped = False
                if paused:
                    mixer.music.pause()
                    was_paused=True
                elif was_paused:
                    mixer.music.unpause()
                    was_paused=False
                if previous:
                    i -= 2
                    mixer.music.stop()
                    previous = False
                pass
        except FileNotFoundError:
            return 0
        except Exception as ex:
            print('Exception occured during playback')
            print(f'Exception: {ex}')

def pause(a=None):
    global paused
    paused = not paused

def skip(a=None):
    global skipped
    skipped = True

def set_volume(_volume):
    global volume
    volume = (float(_volume)/100)

def prev(a=None):
    global previous
    previous = True