import queue
import statistics
import sys
import threading
import concurrent.futures

import sounddevice as sd
import soundfile as sf
import numpy

from fileSystem import RecordFileSystem, AudioFile

assert numpy

executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

haltSignal = threading.Event()
playbackVolume = 0.25
q = queue.Queue()

# Initialize the array that gets sent to the gui for the visual waveform
plotRecSize = 5_000
plotRecStepAmt = 40
plotRec = numpy.ndarray(shape=(plotRecSize, 2), buffer=numpy.array([[0.0, 0.0] * plotRecSize]))

recording_threshold = 0.0
samplerate: int
filetype: str
subtype: str
track: AudioFile
is_track = False
beginning_of_album = 0
threshold_data = []
song_end = 0
identify_at = 0

# Filesystem head
file_head: RecordFileSystem

# Identified Song info
default_msg = 'Nothing yet'
song_info = [default_msg] * 3
finished_identification = True


def get_formats(): return [x for x in sf.available_formats().keys()]


def get_subtype(selected_format): return sf.default_subtype(selected_format), \
                                         [x for x in sf.available_subtypes(selected_format).keys()]


def get_devices(): return [device for device in sd.query_devices() if device['max_input_channels'] > 0]


def set_volume(vol):
    global playbackVolume
    playbackVolume = vol


def callback(indata, outdata, frames, time, status):
    global plotRec
    if status:
        print(status, file=sys.stderr)
    outdata[:] = indata * playbackVolume
    q.put(indata.copy())


def _record(stop_event, single_album):
    global samplerate, identify_at
    sd.default.samplerate = samplerate
    # sd.default.device = device['name']
    with sf.SoundFile('recordings/working/audio.wav', mode='x', samplerate=samplerate,
                      subtype=subtype, channels=2) as current_recording:
        file_head.samplerate = samplerate
        with sd.Stream(channels=2, callback=callback):
            while not stop_event.is_set():
                data = q.get()

                data_max = abs(data).max()

                # Write input stream to audio file
                current_recording.write(data)

                # Get current position
                curr_pos = current_recording.tell()
                find_track_edges(curr_pos, data_max)

                # Attempt to identify the current recording, then add ten sec to the identify counter
                if identify_at < curr_pos and executor._work_queue.qsize() < 2:
                    executor.submit(attempt_identification, curr_pos)
                    identify_at += 10 * current_recording.samplerate

                write_to_plot(data)

        if single_album:
            file_head.single_track()

        file_head.expand_tracks(beginning_of_album, curr_pos)
        file_head.save_all()


def find_track_edges(curr_pos, data_max):
    global recording_threshold, is_track, track, beginning_of_album, identify_at, song_end, song_info
    # Roughly determine if the incoming audio is the beginning or end of a track
    # If there is a non-zero threshold set use that.
    if recording_threshold != 0.0:
        if is_track:
            if 0 < song_end < curr_pos and data_max < recording_threshold:
                is_track = False
            elif song_end == 0 and data_max < recording_threshold:
                file_head.set_latest_track_end(curr_pos)
                is_track = False
        else:
            if data_max > recording_threshold and curr_pos > song_end + 3 * samplerate:
                song_info[2] = 'identifying...'
                song_end = 0
                track = AudioFile('', '.' + filetype, subtype)
                track.data[0] = curr_pos
                file_head.add_track(track)
                is_track = True

    # Otherwise find the minimum threshold from the album's noise
    else:
        if beginning_of_album == 0:
            if 0.05 < data_max < 0.1:
                beginning_of_album = curr_pos
                identify_at = beginning_of_album + 20 * samplerate

        # Read in a fixed amount of noise data (2 sec) and add the max volume to an array
        elif curr_pos - beginning_of_album < samplerate * 2.0:
            threshold_data.append(data_max)

        # Find the median noise max, to remove the outliers inherent in starting the record
        # Then add a small amount to ensure that noise is excluded.
        else:
            recording_threshold = statistics.median(threshold_data) + 0.015


def attempt_identification(curr_pos):
    global song_info, song_end, identify_at
    identified_info = file_head.identify_latest(curr_pos)
    if identified_info is not None:
        song_info = identified_info[:3]
        song_end = identified_info[3]
        identify_at = identified_info[3] + 10 * samplerate


def write_to_plot(data):
    """ Write input stream to waveform array, then trim the waveform array"""
    global plotRec
    plotRec = numpy.append(plotRec, data[::plotRecStepAmt], axis=0)
    if plotRec.size > plotRecSize:
        plotRec = plotRec[-plotRecSize:]


def start_recording(rec_filetype, rec_subtype, rec_samplerate, single_album=False):
    try:
        global plotRec, q, recording_threshold, is_track, filetype, subtype, samplerate
        filetype, subtype, samplerate = rec_filetype, rec_subtype, rec_samplerate
        plotRec = numpy.ndarray(shape=(plotRecSize, 2), buffer=numpy.array([[0.0, 0.0] * plotRecSize]))
        q = queue.Queue()
        recording_threshold = 0.0
        is_track = False
        haltSignal.clear()
        executor.submit(_record, haltSignal, single_album)
    except Exception as e:
        print(e)


def stop_recording():
    haltSignal.set()


def get_plotRec():
    return plotRec.T.tolist()
