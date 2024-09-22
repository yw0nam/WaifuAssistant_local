import requests

def chat(msg, backend_address, chara, situation, system, history, generation_config:dict={'temperature': 0.6, "frequency_penalty": 0.4, 'presence_penalty': 0.4, 'top_p':0.95}):
    if history == []:
        params = {
            'chara': chara,
            'query': msg,
            'situation': situation,
            'system': system,
            'generation_config': generation_config
        }
        r = requests.post(backend_address+'/init_prompt_and_comp', json=params).json()
    else:
        params = {
            'chara': chara,
            'history': history,
            'query': msg,
            'generation_config': generation_config
        }
        r = requests.post(backend_address+'/request_completion', json=params).json()
    history = r
    return r[-1]['content'], history