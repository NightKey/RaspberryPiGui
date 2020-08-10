import os, wave
try:
    import mutagen.mp3
except:
    os.system("pip3 install mutagen")
from pygame import mixer
from print_handler import printer, verbose

"""A program for playing mp3 from a given directory"""

skipped = False
previous = False
paused = False
volume = 1.0
playing = False
kill = False
now_playing = "none"
sounds = []

print = printer

def stop():
    """Stops the player from playing"""
    global kill
    verbose("USB stop called")
    kill = True

def play_sound(name):
    if name in sounds:
        tmp = wave.open(sounds[name])
        mixer.init(frequency=tmp.getframerate())
        mixer.music.load(sounds[name])
        mixer.music.set_volume(volume)
        mixer.music.play()

def start(directory):
    """
    Creates a playlist from a given directory, using only MP3 and WAV files.
    """
    global paused
    global skipped
    global previous
    global now_playing
    global playing
    was_paused = False
    files = []
    for (dirpath, _, filenames) in os.walk(directory):
        for file in filenames:
            files.append(os.path.join(dirpath, file))   #Creates a list of files
    i = 0
    while i < len(files) - 1:
        now = files[i]
        if now.split('.')[-1].lower() not in ['mp3', 'wav']:
            del files[i]    #Removes every file that isn't MP3 or WAV
        else:
            i += 1
        print(f'Size: {len(files)}', 'USB', end='')
    i = 0
    fail_count = 0
    while i < len(files):   #Starts playing files while it's not at the end.
        try:
            if fail_count > 5:  #If playing failes 5 times, breaks out (The media was removed probably)
                break
            item = files[i]
            i+=1
            now_playing = os.path.basename(item)
            if now_playing.split('.')[-1].lower() == 'mp3': #If it's an MP3 file, sets the requency to the files sample rate
                tmp = mutagen.mp3.MP3(item)
                mixer.init(frequency=tmp.info.sample_rate)
            else:   #If it's a WAV file, sets the requency to the files sample rate
                tmp = wave.open(item)
                mixer.init(frequency=tmp.getframerate())
            del tmp
            print(f'Now playing {now_playing}', 'USB player')
            mixer.music.load(item)
            mixer.music.set_volume(volume)
            mixer.music.play()
            playing = True
            while True:
                if mixer.music.get_volume() != volume:  #Sets the volume, if it's changed during replay
                    mixer.music.set_volume(volume)
                if not mixer.music.get_busy() and not paused:   #If the music isn't paused, and the play finished exits the loop
                    break
                if skipped: #If skipped, stops the music
                    mixer.music.stop()
                    skipped = False
                if paused:  #If paused, pauses the music
                    mixer.music.pause()
                    was_paused=True
                elif was_paused:    #If not paused, but was, un pauses the player
                    mixer.music.unpause()
                    was_paused=False
                if previous:    #Skips back one
                    i -= 2
                    mixer.music.stop()
                    previous = False
                if kill:    #If killed, stops the music
                    mixer.stop()
            playing = False
            now_playing = "none"
            if fail_count != 0: #If finished, and failcount wasn't 0, resets it (If a file was unplayable)
                fail_count = 0
            if kill:    #If kill, returns
                break
        except Exception as ex:
            print('Exception occured during playback', 'USB player')
            print(f'Exception: {ex}', 'USB player')
            fail_count += 1

def pause(a=None):  #Pauses the player
    global paused
    paused = not paused

def skip(a=None):  #Skips the player
    global skipped
    skipped = True

def set_volume(_volume):  #Setst the volume to the player
    global volume
    volume = (float(_volume)/100)

def prev(a=None):  #Skips back the player
    global previous
    previous = True

def show_now_playing():  #Shows the now playing
    print(now_playing, 'USB player')

if __name__=="__main__":  #Tests the player
    def Player():
        start('./test/Test')
    import threading
    player = threading.Thread(target=Player)
    player.name = 'Player'
    player.start()
    while True:
        a = input('> ')
        if a == 'pause':
            pause()
        elif a == 'skip':
            skip()
        elif a == 'prev':
            prev()
        elif a == 'now playing':
            show_now_playing()
        elif "volume" in a:
            set_volume(a.split(' ')[-1])
