import base64
import json
import wave
import os
import subprocess
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
from tornado.options import define, options, parse_command_line
from vosk import Model, KaldiRecognizer

from tools import utils
"""tornado-asr语音识别模型，2020-11-6 """

define("port", default=10013, help="run on the given port", type=int)

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.set_default_header()
    def set_default_header(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')


class IndexHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write('welcome to you!')

class AsrHandler(BaseHandler):

    def post(self):
        # global conversation
        voice_data = self.get_argument('voice')
        tmpfile = utils.write_temp_file(base64.b64decode(voice_data), '.mp3','/home/asrdatabases')    
        fname, _= os.path.splitext(tmpfile)
        nfile = fname + '-16k.wav'
        # downsampling
        soxCall = 'sox ' + tmpfile + \
                    ' ' + nfile + ' rate 16k'
        subprocess.call([soxCall], shell=True, close_fds=True)
        utils.check_and_delete(tmpfile)
        wf = wave.open(nfile, "rb")

        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            # print ("Audio file must be WAV format mono PCM.")
            # exit (1)
            res = {"code": 1, "err_msg": "Audio file must be WAV format mono PCM."}
            self.write(json.dumps(res))
        else:

            model = Model("model")
            rec = KaldiRecognizer(model, wf.getframerate())

            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    # print(rec.Result())
                    pass
                else:
                    # print(rec.PartialResult())
                    pass
            res_json = rec.FinalResult()
            res_dict = json.loads(res_json)
            text=res_dict.get('text',-1)
            text=''.join(text.split())
            if len(text) < 3:
                res = {"code": 1, "result":"Invalid audio Please Try again."} 
                self.write(json.dumps(res))
            else:
                res = {"code": 0, "result":text} 
                self.write(json.dumps(res))
    
        self.finish()

if __name__ == '__main__':

    settings = {"debug": True}
    tornado.options.parse_command_line()

    app = tornado.web.Application(handlers=[
        (r"/", IndexHandler),
        (r"/asr", AsrHandler),
    ], **settings)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    print("Please click http://localhost:{}".format(options.port))
    tornado.ioloop.IOLoop.instance().start()

