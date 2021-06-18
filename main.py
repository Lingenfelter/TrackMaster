import gui
import os

if __name__ == '__main__':
    if os.path.exists('recordings/file.wav'):
        os.remove('recordings/file.wav')

    gui.show_gui()
