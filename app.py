import os
import twilio.twiml as twiml
import audioop
import urllib
import sys
import wave

from flask import Flask, request
app = Flask(__name__)

song = ' ' * 1000

@app.route('/')
def beatbox():
    r = twiml.Response()
    #r.say("Welcome to Twilio Beatbox! Record a loop after the ding. Press pound when finished.")
    r.record(action='/record_callback', method='GET', finishOnKey='#')
    return str(r)

@app.route('/record_callback')
def record_handler():
    global song
    r = twiml.Response()
    tmp_file = wave.open(urllib.urlretrieve(request.values.get('RecordingUrl'))[0])
    sys.stderr.write('filename: ' + urllib.urlretrieve(request.values.get('RecordingUrl'))[0] + '\n')
    s = tmp_file.readframes(1000)
    if len(s) == 0:
        s = ' ' * 1000
    elif len(s) < 1000:
        s = (s * ((1000 / len(s)) + 1))
    sys.stderr.write('len s: ' + str(len(s)))
    sys.stderr.write('len song: ' + str(len(song)))
    song = audioop.add(s[:1000], song, 2)
    r.play(request.values.get('RecordingUrl'))
    r.say('Press 1 to record another track or 2 to finish')
    r.gather(method='GET', numDigits=1, action='/user_option')
    return str(r)

@app.route('/user_option')
def user_option():
    ret = ''
    if request.values.get('Digits') == 1:
        ret = str(twiml.Response().record(action='/record_handler', method='GET', finishOnKey='#'))
    return ret

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
