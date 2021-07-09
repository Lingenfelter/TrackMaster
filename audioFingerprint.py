import requests
import json
import musicbrainzngs as brain
import soundfile as sf

FINGERPRINTING_KEY: str

brain.set_useragent('TrackMaster', '0.1', 'M.Lingenfelter92@gmail.com')


def identify_track(file: str, beginning, end, dump=True):
    output = 'recordings/working/identify.wav'
    with sf.SoundFile(file) as source:
        time_to_identify = source.samplerate * 25
        frames = end - beginning
        if frames > time_to_identify:
            seek = end - time_to_identify
            frames = time_to_identify
        else:
            seek = beginning
        source.seek(seek)
        sf.write(output, source.read(frames=frames), source.samplerate)
    data = {'api_token': FINGERPRINTING_KEY, 'return': 'musicbrainz'}
    files = {'file': open(output, 'rb')}

    result = requests.post('https://api.audd.io/', data=data, files=files).json()
    if dump:
        with open('track.json', 'w') as f:
            json.dump(result, f, indent=4)
    return result


def get_art(release_id):
    return brain.get_image_front(release_id, '500')


def get_data(artist, song):
    result = brain.search_recordings(recording=song, artistname=artist)

    with open('data.json', 'w') as f:
        json.dump(result, f, indent=4)
