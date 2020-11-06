#!/usr/bin/env python3

import json
import os
import sys
import asyncio
import pathlib
import websockets
import concurrent.futures
import logging
from vosk import Model, KaldiRecognizer


# Enable loging if needed
#
# logger = logging.getLogger('websockets')
# logger.setLevel(logging.INFO)
# logger.addHandler(logging.StreamHandler())

vosk_interface = os.environ.get('VOSK_SERVER_INTERFACE', '0.0.0.0')
vosk_port = int(os.environ.get('VOSK_SERVER_PORT', 10012))
vosk_model_path = os.environ.get('VOSK_MODEL_PATH', 'model')
vosk_sample_rate = float(os.environ.get('VOSK_SAMPLE_RATE', 16000))

if len(sys.argv) > 1:
   vosk_model_path = sys.argv[1]

# Gpu part, uncomment if vosk-api has gpu support
#
# from vosk import GpuInit, GpuInstantiate
# GpuInit()
# def thread_init():
#     GpuInstantiate()
# pool = concurrent.futures.ThreadPoolExecutor(initializer=thread_init)

model = Model(vosk_model_path)
pool = concurrent.futures.ThreadPoolExecutor((os.cpu_count() or 1))
loop = asyncio.get_event_loop()

def process_chunk(rec, message):
    if message == '{"eof" : 1}':
        return rec.FinalResult(), True
    elif rec.AcceptWaveform(message):
        return rec.Result(), False
    else:
        return rec.PartialResult(), False

async def recognize(websocket, path):

    rec = None
    phrase_list = None
    sample_rate = vosk_sample_rate
    re_text = ''

    while True:

        message = await websocket.recv()

        # Load configuration if provided
        if isinstance(message, str) and 'config' in message:
            jobj = json.loads(message)['config']
            if 'phrase_list' in jobj:
                phrase_list = jobj['phrase_list']
            if 'sample_rate' in jobj:
                sample_rate = float(jobj['sample_rate'])
            continue

        # Create the recognizer, word list is temporary disabled since not every model supports it
        if not rec:
            if phrase_list:
                 rec = KaldiRecognizer(model, sample_rate, json.dumps(phrase_list))
            else:
                 rec = KaldiRecognizer(model, sample_rate)

        response, stop = await loop.run_in_executor(pool, process_chunk, rec, message)
        if 'text' in response:
            text = json.loads(response)['result']
            #result_te = json.loads(response)['text']
            if len(text) < 4:
                await websocket.send(re_text)  
                continue
            #text = ''.join(text.split())
            for i in range(len(text)):
                
                if i>0:
                    last_time = text[i-1]['end']
                    now_time = text[i]['start']
                    in_time = now_time - last_time
                    if in_time > 0.7:
                        n_text = l_text + '，' + text[i]['word']
                    else:
                        n_text = l_text + text[i]['word']
                    l_text = n_text
                else:
                    l_text = re_text + text[i]['word']
            re_text = l_text + '。'

            
            await websocket.send(re_text)
           
        else:
            part_text = json.loads(response)['partial']
            part_text = re_text + ''.join(part_text.split())
            await websocket.send(part_text)
        if stop: break

start_server = websockets.serve(
    recognize, vosk_interface, vosk_port)

loop.run_until_complete(start_server)
loop.run_forever()
