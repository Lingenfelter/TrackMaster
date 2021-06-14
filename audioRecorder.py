import queue
import sys
import threading

import sounddevice as sd
import soundfile as sf
import numpy
assert numpy

haltSignal = threading.Event()
playbackVolume = 0.0
q = queue.Queue()

plotRecSize = 10_000
plotRecStepAmt = 20
plotRec = numpy.ndarray(shape=(plotRecSize, 2), buffer=numpy.array([[0.0, 0.0] * plotRecSize]))


def set_volume(vol):
    global playbackVolume
    playbackVolume = vol


def callback(indata, outdata, frames, time, status):
    global plotRec
    if status:
        print(status, file=sys.stderr)
    outdata[:] = indata.copy() * playbackVolume
    q.put(indata.copy())


def _record(stop_event):
    global plotRec
    device = sd.query_devices(None, 'input')

    with sf.SoundFile('recordings/file.wav', mode='x', samplerate=int(device['default_samplerate']), channels=2) as file:
        with sd.Stream(channels=2, callback=callback):
            while not stop_event.is_set():
                data = q.get()
                file.write(data)
                plotRec = numpy.append(plotRec, data[::plotRecStepAmt], axis=0)
                if plotRec.size > plotRecSize:
                    plotRec = plotRec[-plotRecSize:]


def start_recording():
    haltSignal.clear()
    threading.Thread(target=_record, args=(haltSignal, )).start()


def stop_recording():
    haltSignal.set()


def get_plotRec():
    return plotRec.T.tolist()