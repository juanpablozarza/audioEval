from flask import Flask, render_template, request
import webbrowser
import os
from flask_cors import CORS
import json

import lambdaTTS
import lambdaSpeechToScore
import lambdaGetSample
import io
import base64
from pydub import AudioSegment

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = '*'

rootPath = ''


@app.route(rootPath+'/')
def main():
    return render_template('main.html')


@app.route(rootPath+'/getAudioFromText', methods=['POST'])
def getAudioFromText():
    event = {'body': json.dumps(request.get_json(force=True))}
    return lambdaTTS.lambda_handler(event, [])


@app.route(rootPath+'/getSample', methods=['POST'])
def getNext():
    event = {'body':  json.dumps(request.get_json(force=True))}
    return lambdaGetSample.lambda_handler(event, [])

def convert_mp3_to_base64_ogg(file):
    try:
        mp3_file_path = f"./{file.filename}"
        file.save(mp3_file_path)
        
        # Load the MP3 file
        audio = AudioSegment.from_mp3(mp3_file_path)
        
        # Create a BytesIO object to hold the OGG data
        ogg_buffer = io.BytesIO()
        
        # Export the audio data to the OGG format and write it to the BytesIO object
        audio.export(ogg_buffer, format="ogg")
        
        # Get the binary data from the BytesIO object
        ogg_data = ogg_buffer.getvalue()
        
        # Encode the binary data to base64
        base64_ogg = base64.b64encode(ogg_data).decode('utf-8')
        
        # Create the data URI string
        base64_ogg_str = f"data:audio/ogg;base64,{base64_ogg}"
        print("Converted to base64 OGG...")
        return {"output": base64_ogg_str, 'sampleRate': audio.frame_rate}
    except Exception as e:
        print("Conversion to ogg failed with error:")
        print(e)
        return {"output": str(e)}

@app.route(rootPath+'/GetAccuracyFromRecordedAudio', methods=['POST'])
def GetAccuracyFromRecordedAudio():
    file = request.files['file']
    title = request.form['title']
    language = request.form['language']
    fileDict = convert_mp3_to_base64_ogg(file)
    event = {'body': json.dumps({"title": title, "base64Audio":fileDict["output"],"language": language, "sampleRate": fileDict['sampleRate']})}
    lambda_correct_output = lambdaSpeechToScore.lambda_handler(event, [])
    return lambda_correct_output


if __name__ == "__main__":
    language = 'de'
    print(os.system('pwd'))
    webbrowser.open_new('http://127.0.0.1:3000/')
    app.run(host="0.0.0.0", port=3000)
