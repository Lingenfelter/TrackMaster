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

    def set_end(self, end):
        cutoff = 0.1 * self.samplerate
        if end - self.data[0] > cutoff:
            self.data[1] = end
        else:
            self.parent.remove_element(self)

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
                except Exception as e:
                    print('-' * 50)
                    print('exception:', e)
                    print(f'track {self.name} \t start: {start} \t end: {self.data[1]} \t diff {frames} ')
                    print('-' * 50)


class ImageFile(File):
    def __init__(self, name, filetype='.png', data=None):
        self.updated = False
        File.__init__(self, name, filetype, data)

    def set_image(self, data):
        self.data = Image.open(io.BytesIO(data))

    def save(self, path=None, close=True):
        try:
            if path is None:
                path = self.get_path() + self.filetype
            if os.path.exists(path):
                os.remove(path)
            self.data.save(path)
            if close:
                self.data.close()
        except Exception as e:
            print(f'exception: {e}')


class RecordFileSystem:
    def __init__(self):
        self.artist = Directory('artist')
        self.album = Directory('album')
        self.album_art = ImageFile('img')
        self.samplerate = 0
        self.identify_at = 30
        self.potential_albums = {}
        self.album_id = None

        self.artist.add_child(self.album)
        self.album.add_child(self.album_art)

        # How close, in seconds, that the end of one track and the beginning of the next need to be to merge
        self.merge_threshold = 1.5

    def identify_latest(self, curr_pos):
        if len(self.album.data) == 1:
            return None
        # Get last track
        track = self.album.data[-1]

        # Check if it's already identified
        if track.is_identified:
            return [track.artist, track.album, track.name]

        # Otherwise, check if the track is long enough
        elif curr_pos - track.data[0] > self.samplerate * 30:
            # Identify track
            info = audID.identify_track(track.audio_source, track.data[0], curr_pos)
            # If there is a result, assign it to the track
            if info['result']:
                # Set basic info for the track
                name = info['result']['title']

                for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
                    name = name.replace(char, '-')

                track.name = name
                track.album = info['result']['album']
                track.artist = info['result']['artist']

                # Check if all the results have arrived
                if 'musicbrainz' in info['result']:

                    most_common_album_count = 0

                    for version in info['result']['musicbrainz']:
                        for album in version['releases']:
                            if album['id'] in self.potential_albums:
                                existing_album = self.potential_albums[album['id']]
                                album_occurrence = existing_album[1] + 1
                                title = existing_album[0]
                            else:
                                album_occurrence = 1
                                title = album['title']

                            self.potential_albums[album['id']] = [title, album_occurrence]

                            if album_occurrence > most_common_album_count:
                                if self.album_id is not album['id']:
                                    self.album_id = album['id']
                                    self.album.name = title
                                    self.album_art.updated = True

                                most_common_album_count = album_occurrence

                    if self.album_art.updated:
                        self.album_art.set_image(audID.get_art(self.album_id))
                        self.album_art.save('recordings/working/album.jpg', False)
                    track.is_identified = True

                return [track.artist, track.album, track.name]

        return None

    def add_track(self, track):
        track.samplerate = self.samplerate
        if len(self.album.data) > 1:
            track_spacing = self.samplerate * self.merge_threshold
            prev_track = self.album.data[-1]

            if track.data[0] - prev_track.data[1] > track_spacing:
                self.album.add_child(track)
        else:
            self.album.add_child(track)

    def set_latest_track_end(self, end):
        track = self.album.data[-1]
        track.set_end(end)

    def get_album_art(self):
        if self.album_art.updated:
            return 'recordings/working/album.jpg'
        return None

    def save_all(self):
        self.artist.save_tree()
