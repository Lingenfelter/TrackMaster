import os
import io
from PIL import Image
import soundfile as sf
import audioFingerprint as audID

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
    def __init__(self, name='', filetype='.wav'):
        File.__init__(self, name, filetype, data=[0, 0])
        self.audio_source = 'recordings/working/audio.wav'
        self.padding = 0.0  # Seconds added before and after a track
        self.artist = ''
        self.album = ''
        self.samplerate = 0
        self.is_identified = False

    def set_track(self, start, end):
        self.data[0] = start
        self.data[1] = end

    def merge(self, target):
        self.data[1] = target.data[1]

    def save(self):
        # All print statements are for real-time use debugging, will be used to monitor when connected
        # to a record player.
        global track_num
        min_length = 30 * self.samplerate
        if self.data[1] - self.data[0] > min_length:
            with sf.SoundFile(self.audio_source) as source:
                # Get the beginning of the track
                start = int(self.data[0])
                padding = int(self.padding * source.samplerate)
                # Get the running time of the track
                frames = (int(self.data[1]) - start)
                try:
                    # Save the track in a "## - name.file" convention.
                    track_num += 1
                    self.name = str('{:02d}'.format(track_num)) + ' - ' + self.name

                    # Add a small amount of recording padding to ensure that the whole note that triggered
                    # the recording is captured.
                    start = start - padding if start - padding > 0 else 0
                    frames += (padding * 2)

                    source.seek(start)
                    path = self.get_path() + self.filetype
                    sf.write(path, source.read(frames=frames), source.samplerate)
                    print(f'{self.name = }: saved')
                except Exception as e:
                    print('exception:', e)
                    print('-' * 50)
                    print(f'track {self.name} \t start: {start} \t end: {self.data[1]} \t diff {frames} ')
        else:
            print(f'File {self.name} not long enough to save')


class ImageFile(File):
    def __init__(self, name, filetype='.png', data=None):
        File.__init__(self, name, filetype, data)

    def set_image(self, data):
        self.data = Image.open(io.BytesIO(data))

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
        self.cutoff = 0.1  # Minimum time, in seconds that a track needs to be larger than
        self.identify_at = 30
        self.potential_albums = {}

        self.artist.add_child(self.album)

        # How close, in seconds, that the end of one track and the beginning of the next need to be to merge
        self.merge_threshold = 1.5

    def identify_latest(self, curr_pos):
        default_msg = 'Nothing yet'
        if len(self.album.data) == 0:
            return [default_msg * 3]
        # Get last track
        track = self.album.data[-1]

        # Check if it's already identified
        if track.is_identified:
            return [track.artist, track.album, track.name]

        # Otherwise, check if the track is long enough
        elif curr_pos - track.data[0] > self.samplerate * 30:
            print('Identifying...', end='\t')
            # Identify track
            info = audID.identify_track(track.audio_source, track.data[0], curr_pos)
            # If there is a result, assign it to the track
            if info['result']:
                track.name = info['result']['title']
                track.artist = info['result']['artist']
                print('Returned result...', end='\t')
                if 'musicbrainz' in info['result']:
                    for release in info['result']['musicbrainz']['releases']:
                        if release['id'] in self.potential_albums:
                            data = self.potential_albums[release['id']]
                            data[2] += 1
                            self.potential_albums[release['id']] = data
                        else:
                            self.potential_albums[release['id']] = [release['title'], release['media']['track']['number'], 1]
                    print('Fully identified')
                    track.is_identified = True
                else:
                    print('Still not identified')
                return [track.artist, track.album, track.name]

        return [default_msg * 3]

    def add_track(self, track):
        track.samplerate = self.samplerate
        # If the track is larger than the cutoff, add the track.
        if track.data[1] - track.data[0] > self.samplerate * self.cutoff:
            # If track is not the first element, compare it to the previous track
            if len(self.album.data) > 0:
                track_spacing = self.samplerate * self.merge_threshold
                prev_track = self.album.data[-1]

                # If this track and the previous track are with-in the merging threshold, merge
                if track.data[0] - prev_track.data[1] < track_spacing:
                    prev_track.merge(track)

                # Otherwise make it a new track.
                else:
                    self.album.add_child(track)
            else:
                self.album.add_child(track)

    def save_all(self):
        print('-' * 50, '\nSaving ...')
        print(f'{self.potential_albums = }')
        self.artist.save_tree()
