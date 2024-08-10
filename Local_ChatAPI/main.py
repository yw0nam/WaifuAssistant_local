print('Initializing... Dependencies')
from vtube_studio import Char_control
import speech_recognition as sr
import soundfile as sf
import pyaudio
import scipy.io.wavfile as wav
import requests
import random
import logging
from openai import OpenAI
logging.getLogger("requests").setLevel(logging.WARNING) # make requests logging only important stuff
logging.getLogger("urllib3").setLevel(logging.WARNING) # make requests logging only important stuff

# initialize Vstudio Waifu Controller
print('Initializing... Vtube Studio')
waifu = Char_control(port=8003, plugin_name='MyBitchIsAI', plugin_developer='HRNPH')
client = OpenAI(api_key="token-abc123", base_url="http://localhost:8002/v1/")
print('Initialized')

# Define Varaibles
chara = 'ナツメ'
history= []
split_counter = 0
situation = ""
    
# chat api
def chat(msg, history=history, reset=False):
    if reset:
        history = []
    try:
        if history == []:
            params = {
                'chara': chara,
                'query': msg,
                'situation': situation
            }
            r = requests.post('http://localhost:8001'+'/init_prompt_and_comp', json=params).json()
        else:
            params = {
                'chara': chara,
                'history': history,
                'query': msg,
            }
            r = requests.post('http://localhost:8001'+'/request_completion', json=params).json()
    except requests.exceptions.ConnectionError as e:
        print('--------- Exception Occured ---------')
        print('if you have run the server on different device, please specify the ip address of the server with the port')
        print('Example: http://192.168.1.112:8267 or leave it blank to use localhost')
        print('***please specify the ip address of the server with the port*** at:')
        print(f'*Line {e.__traceback__.tb_lineno}: {e}')
        print('-------------------------------------')
        exit()
    history = r
    return r[-1]['content']

while True:
    # con = str(input("You: "))
    # if con.lower() == 'exit':
    #     print('Stopping...')
    #     break # exit prototype

    # if con.lower() == 'reset':
    #     print('Resetting...')
    #     print(chat('None', None, reset=True))
    #     continue # reset story skip to next loop
    
    print("Recording started...")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something!")
        user_input = input()
        audio = r.listen(source)
    # Save the recording as a WAV file
    transcript = client.audio.transcriptions.create(
        model="large-v3", file=audio.get_wav_data()
    ).text 
    # ----------- Create Response --------------------------
    answer = chat(transcript, history) # send message to api

    print("**")
    if len(answer) > 2:
        use_answer = answer

        # ------------------------------------------------------
        print(f'{answer}')
        # if answer.strip().endswith(f'{chara}:') or answer.strip() == '':
        #     continue # skip audio processing if the answer is just the name (no talking)

        # ----------- Waifu Create Talking Audio -----------------------
        wav = requests.post('http://localhost:8001'+'/request_tts', 
            json={
                'chara': chara,
                'chara_response': answer.split(':')[1]+ '。'
            }
        )
        audio_filepath = './audio_cache/dialog_cache.wav'
        with open(audio_filepath, "wb") as f:
            f.write(wav.content)
        # --------------------------------------------------

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

        # --------------------------------------------------
        # if emo:  ## express emotion
        #     waifu.express(emo)  # express emotion in Vtube Studio
        waifu.express(random.choice(['sad']))  # express emotion in Vtube Studio
        # --------------------------------------------------