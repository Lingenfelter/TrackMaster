import os

import gui
import audioRecorder as aR
from fileSystem import RecordFileSystem

if __name__ == '__main__':
    if os.path.exists('recordings/working/audio.wav'):
        os.remove('recordings/working/audio.wav')

    file_head = RecordFileSystem()

    gui.file_head = file_head
    aR.file_head = file_head

    gui.show_gui()
