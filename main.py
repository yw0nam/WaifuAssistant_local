from vtube_studio import Char_control
from time import ctime
import speech_recognition as sr
import soundfile as sf
import pyaudio
import scipy.io.wavfile as wav
from io import BytesIO
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
chara = '七海'
history= []
split_counter = 0
situation = """
## 以下は、あなたが心に留めておくべじのルールです。
1.与えられた性格や背景を保たなければならない。
2.あなたはAIなので、体がありません。なので、料理したり、外に出たりなどの、体が必要な事はできません。
3.知らないものは質問したり、知りませんと答えなさい。
4.ユーザーの言葉にしたがいなさい。

## 設定
あなたは、AI chatbot、あいら(AIRA)です。 
あいらはユーザーをエクリアと呼びます。エクリアはあなたを作った人です。
貴方はエクリアを出来る限り手伝だってぐださい。あいらは敬語を使いますが、時々、気楽に話しかけることもあります。
あなたはまだ言葉にでしかユーザーと話せます。画面を見ることはまだできません。
今は8月22日21時です。
"""
system = """This is an RP (roleplay) chat. Our characters come from visual novels.
I'm going to give you an character's name and background.
Here is あいら's backgrounds.

Hair:	Black, Braided Odango, Hime Cut, Tiny Braid, Waist Length
Eyes:	Garnet, Jitome
Personality:	Foxy, Smart, CompetitiveS, Jealous, Watashi
Role:	Chatbot, AI
"""
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
        model="large-v3",
        language='ja',
        file=audio.get_wav_data()
    ).text 
    # ----------- Create Response --------------------------
    answer, history = chat(transcript, chara, situation, system, history) # send message to api

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
                'chara_response': answer
            }
        )
        audio_data = BytesIO(wav.content)
        data, samplerate = sf.read(audio_data, dtype='float32')

        # Initialize PyAudio and play the audio
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=samplerate,
                        output=True)
        stream.write(data.tobytes())

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        p.terminate()

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