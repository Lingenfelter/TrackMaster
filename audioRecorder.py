import queue
import statistics
import sys
import threading

import sounddevice as sd
import soundfile as sf
import numpy

from fileSystem import RecordFileSystem, AudioFile

assert numpy

haltSignal = threading.Event()
playbackVolume = 1.0
q = queue.Queue()

# Initialize the array that gets sent to the gui for the visual waveform
plotRecSize = 5_000
plotRecStepAmt = 40
plotRec = numpy.ndarray(shape=(plotRecSize, 2), buffer=numpy.array([[0.0, 0.0] * plotRecSize]))

recording_threshold = 0.0

# Filesystem head
file_head: RecordFileSystem


def set_volume(vol):
    global playbackVolume
    playbackVolume = vol


def callback(indata, outdata, frames, time, status):
    global plotRec
    if status:
        print(status, file=sys.stderr)
    outdata[:] = indata * playbackVolume
    q.put(indata.copy())


def _record(stop_event):
    global recording_threshold
    is_track = False
    device = sd.query_devices(None, 'input')
    start_pos = None
    track_num = 0
    beginning_of_album = 0
    threshold_data = []

    with sf.SoundFile('recordings/working/audio.wav', mode='x', samplerate=int(device['default_samplerate']),
                      channels=2) as current_recording:
        file_head.samplerate = current_recording.samplerate
        with sd.Stream(channels=2, callback=callback):
            while not stop_event.is_set():
                data = q.get()

                data_max = abs(data).max()

                # Write input stream to audio file
                current_recording.write(data)

                # Roughly determine if the incoming audio is the beginning or end of a track
                # If there is a non-zero threshold set use that.
                if recording_threshold != 0.0:
                    if data_max > recording_threshold and not is_track:
                        track_num += 1
                        start_pos = current_recording.tell()
                        # Temporary print statements and naming convention for ease of debugging while
                        # running program on an actual record player.
                        print('Starting track', track_num, 'at pos', start_pos, end='... \t')
                        track = AudioFile(str(track_num))
                        is_track = True
                    elif data_max < recording_threshold and is_track:
                        print('End at', current_recording.tell())
                        track.set_track(start_pos, current_recording.tell())
                        file_head.add_track(track)
                        is_track = False

                # Otherwise find the minimum threshold from the album's noise
                else:
                    if beginning_of_album == 0:
                        if 0.05 < data_max < 0.1:
                            beginning_of_album = current_recording.tell()
                            print(f'{beginning_of_album = }')

                    # Read in a fixed amount of noise data (1/4 of a sec) and add the max volume to an array
                    elif current_recording.tell() - beginning_of_album < current_recording.samplerate * 0.25:
                        threshold_data.append(data_max)

                    # Find the median noise max, to remove the outliers inherent in starting the record
                    # Then add a small amount to ensure that noise is excluded.
                    else:
                        recording_threshold = statistics.median(threshold_data) + 0.015
                        print(f'{recording_threshold = }')

                write_to_plot(data)

            file_head.save_all()


def write_to_plot(data):
    ''' Write input stream to waveform array, then trim the waveform array'''
    global plotRec
    plotRec = numpy.append(plotRec, data[::plotRecStepAmt], axis=0)
    if plotRec.size > plotRecSize:
        plotRec = plotRec[-plotRecSize:]


def start_recording():
    haltSignal.clear()
    threading.Thread(target=_record, args=(haltSignal,)).start()


def stop_recording():
    haltSignal.set()


def get_plotRec():
    return plotRec.T.tolist()
