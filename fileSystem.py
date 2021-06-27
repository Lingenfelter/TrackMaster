import os
from PIL import Image
import soundfile as sf

saveDir = 'recordings'
track_num = 0


class File:
    def __init__(self, name, filetype, data=None):
        self.name = name
        self.filetype = filetype
        self.data = data
        self.parent = None

    def get_path(self):
        if self.parent is None:
            return os.path.join(saveDir, self.name)
        return os.path.join(self.parent.get_path(), self.name)


class Directory(File):
    def __init__(self, name):
        File.__init__(self, name, '_dir', data=[])

    def add_child(self, child):
        self.data.append(child)
        child.parent = self

    def save(self):
        path = self.get_path()
        if not os.path.exists(path):
            os.mkdir(path)

    def save_tree(self):
        self.save()
        for el in self.data:
            if el.filetype == '_dir':
                el.save_tree()
            else:
                el.save()

    def remove_element(self, item):
        self.data.remove(item)


class AudioFile(File):
    def __init__(self, name, filetype='.wav'):
        File.__init__(self, name, filetype, data=[0, 0])
        self.audio_source = 'recordings/working/audio.wav'
        self.cutoff = 0.0  # Files below this length in seconds are not saved
        self.padding = 0.0  # Seconds added before and after a track
        self.artist = ''
        self.album = ''

    def set_track(self, start, end):
        self.data[0] = start
        self.data[1] = end

    def merge(self, target):
        self.data[1] = target.data[1]
        # self.parent.remove_element(target)

    def save(self):
        # All print statements are for real-time use debugging, will be used to monitor when connected
        # to a record player.
        global track_num
        with sf.SoundFile(self.audio_source) as source:
            # Get the beginning of the track
            start = int(self.data[0])
            padding = int(self.padding * source.samplerate)
            # Get the running time of the track
            frames = (int(self.data[1]) - start)
            try:
                # If the running time is longer than the cutoff length, save the track
                if frames > self.cutoff * source.samplerate:
                    # Save the track in a "01 - name.file" convention.
                    track_num += 1
                    self.name = str('{:02d}'.format(track_num)) + ' - ' + self.name

                    print(f'track {self.name} \t start: {start} \t end: {self.data[1]} \t diff {frames} ')

                    # Add a small amount of recording padding to ensure that the whole note that triggered
                    # the recording is captured.
                    start = start - padding if start - padding > 0 else 0
                    frames += (padding * 2)

                    source.seek(start)
                    path = self.get_path() + self.filetype
                    sf.write(path, source.read(frames=frames), source.samplerate)
                    print(f'{self.name = }: saved')
                else:
                    print(f'{self.name = }: did not save due to insufficient length')
                    print(f'{frames = }\t{self.cutoff * source.samplerate = }')
            except Exception:
                print(f'{Exception = }')
                print('-' * 50)
                print(f'track {self.name} \t start: {start} \t end: {self.data[1]} \t diff {frames} ')


class ImageFile(File):
    def __init__(self, name, filetype='.png', data=None):
        File.__init__(self, name, filetype, data)

    def set_image(self, data):
        self.data = Image.open(data)

    def save(self):
        path = self.get_path() + self.filetype
        if os.path.exists(path):
            os.remove(path)
        self.data.save(path)
        self.data.close()


class RecordFileSystem:
    def __init__(self):
        self.artist = Directory('artist')
        self.album = Directory('album')
        self.samplerate = 0

        self.artist.add_child(self.album)

        # How close, in seconds, that the end of one track and the beginning of the next need to be to merge
        self.merge_threshold = 0.73

    def add_track(self, track):

        # If track is not the first element, compare it to the previous track
        if len(self.album.data) > 0:
            track_spacing = self.samplerate * self.merge_threshold
            prev_track = self.album.data[-1]

            # If this track and the previous track are with-in the merging threshold, merge
            if track.data[0] - prev_track.data[1] < track_spacing:
                print(f'{track.name = }\t Merged with {prev_track.name = }')
                prev_track.merge(track)

            # Otherwise make it a new track.
            else:
                print(f'{track.name = }\tGap too large, did not merge -'
                      f' {track.data[0] - prev_track.data[1]} < {track_spacing}')
                self.album.add_child(track)
        else:
            print(f'{track.name = }\t First element')
            self.album.add_child(track)

    def save_all(self):
        print('-' * 50, '\nSaving ...')
        self.artist.save_tree()
