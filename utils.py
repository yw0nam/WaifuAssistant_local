import requests

def chat(backend_address, history, generation_config:dict={'temperature': 0.6, "frequency_penalty": 0.4, 'presence_penalty': 0.4, 'top_p':0.95, 'stream':True}):
    params = {
        'history': history,
        'generation_config': generation_config
    }
    r = requests.post(backend_address+'/request_completion', json=params, stream=True)
    return r