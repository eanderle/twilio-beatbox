import os
import twilio.twiml as twiml

from flask import Flask
app = Flask(__name__)

@app.route('/')
def beatbox():
    r = twiml.Response()
    r.say("Welcome to Twilio Beatbox! Record a loop after the ding. Ding")
    r.record(action='/record_handler')
    return str(r)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
