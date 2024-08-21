import requests

def chat(msg, chara, situation, system, history, generation_config:dict={'temperature': 0.4, "frequency_penalty": 0.9}):
    if history == []:
        params = {
            'chara': chara,
            'query': msg,
            'situation': situation,
            'system': system,
            'generation_config': generation_config
        }
        r = requests.post('http://localhost:8001'+'/init_prompt_and_comp', json=params).json()
    else:
        params = {
            'chara': chara,
            'history': history,
            'query': msg,
            'generation_config': generation_config
        }
        r = requests.post('http://localhost:8001'+'/request_completion', json=params).json()
    history = r
    return r[-1]['content'], history