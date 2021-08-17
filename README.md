# TrackMaster
A vinyl record music recorder and manager

![In use](https://drive.google.com/uc?export=view&id=1G2deaa8YRRrNNbUI4C1nsRXREpmv_cLQ)

## Features
* Records a record and saves it as the individual tracks
* Identifies the songs and saves them with their name
* Tracks saved in a [artist]/[album]/[track].filetype format

## Video
https://user-images.githubusercontent.com/50857801/129616813-852ab81d-0f3d-4ce5-b511-b7cc2ecf8752.mp4

## Requirements
* Dear PyGui - [GitHub](https://github.com/hoffstadt/DearPyGui) and [PyPi](https://pypi.org/project/dearpygui/)
* Python-SoundDevice - [GitHub](https://github.com/spatialaudio/python-sounddevice/) and [PyPi](https://pypi.org/project/sounddevice/)
* SoundFile - [GitHub](https://github.com/bastibe/python-soundfile) and [PyPi](https://pypi.org/project/SoundFile/)
* Numpy - [GitHub](https://github.com/numpy/numpy) and [PyPi](https://pypi.org/project/numpy/)
* MusicBrainzngs - [PyPi](https://pypi.org/project/musicbrainzngs/)
* Pillow - [GitHub](https://github.com/python-pillow/Pillow) and [PyPi](https://pypi.org/project/Pillow/)
* Python-dotenv - [GitHub](https://github.com/theskumar/python-dotenv) and [PyPi](https://pypi.org/project/python-dotenv/)

## Running Instructions
1. Download the required packages
2. Update the .env file with your [AudD API key](https://audd.io)
3. Plug-in record player into your computer
4. Run main.py file
5. Adjust the save directory and any settings
6. Press 'Record' button
7. Start playing your record like normal
8. Press 'Stop Recording' when finished
