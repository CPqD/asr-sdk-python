# -*- coding: utf-8 -*-
#
#  Copyright 2017 CPqD. All rights reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
"""
@author: Akira Miasato

Main Speech Recognizer class:
    http://speech-doc.cpqd.com.br/asr/get_started/sdks.html
"""
from sys import stderr
from threading import Condition, Thread
from base64 import b64encode
import copy

from .listener import RecognitionListener
from .logger import Logger
from .websocket_api import ASRClient, start_recog_msg, define_grammar_msg
from .websocket_api import send_audio_msg, cancel_recog_msg
from .language_model_list import LanguageModelList


class RecognitionException(Exception):
    def __init__(self, c, m):
        super(RecognitionException, self).__init__(m)
        self.code = c


class SpeechRecognizer:
    """
    Class which recognizes speech and returns structured results.

    Each instance represents a single recognition session in the configured
    server.

    For an example of use, see the example in:
        http://speech-doc.cpqd.com.br/asr/get_started/sdks.html
    """
    def __init__(self, serverUrl, credentials=("", ""),
                 alias="PySpeechRecognizer",
                 logStream=stderr,
                 recogConfig=None,
                 userAgent=None,
                 listener=RecognitionListener(),
                 audioSampleRate=8000,
                 audioEncoding='pcm',
                 maxWaitSeconds=30,
                 connectOnRecognize=False,
                 autoClose=False,
                 logLevel="warning"):
        assert audioSampleRate in [8000, 16000]
        assert audioEncoding in ["pcm", "wav", "raw"]
        assert (isinstance(listener, RecognitionListener))
        self._serverUrl = serverUrl
        self._user = credentials[0]
        self._password = credentials[1]
        self._sessionConfig = recogConfig
        self._userAgent = userAgent
        self._listener = listener
        self._audioSampelRate = audioSampleRate
        self._audioEncoding = audioEncoding
        self._maxWaitSeconds = maxWaitSeconds
        self._connectOnRecognize = connectOnRecognize
        self._autoClose = autoClose
        self._logger = Logger(logStream, alias, logLevel)
        self._cv_define_grammar = Condition()
        self._cv_start_recog = Condition()
        self._cv_send_audio = Condition()
        self._cv_wait_recog = Condition()
        self._cv_wait_cancel = Condition()
        self._ws = None
        self._sendAudioThread = None
        self._is_recognizing = False
        self._joinThread = False

        # Recognition attributes
        self._audioSource = None
        self._recogConfig = None

        if not connectOnRecognize:
            self._connect()

    def __del__(self):
        self.close()

    def _connect(self):
        if self._ws is None:
            credentials = b64encode(b':'.join([self._user.encode(),
                                               self._password.encode()]))
            credentials = b"Basic " + credentials
            headers = [("Authorization", credentials.decode())]
            self._ws = ASRClient(url=self._serverUrl,
                                 cv_define_grammar=self._cv_define_grammar,
                                 cv_start_recog=self._cv_start_recog,
                                 cv_send_audio=self._cv_send_audio,
                                 cv_wait_recog=self._cv_wait_recog,
                                 cv_wait_cancel=self._cv_wait_cancel,
                                 listener=self._listener,
                                 user_agent=self._userAgent,
                                 config=self._sessionConfig,
                                 logger=self._logger,
                                 headers=headers)
            self._ws.connect()

    def _send_audio_loop(self):
        with self._cv_send_audio:
            while self._ws.status not in ["LISTENING",
                                          "NO_INPUT_TIMEOUT",
                                          "ABORTED"]:
                self._logger.debug("Waiting for send audio notify")
                self._cv_send_audio.wait(.5)  # Break loop as soon as ready
            bytestr = next(self._audioSource)
            for x in self._audioSource:
                if self._ws.status != "LISTENING":
                    bytestr = x
                    break
                if self._joinThread:
                    bytestr = x
                    break
                self._ws.send(send_audio_msg(bytestr, False), binary=True)
                self._logger.debug("Send audio")
                bytestr = x
            self._ws.send(send_audio_msg(bytestr, True), binary=True)
            self._logger.debug("Send audio")

    def _disconnect(self):
        if self._ws is not None:
            try:
                self._ws.disconnect()
            except Exception as e:
                self._logger.warning("Non-critical error on disconnect: "
                                     "{}".format(e))
            self._ws = None

    def waitRecognitionResult(self):
        if self._ws is None:
            msg = "Trying to wait recognition with closed recognizer!"
            self._logger.warning(msg)
            return []
        if not self._is_recognizing:
            msg = "Trying to wait recognition without having one started!"
            self._logger.warning(msg)
            if self._autoClose:
                self.close()
            return []
        with self._cv_wait_recog:
            self._cv_wait_recog.wait(self._maxWaitSeconds)
            if self._ws.status == "ABORTED":
                self._ws.recognition_list = []
                return []
            elif self._ws.status != "RECOGNIZED":
                msg = "Wait recognition timeout after " \
                      "{} seconds".format(self._maxWaitSeconds)
                self._logger.warning(msg)
                self.cancelRecognition()
                if self._autoClose:
                    self.close()
                raise RecognitionException("FAILURE", msg)
            else:
                self._ws.onWaitRecognitionFinished()
                ret = copy.deepcopy(self._ws.recognition_list)
                # By specification, we clean the recognition list after
                # calling waitRecognitionResult
                self._ws.recognition_list = []
                if self._sendAudioThread is not None:
                    self._finishRecognition()
                if self._autoClose:
                    self.close()
                return ret

    def recognize(self, audio_source, lm_list, config=None):
        assert(isinstance(lm_list, LanguageModelList))
        if self._ws is None:
            self._connect()
        if self._is_recognizing:
            msg = "Last recognition is still pending."
            self._logger.error(msg)
            raise RecognitionException("FAILURE", msg)
        self._is_recognizing = True
        if not self._ws.isConnected():
            with self._cv_start_recog:
                self._cv_start_recog.wait(self._maxWaitSeconds)
        if self._ws.status != "IDLE":
            self._logger.warning("Recognize timeout after {} "
                                 "seconds".format(self._maxWaitSeconds))
            return
        self._recogConfig = config
        self._audioSource = audio_source
        lm_uris = []
        for lm in lm_list._lm_list:
            if type(lm) == str:
                lm_uris.append(lm)
            elif type(lm) == tuple:
                msg = define_grammar_msg(*lm)
                self._ws.send(msg, binary=True)
                self._logger.debug(b"SEND: " + msg)
                with self._cv_define_grammar:
                    self._cv_define_grammar.wait(self._maxWaitSeconds)
                lm_uris.append('session:' + lm[0])
        msg = start_recog_msg(lm_uris)
        self._ws.send(msg, binary=True)
        self._logger.debug(b"SEND: " + msg)
        self._sendAudioThread = Thread(target=self._send_audio_loop)
        self._sendAudioThread.start()

    def _finishRecognition(self):
        self._joinThread = True
        self._sendAudioThread.join(self._maxWaitSeconds)
        self._joinThread = False
        if self._sendAudioThread.isAlive():
            self._logger.warning("Send audio thread join timeout after "
                                 "{} seconds".format(self._maxWaitSeconds))
        self._sendAudioThread = None
        self._is_recognizing = False

    def cancelRecognition(self):
        if self._sendAudioThread is not None:
            if not self._ws.terminated:
                self._ws.send(cancel_recog_msg(), binary=True)
#                with self._cv_wait_recog:
#                    self._cv_wait_recog.wait(self._maxWaitSeconds)
#                if self._ws.status != "IDLE":
#                    self._logger.warning("Timeout on waiting Cancel Recognition")
            self._finishRecognition()
            self._ws.recognition_list = []  # Clear result after cancelling
        else:
            msg = "No recognition is being performed to be cancelled."
            raise RecognitionException("FAILURE", msg)

    def close(self):
        try:
            self.cancelRecognition()
        except RecognitionException:
            pass
        else:
            self._logger.warning("Cancelled active recognition on close.")
        self._disconnect()
