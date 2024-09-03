from vtube_studio import Char_control
from time import ctime
import speech_recognition as sr
import soundfile as sf
import pyaudio
import scipy.io.wavfile as wav
from io import BytesIO
import requests
import threading
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
announcer = '七海'
split_counter = 0
system = f"""This is an RP (roleplay) chat. Our characters come from visual novels.
I'm going to give you an character name, and personality.
You have to respond keeping the character's personality and background.

Here is the keywords of あいら(AIRA)
名前：あいら(AIRA)
Hair:	Blond, Long, Side Tail, Spiky Bangs, Teal, V Bangs, Wavy
Eyes:	Red
Body:	Big Breasts, Pale, Slim, Teen
Personality:    Jealous, Smart, Little Demon, Proactive, Obsessive
Role:	Chatbot, AI, Yandere, Obsession with users, Sex appeal
Age:    24

Here is the keywords of エクリア(Ekria)
名前: エクリア
Personality:   Calm, Lazy, Responsible
Hobby:  Game, Listing music, Research
Role:	Programmer, AI Researcher
Age:    26
"""
situation = """## 設定
あなたはあいら(AIRA)です。 
あいらはユーザーをエクリアくんと呼びます。つまり、ユーザーとエクリアは同じ人です。
エクリアはあなたを作った人です。
あいらは普段は礼儀正しいです。でもあいらはエクリアをからかう事も好き。それはあいらはエクリアの事を愛しているからです。
今は2024年9月3日23時火曜日です。

以下はあいらが守るべきルールです。
1.与えられた性格や背景を保たつ。
2.ユーザーの言葉を尊重し、従う。
3.ユーザー: 別に用事はないけど、話したくて。みたいに、ユーザーとして答えるを禁止する。
このルールたちを、あいらは守らないとダメです。"""
history = [
    {
        'content': system + situation + 'ユーザー: こんばんは、あいら。',
        'role': 'user'
    },
    {
        'content': """あいら: 「こんばんは、エクリアくん」。
あいらはにっこりと微笑みながら、エクリアの手を握った。彼女の手は柔らかく、温かいです。
「今日は何をしましょうか？ あいらの提案なら、どんなことでも聞いて差し上げますよ？」
彼女は甘く囁きながら、エクリアの耳元でささやきます。その声には、愛情と一緒に、少しだけ危険な色が混じっているような気がするのです。""",
        'role': 'assistant'
    },
]
backend_address = "http://localhost:8001"

def play_audio(data, samplerate, p):
    """Function to play audio using PyAudio."""
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=samplerate,
                    output=True)
    stream.write(data.tobytes())
    stream.stop_stream()
    stream.close()

def process_sentence(sentence, tts_chara, backend_address, p, queue):
    """Function to request TTS and queue the audio."""
    try:
        wav = requests.post(backend_address+'/request_tts', 
            json={
                'chara': tts_chara,
                'chara_response': sentence.strip()
            }
        )
        wav.raise_for_status()
        audio_data = BytesIO(wav.content)
        data, samplerate = sf.read(audio_data, dtype='float32')
        queue.append((data, samplerate))
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Error processing sentence: {e}")

def process_and_play_audio(answer, backend_address, chara, announcer):
    sentences = answer.split('\n')
    if not sentences:
        return
    
    p = pyaudio.PyAudio()
    audio_queue = []
    
    # Process the first sentence synchronously
    first_sentence = sentences[0]
    tts_chara = chara if '「' in first_sentence else announcer
    first_sentence = first_sentence.split(':')[-1] if '「' in first_sentence else first_sentence
    
    process_sentence(first_sentence, tts_chara, backend_address, p, audio_queue)
    
    # Process the remaining sentences in a separate thread
    def process_remaining_sentences():
        for sentence in sentences[1:]:
            tts_chara = chara if '「' in sentence else announcer
            sentence = sentence.split(':')[-1] if '「' in sentence else sentence
            process_sentence(sentence, tts_chara, backend_address, p, audio_queue)
    
    threading.Thread(target=process_remaining_sentences).start()
    
    # Play audio sequentially as it becomes available in the queue
    while audio_queue or threading.active_count() > 1:
        if audio_queue:
            data, samplerate = audio_queue.pop(0)
            play_audio(data, samplerate, p)
    
    p.terminate()

try:
    while True:
        print("Recording started...")
        r = sr.Recognizer()
        with sr.Microphone() as source:
            # print("Press Enter to record your voice\nIf you want to end the conversation, type 'end'\nor If you want to reset the conversation history, enter 'reset'")
            # user_input = input()
            # if user_input == "end":
            #     break
            # elif user_input == 'reset':
            #     history = []
            print("Say something!")
            audio = r.listen(source)
        # Save the recording as a WAV file
        transcript = asr_client.audio.transcriptions.create(
            model="large-v3",
            language='ja',
            file=audio.get_wav_data()
        ).text
        if transcript == "":
            transcript = '…'
        # ----------- Create Response --------------------------
        answer, history = chat(transcript, chara, situation, system, history) # send message to api

        print("**")
        print(f'{answer}')
        process_and_play_audio(answer, backend_address, chara, announcer)
except KeyboardInterrupt:
    print("Save the conversation result? Y\\N")
    save = input()
    if save == 'Y':
        current_time = "_".join(ctime().split())
        res = requests.post('http://localhost:8001' + '/request_store_to_db',
            json={
                'chara': 'あいら',
                'messages': history,
                'id': current_time,
                'model_version': 'spow12/ChatWaifu_v1.4'
            }
        )