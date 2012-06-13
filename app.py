import os
import twilio.twiml as twiml

from flask import Flask, request
app = Flask(__name__)

@app.route('/')
def beatbox():
    r = twiml.Response()
    r.say("Welcome to Twilio Beatbox! Record a loop after the ding. Press pound when finished. Ding")
    r.record(action='/record_handler', method='GET', playBeep=False, finishOnKey='#')
    return str(r)

@app.route('/record_handler')
def record_handler():
    r = twiml.Response()
    r.play(request.values.get('RecordingUrl'))
    return str(r)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)
