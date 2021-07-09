import os
from dotenv import load_dotenv

import gui
import audioRecorder as aR
import audioFingerprint as audID
from fileSystem import RecordFileSystem

if __name__ == '__main__':
    if os.path.exists('recordings/working/audio.wav'):
        os.remove('recordings/working/audio.wav')

    file_head = RecordFileSystem()

    gui.file_head = file_head
    aR.file_head = file_head

    load_dotenv('.env')

    FINGERPRINTING_KEY = os.environ.get('API_KEY')
    audID.FINGERPRINTING_KEY = FINGERPRINTING_KEY

    # audID.get_sample('recordings/artist/album/11 - 491.wav', 'recordings/working/test.wav')
    # audID.identify('recordings/working/test.wav')
    # audID.get_data('David Bowie', 'Starman')

    gui.show_gui()
