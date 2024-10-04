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

@app.route(rootPath+'/convert3gpToMp3', methods=['POST'])
def convert3gpToMp3():
    file = request.files['file']
    print(f"Received file: {file.filename}, Content-Type: {file.content_type}")
    convert_3gp_to_mp3(file)
    return {"output": "Conversion successful!"}


def convert_3gp_to_mp3(input_file_path):
    print("Converting 3gp to mp3:", input_file_path)
    try:
        ext = input_file_path.rsplit('.', 1)[1]
        print(ext)

        if ext.lower() == 'caf':
            print("Converting CAF to WAV:", input_file_path)
            audio = AudioSegment.from_file(input_file_path, format='caf')
            output_file_path = input_file_path.replace('.caf', '.mp3')
            audio.export(output_file_path, format='mp3')
            print(f"Conversion successful! File saved as: {output_file_path}")
            return

        # Load the 3gp file
        audio = AudioSegment.from_file(input_file_path, format="3gp")

        # Set the output file path
        output_file_path = input_file_path.rsplit('.', 1)[0] + ".mp3"

        # Export the audio as mp3
        audio.export(output_file_path, format="mp3")

        print(f"Conversion successful! File saved as: {output_file_path}")
    except Exception as e:
        print(f"An error occurred during conversion: {e}")
def convert_wav_to_base64_ogg(file):
    try:
        # Save the uploaded WAV file
        wav_file_path = f"./{file.filename}"
        file.save(wav_file_path)
        
        # Load the WAV file using pydub
        audio = AudioSegment.from_wav(wav_file_path)
        
        # Create a BytesIO object to hold the OGG data
        ogg_buffer = io.BytesIO()
        
        # Export the audio data to OGG format
        audio.export(ogg_buffer, format="ogg")
        
        # Get the binary data from the BytesIO object
        ogg_data = ogg_buffer.getvalue()
        
        # Encode the binary data to base64
        base64_ogg = base64.b64encode(ogg_data).decode('utf-8')
        
        # Create the data URI string
        base64_ogg_str = f"data:audio/ogg;base64,{base64_ogg}"
        print("Converted WAV to base64 OGG...")
        return {"output": base64_ogg_str, 'sampleRate': audio.frame_rate}
    except Exception as e:
        print(e)
        return {"output": str(e)}

def convert_3gp_to_base64_ogg(file):
    try:
        threegp_file_path = f"./{file.filename}"
        file.save(threegp_file_path)
        
        # Load the 3GP file
        audio = AudioSegment.from_file(threegp_file_path, format="3gp")
        
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
        print(e)
        return {"output": str(e)}




def convert_mp3_to_base64_ogg(file):
    try:
        # Save the uploaded file securely
        mp3_file_path = f"./{file.filename}"
        file.save(mp3_file_path)
 
        try:
            # Load the MP3 file
            audio = AudioSegment.from_mp3(mp3_file_path)
        except Exception as e:
            raise ValueError(f"Error loading MP3 file: {e}")
        
        # Create a BytesIO object to hold the OGG data
        ogg_buffer = io.BytesIO()
        
        try:
            # Export the audio data to the OGG format and write it to the BytesIO object
            audio.export(ogg_buffer, format="ogg")
        except Exception as e:
            raise ValueError(f"Error exporting to OGG format: {e}")
        
        # Get the binary data from the BytesIO object
        ogg_data = ogg_buffer.getvalue()
        
        # Encode the binary data to base64
        base64_ogg = base64.b64encode(ogg_data).decode('utf-8')
        
        # Create the data URI string
        base64_ogg_str = f"data:audio/ogg;base64,{base64_ogg}"
        print("Converted to base64 OGG...")
        return {"output": base64_ogg_str, 'sampleRate': audio.frame_rate}
    except Exception as e:
        print(e)
        return {"output": str(e)}

@app.route(rootPath+'/GetAccuracyFromRecordedAudio', methods=['POST'])
def GetAccuracyFromRecordedAudio():
    file = request.files['file']
    title = request.form['title']
    transcription = request.form.get('transcription', None)
    language = request.form['language']
    print(f"Received file: {file.filename}, Content-Type: {file.content_type}")

    # Save the uploaded file to a temporary path
    temp_file_path = f"./{file.filename}"
    file.save(temp_file_path)

    # Try to read the file with pydub
    try:
        if file.content_type == 'audio/webm':
            audio = AudioSegment.from_file(temp_file_path, format='webm')
        elif file.content_type == 'audio/ogg':
            audio = AudioSegment.from_file(temp_file_path, format='ogg')
        elif file.content_type == 'audio/wav':
            audio = AudioSegment.from_file(temp_file_path, format='wav')
        else:
            # Attempt to let pydub/ffmpeg detect the format
            audio = AudioSegment.from_file(temp_file_path)
    except Exception as e:
        print(f"Could not read audio file: {e}")
        return {"output": f"Could not read audio file: {e}"}

    # Proceed to export to OGG
    ogg_buffer = io.BytesIO()
    audio.export(ogg_buffer, format="ogg")
    ogg_data = ogg_buffer.getvalue()
    base64_ogg = base64.b64encode(ogg_data).decode('utf-8')
    base64_ogg_str = f"data:audio/ogg;base64,{base64_ogg}"
    print("Converted audio to base64 OGG...")

    event = {
        'body': json.dumps({
            "title": title,
            "base64Audio": base64_ogg_str,
            "language": language,
            "sampleRate": audio.frame_rate,
            "transcription": transcription
        })
    }
    lambda_correct_output = lambdaSpeechToScore.lambda_handler(event, [])
    return lambda_correct_output

if __name__ == "__main__":
    language = 'de'
    print(os.system('pwd'))
    webbrowser.open_new('http://127.0.0.1:3000/')
    app.run(host="0.0.0.0", port=3000)
