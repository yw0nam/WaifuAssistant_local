from vtube_studio import Char_control
from time import ctime
import speech_recognition as sr
import soundfile as sf
import pyaudio
import scipy.io.wavfile as wav
import requests
import random
import logging
from openai import OpenAI
from utils import chat
logging.getLogger("requests").setLevel(logging.WARNING) # make requests logging only important stuff
logging.getLogger("urllib3").setLevel(logging.WARNING) # make requests logging only important stuff

# initialize Vstudio Waifu Controller
print('Initializing... Vtube Studio')
# waifu = Char_control(port=8003, plugin_name='MyBitchIsAI', plugin_developer='HRNPH')
asr_client = OpenAI(api_key="token-abc123", base_url="http://localhost:8002/v1/")
print('Initialized')

# Define Varaibles
chara = 'ナツメ'
history= []
split_counter = 0
situation = ""
backend_address = "http://localhost:8001"

while True:
    print("Recording started...")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Press Enter to record your voice\nIf you want to end the conversation, type 'end'\nor If you want to reset the conversation history, enter 'reset'")
        user_input = input()
        if user_input == "end":
            break
        elif user_input == 'reset':
            history = []
        print("Say something!")
        audio = r.listen(source)
    # Save the recording as a WAV file
    transcript = asr_client.audio.transcriptions.create(
        model="large-v3", file=audio.get_wav_data()
    ).text 
    # ----------- Create Response --------------------------
    answer, history = chat(transcript, chara, situation, history) # send message to api

    print("**")
    if len(answer) > 2:
        use_answer = answer

        # ------------------------------------------------------
        print(f'{answer}')
        # if answer.strip().endswith(f'{chara}:') or answer.strip() == '':
        #     continue # skip audio processing if the answer is just the name (no talking)

        # ----------- Waifu Create Talking Audio -----------------------
        wav = requests.post(backend_address+'/request_tts', 
            json={
                'chara': chara,
                'chara_response': answer.split(':')[1]+ '。'
            }
        )
        audio_filepath = './audio_cache/dialog_cache.wav'
        with open(audio_filepath, "wb") as f:
            f.write(wav.content)
        # --------------------------------------------------
        # if emo:  ## express emotion
        #     waifu.express(emo)  # express emotion in Vtube Studio
        # waifu.express(random.choice(['sad']))  # express emotion in Vtube Studio
        # ----------- Waifu Talking -----------------------
        # play audio directly from cache
        p = pyaudio.PyAudio()
        data, samplerate = sf.read('./audio_cache/dialog_cache.wav', dtype='float32')
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=samplerate,
                        output=True)
        stream.write(data.tobytes())
        stream.stop_stream()
        stream.close()

print("Save the conversation result? Y\\N")
save = input()
if save == 'Y':
    current_time = "_".join(ctime().split())
    print(requests.post(backend_address + '/request_store_to_db',
        json={
            'chara': chara,
            'messages': "||".join(list(map(lambda x: x['content'], history))),
            'document': "\n".join(list(map(lambda x: x['content'], history))),
            'id': current_time
        }
    ))