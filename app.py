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

from flask import Flask, request, url_for
app = Flask(__name__)

# (786) 302-9603
# 714 869 7503

NUM_FRAMES = 40000 # 8000 samples/second * 5 seconds = 40000
song = '\x00' * NUM_FRAMES
base_song_filename = ''
current_song_filename = ''
num_tracks = 0
number = 0
rest = TwilioRestClient()
greeting_url = ''
app.SERVER_NAME = 'twilio-beatbox.herokuapp.com'

@app.route('/')
def beatbox():
    global base_song_filename
    r = twiml.Response()
    r.say("Welcome to Twilio Beatbox! Record a 5 second loop after the ding.")
    r.record(action='/record_handler', method='GET', maxLength=5)

    base_song_filename = request.values.get('From') + '-' + str(time.time()) + '.wav'
    random.seed()
    return str(r)

@app.route('/record_handler')
def record_handler():
    global song
    global current_song_filename
    global num_tracks
    r = twiml.Response()

    flask_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(flask_dir, "static/")
    sys.stderr.write('url ' + request.values.get('RecordingUrl') + '\n')
    rec_file = urllib.urlopen(request.values.get('RecordingUrl'))
    sys.stderr.write(rec_file.read() + '\n')
    recording = wave.open(rec_file)
    s = recording.readframes(NUM_FRAMES)
    if len(s) == 0:
        s = '\x00' * NUM_FRAMES
    elif len(s) < NUM_FRAMES:
        s = (s * ((NUM_FRAMES / len(s)) + 1))
    song = audioop.add(s[:NUM_FRAMES], song, 2)

    # Need a unique filename so Twilio won't cache it
    if current_song_filename != '':
        os.remove(os.path.join(static_dir, current_song_filename))
    current_song_filename = str(num_tracks) + base_song_filename

    song_file_full_path = os.path.join(static_dir, current_song_filename)
    song_file = wave.open(song_file_full_path, 'w')
    song_file.setnchannels(1)
    song_file.setsampwidth(2)
    song_file.setframerate(8000)
    song_file.writeframes(song)
    song_file.close()
    num_tracks += 1
    r.play(url_for('static', filename=current_song_filename))

    r.say('Press 1 to record another track or 2 to finish')
    r.gather(method='GET', numDigits=1, action='/user_option')
    return str(r)

@app.route('/user_option')
def user_option():
    r = twiml.Response()
    if request.values.get('Digits') == '1':
        r.record(action='/record_handler', method='GET', maxLength=5)
    elif request.values.get('Digits') == '2':
        r.say('Here is your song')
        r.play(url_for('static', filename=current_song_filename), loop=2)
        r.say('Enter a phone number to send this song to')
        r.gather(method='GET', numDigits=10, action='/phone_number')
    return str(r)

@app.route('/phone_number')
def phone_number():
    global number
    r = twiml.Response()
    number = request.values.get('Digits')
    r.say('Record a greeting for your friend')
    r.record(method='GET', finishOnKey='#', action='/send_song')
    return str(r)

@app.route('/send_song')
def send_song():
    global greeting_url
    greeting_url = request.values.get('RecordingUrl')
    r = twiml.Response()
    r.say('Sending song')
    call = rest.calls.create(to=number,
            from_='6164218012',
            url=url_for('play_song', _external=True))
    return str(r)

@app.route('/play_song', methods=['POST'])
def play_song():
    r = twiml.Response()
    r.play(greeting_url)
    r.play(url_for('static', filename=current_song_filename), loop=0)
    return str(r)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
