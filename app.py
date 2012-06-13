import os
import twilio.twiml as twiml
import audioop
import urllib
import sys
import wave
import hashlib

from flask import Flask, request, url_for
app = Flask(__name__)

NUM_FRAMES = 20000
song = '\x00' * NUM_FRAMES

@app.route('/')
def beatbox():
    r = twiml.Response()
    #r.say("Welcome to Twilio Beatbox! Record a loop after the ding. Press pound when finished.")
    r.record(action='/record_handler', method='GET', finishOnKey='#')
    return str(r)

@app.route('/record_handler')
def record_handler():
    global song
    r = twiml.Response()

    flask_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(flask_dir, "static/")
    filename = os.path.join(static_dir, 'lol')
    urllib.urlretrieve(request.values.get('RecordingUrl'), filename)
    tmp_file = wave.open(filename)
    s = tmp_file.readframes(NUM_FRAMES)
    os.remove(filename)
    if len(s) == 0:
        s = '\x00' * NUM_FRAMES
    elif len(s) < NUM_FRAMES:
        s = (s * ((NUM_FRAMES / len(s)) + 1))
    song = audioop.add(s[:NUM_FRAMES], song, 2)

    fuu_name = hashlib.sha224(song).hexdigest() + '.wav'
    fuu_full_path = os.path.join(static_dir, fuu_name)
    fuu = wave.open(fuu_full_path, 'w')
    fuu.setnchannels(1)
    fuu.setsampwidth(2)
    fuu.setframerate(8000)
    fuu.writeframes(song)
    fuu.close()
    r.play(url_for('static', filename=fuu_name))
    r.say('Press 1 to record another track or 2 to finish')
    r.gather(method='GET', numDigits=1, action='/user_option')
    return str(r)

@app.route('/user_option')
def user_option():
    ret = ''
    if request.values.get('Digits') == '1':
        r = twiml.Response()
        r.record(action='/record_handler', method='GET', finishOnKey='#')
        ret = str(r)
    return ret

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
