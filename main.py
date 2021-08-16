import os
from dotenv import load_dotenv

import gui
import audioRecorder as aR
import audioFingerprint as audID
from fileSystem import RecordFileSystem

if __name__ == '__main__':
    if os.path.exists('recordings/working/audio.wav'):
        os.remove('recordings/working/audio.wav')

    load_dotenv('.env')

    FINGERPRINTING_KEY = os.environ.get('API_KEY')
    audID.FINGERPRINTING_KEY = FINGERPRINTING_KEY

    gui.show_gui()
