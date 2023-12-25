import os
from typing import List
import wave
try:
    import mutagen.mp3
except:
    os.system("pip3 install mutagen")
from pygame import mixer
from smdb_logger import Logger
from time import sleep

"""A program for playing mp3 from a given directory"""


class USBPlayer:

    def __init__(self, logger) -> None:
        self.volume = 1.0
        self.playing = False
        self.paused = False
        self.kill = False
        self.index = 0
        self.now_playing = "none"
        self.sounds = []
        self.files = []
        self.logger: Logger = logger

    def stop(self):
        """Stops the player from playing"""
        self.logger.debug("USB stop called")
        self.kill = True
        mixer.music.stop()

    def play_sound(self, name):
        if name in self.sounds:
            tmp = wave.open(self.sounds[name])
            mixer.init(frequency=tmp.getframerate())
            mixer.music.load(self.sounds[name])
            mixer.music.set_volume(self.volume)
            mixer.music.play()
            while mixer.music.get_busy():
                sleep(1)
            mixer.music.unload()
            mixer.quit()

    def start(self, directory):
        """
        Creates a playlist from a given directory, using only MP3 and WAV files.
        """
        self.files: List[str] = []
        for (dirpath, _, filenames) in os.walk(directory):
            for file in filenames:
                # Creates a list of files
                self.files.append(os.path.join(dirpath, file))
        i = 0
        while i < len(self.files) - 1:
            now = self.files[i]
            if now.split('.')[-1].lower() not in ['mp3', 'wav']:
                del self.files[i]  # Removes every file that isn't MP3 or WAV
            else:
                i += 1
            # self.logger.debug(f'Size: {len(self.files)}')
        fail_count = 0
        # Starts playing files while it's not at the end.
        while self.index < len(self.files):
            try:
                # If playing failes 5 times, breaks out (The media was removed probably)
                if fail_count > 5:
                    break
                item = self.files[self.index]
                self.index += 1
                self.now_playing = os.path.basename(item)
                # If it's an MP3 file, sets the requency to the files sample rate
                if self.now_playing.split('.')[-1].lower() == 'mp3':
                    tmp = mutagen.mp3.MP3(item)
                    mixer.init(frequency=tmp.info.sample_rate)
                else:  # If it's a WAV file, sets the requency to the files sample rate
                    tmp = wave.open(item)
                    mixer.init(frequency=tmp.getframerate())
                del tmp
                self.logger.info(f'Now playing {self.now_playing}')
                mixer.music.load(item)
                mixer.music.set_volume(self.volume)
                mixer.music.play()
                self.playing = True
                while True:
                    if mixer.music.get_volume() != self.volume:  # Sets the volume, if it's changed during replay
                        mixer.music.set_volume(self.volume)
                    # If the music isn't paused, and the play finished exits the loop
                    if not mixer.music.get_busy() and not self.paused:
                        break
                mixer.music.unload()
                mixer.quit()
                self.playing = False
                self.now_playing = "none"
                # If finished, and failcount wasn't 0, resets it (If a file was unplayable)
                if fail_count != 0:
                    fail_count = 0
                if self.kill:  # If kill, returns
                    break
            except Exception as ex:
                self.logger.error(
                    f'Exception occured during playbackException: {ex}')
                fail_count += 1
        self.index = 0

    def pause(self, a=None):  # Pauses the player
        if not self.paused:
            self.paused = True
            mixer.music.pause()
        else:
            mixer.music.unpause()
            sleep(0.5)
            self.paused = False

    def skip(self, a=None):  # Skips the player
        mixer.music.stop()

    def set_volume(self, _volume):  # Setst the volume to the player
        self.volume = (float(_volume)/100)

    def prev(self, a=None):  # Skips back the player
        self.index -= 2
        mixer.music.stop()

    def show_now_playing(self, ):  # Shows the now playing
        self.logger.info(self.now_playing)
