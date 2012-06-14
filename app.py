import os
import twilio.twiml as twiml
from twilio.rest import TwilioRestClient
import audioop
import urllib
import sys
import wave
import time
import hashlib
import string
import StringIO
import soundcloud

from flask import Flask, request, url_for
app = Flask(__name__)

# (786) 302-9603
# 714 869 7503

NUM_FRAMES = 80000 # 8000 samples/second * 5 seconds = 40000

song = {}
base_song_filename = {}
current_song_filename = {}
num_tracks = {}
number = {}
greeting_url = {}
num_songs = {}

rest = TwilioRestClient()
soundcloud_client = soundcloud.Client(client_id=os.environ['CLIENT_ID'], client_secret=os.environ['CLIENT_SECRET'], username=os.environ['USERNAME'], password=os.environ['PASSWORD'])
app.SERVER_NAME = 'twilio-beatbox.herokuapp.com'

@app.route('/')
def beatbox():
    global song
    global base_song_filename
    global current_song_filename
    global num_tracks
    global number
    global greeting_url
    global num_songs

    phone_number = request.values.get('From')
    song.update({phone_number:'\x00' * NUM_FRAMES})
    base_song_filename.update({phone_number:phone_number + '-' + str(time.time()) + '.wav'})
    current_song_filename.update({phone_number:''})
    num_tracks.update({phone_number:0})
    number.update({phone_number:0})
    greeting_url.update({phone_number:''})
    if phone_number in num_songs:
        num_songs[phone_number] += 1
    else:
        num_songs.update({phone_number:1})

    r = twiml.Response()
    r.say("Welcome to Twilio Beatbox! Record a 5 second loop after the ding.")
    r.record(action='/record_handler', method='GET', maxLength=5)

    return str(r)

@app.route('/record_handler')
def record_handler():
    global song
    global current_song_filename
    global num_tracks
    r = twiml.Response()
    phone_number = request.values.get('From')

    flask_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(flask_dir, "static/")
    rec_string = urllib.urlopen(request.values.get('RecordingUrl')).read()

    while string.find(rec_string, 'RestException') != -1:
        rec_string = urllib.urlopen(request.values.get('RecordingUrl')).read()

    rec_file = StringIO.StringIO(rec_string)
    recording = wave.open(rec_file)
    s = recording.readframes(NUM_FRAMES)
    if len(s) == 0:
        s = '\x00' * NUM_FRAMES
    elif len(s) < NUM_FRAMES:
        s = (s * ((NUM_FRAMES / len(s)) + 1))
    song[phone_number] = audioop.add(s[:NUM_FRAMES], song[phone_number], 2)

    # Need a unique filename so Twilio won't cache it
    if current_song_filename[phone_number] != '':
        os.remove(os.path.join(static_dir, current_song_filename[phone_number]))
    current_song_filename[phone_number] = str(num_tracks[phone_number]) + base_song_filename[phone_number]

    song_file_full_path = os.path.join(static_dir, current_song_filename[phone_number])
    song_file = wave.open(song_file_full_path, 'w')
    song_file.setnchannels(1)
    song_file.setsampwidth(2)
    song_file.setframerate(8000)
    song_file.writeframes(song[phone_number])
    song_file.close()
    num_tracks[phone_number] += 1
    r.play(url_for('static', filename=current_song_filename[phone_number]))

    with r.gather(method='GET', numDigits=1, action='/user_option') as g:
        g.say('Press 1 to record another track or 2 to finish')
    return str(r)

@app.route('/user_option')
def user_option():
    r = twiml.Response()
    phone_number = request.values.get('From')
    if request.values.get('Digits') == '1':
        r.record(action='/record_handler', method='GET', maxLength=5)
    elif request.values.get('Digits') == '2':
        flask_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(flask_dir, "static/")
        song_file_full_path = os.path.join(static_dir, current_song_filename[phone_number])
        track = soundcloud_client.post('/tracks', track={
            'title': phone_number[-4:] + "'s song " + str(num_songs[phone_number]),
            'asset_data': open(song_file_full_path, 'rb')
        })
        with r.gather(method='GET', numDigits=10, action='/phone_number', timeout=30) as g:
            g.say('Enter a phone number to send this song to')
    return str(r)

@app.route('/phone_number')
def phone_number():
    global number
    r = twiml.Response()
    number[request.values.get('From')] = request.values.get('Digits')
    r.say('Record a greeting for your friend. Push pound when finished')
    r.record(method='GET', finishOnKey='#', action='/send_song')
    return str(r)

@app.route('/send_song')
def send_song():
    global greeting_url
    phone_number = request.values.get('From')
    greeting_url[phone_number] = request.values.get('RecordingUrl')
    r = twiml.Response()
    r.say('Sending song. Goodbye')

    call = rest.calls.create(to=number[phone_number],
            from_='6164218012',
            url=url_for('play_song', _external=True) + '?FromLOL=' + urllib.quote(request.values.get('From')))
    return str(r)

@app.route('/play_song', methods=['POST'])
def play_song():
    global song
    global base_song_filename
    global current_song_filename
    global num_tracks
    global number
    global greeting_url

    phone_number = request.values.get('FromLOL')
    sys.stderr.write(str(greeting_url.keys()) + '\n')
    r = twiml.Response()
    r.play(greeting_url[phone_number])
    r.play(url_for('static', filename=current_song_filename[phone_number]), loop=0)

    song[phone_number] = ''
    base_song_filename[phone_number] = ''
    current_song_filename[phone_number] = ''
    num_tracks[phone_number] = 0
    number[phone_number] = ''
    greeting_url[phone_number] = ''

    return str(r)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
