import gui
import os

if os.path.exists('recordings/file.wav'):
    os.remove('recordings/file.wav')

gui.show_gui()