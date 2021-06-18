import os
from PIL import Image
import soundfile as sf


class File:
    def __init__(self, name, filetype, data=None):
        self.name = name
        self.filetype = filetype
        self.data = data
        self.parent = None

    def get_path(self):
        if self.parent is None:
            return os.path.join('recordings', self.name)
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
        File.__init__(self, name, filetype)
        self.artist = ''
        self.album = ''

    def merge(self, target):
        self.data[1] = target.data[1]
        self.parent.remove_element(target)

    def save(self):
        with sf.SoundFile('recordings/working/audio.flac') as source:
            source.seek(self.data[0])
            path = self.get_path() + self.filetype
            frames = (self.data[1] - self.data[0])
            sf.write(path, source.read(frames=frames), source.samplerate)


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
