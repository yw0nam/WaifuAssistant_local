import requests

def chat(msg, chara, situation, history):
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
    history = r
    return r[-1]['content'], history