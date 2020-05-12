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
from time import time
import logging
import copy

from cpqdasr.recognizer_protocol import WS4PYClient
from cpqdasr.recognizer_protocol import (
    send_audio_msg,
    cancel_recog_msg,
    start_recog_msg,
    define_grammar_msg,
)

from .listener import RecognitionListener
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

    def __init__(
        self,
        server_url,
        credentials=("", ""),
        alias="PySpeechRecognizer",
        log_stream=stderr,
        recog_config=None,
        user_agent=None,
        listener=RecognitionListener(),
        audio_sample_rate=8000,
        audio_encoding="pcm",
        max_wait_seconds=30,
        connect_on_recognize=False,
        auto_close=False,
    ):
        assert audio_sample_rate in [8000, 16000]
        assert audio_encoding in ["pcm", "wav", "raw"]
        assert isinstance(listener, RecognitionListener)
        self._serverUrl = server_url
        self._user = credentials[0]
        self._password = credentials[1]
        self._session_config = recog_config
        self._user_agent = user_agent
        self._listener = listener
        self._audio_sample_rate = audio_sample_rate
        self._audio_encoding = audio_encoding
        self._max_wait_seconds = max_wait_seconds
        self._connect_on_recognize = connect_on_recognize
        self._auto_close = auto_close
        self._logger = logging.getLogger("cpqdasr")
        self._cv_define_grammar = Condition()
        self._cv_create_session = Condition()
        self._cv_send_audio = Condition()
        self._cv_wait_recog = Condition()
        self._cv_wait_cancel = Condition()
        self._ws = None
        self._send_audio_thread = None
        self._is_recognizing = False
        self._join_thread = False

        # Recognition attributes
        self._audio_source = None
        self._recog_config = None

        if not connect_on_recognize:
            self._connect()

    def __del__(self):
        self.close()

    def _connect(self):
        if self._ws is None:
            credentials = b64encode(
                b":".join([self._user.encode(), self._password.encode()])
            )
            credentials = b"Basic " + credentials
            headers = [("Authorization", credentials.decode())]
            self._ws = WS4PYClient(
                url=self._serverUrl,
                cv_define_grammar=self._cv_define_grammar,
                cv_create_session=self._cv_create_session,
                cv_send_audio=self._cv_send_audio,
                cv_wait_recog=self._cv_wait_recog,
                cv_wait_cancel=self._cv_wait_cancel,
                listener=self._listener,
                user_agent=self._user_agent,
                config=self._session_config,
                headers=headers,
            )
            self._ws.connect()

    def _send_audio_loop(self):
        with self._cv_send_audio:
            while self._ws.status not in ["LISTENING", "NO_INPUT_TIMEOUT", "ABORTED"]:
                self._logger.debug("Waiting for send audio notify")
                self._cv_send_audio.wait(0.5)  # Break loop as soon as ready
            try:
                b = next(self._audio_source)
            except StopIteration:
                self._logger.warning("Empty audio source!")
                self._ws.send(send_audio_msg(b"", True), binary=True)
                return
            self._ws._time_wait_recog = time()
            for x in self._audio_source:
                if self._ws.status != "LISTENING":
                    b = x
                    break
                if self._join_thread:
                    b = x
                    break
                self._ws.send(send_audio_msg(b, False), binary=True)
                self._logger.debug("Send audio")
                b = x
            self._ws.send(send_audio_msg(b, True), binary=True)
            self._logger.debug("Send audio")

    def _disconnect(self):
        if self._ws is not None:
            try:
                self._ws.disconnect()
            except Exception as e:
                self._logger.warning(
                    "Non-critical error on disconnect: " "{}".format(e)
                )
            self._ws = None

    def wait_recognition_result(self):
        if self._ws is None:
            msg = "Trying to wait recognition with closed recognizer!"
            self._logger.warning(msg)
            return []
        if not self._is_recognizing:
            msg = "Trying to wait recognition without having one started!"
            self._logger.warning(msg)
            if self._auto_close:
                self.close()
            return []
        with self._cv_wait_recog:
            self._cv_wait_recog.wait(self._max_wait_seconds)
            if self._ws.status == "ABORTED":
                self._ws.recognition_list = []
                return []
            elif self._ws.status not in [
                "RECOGNIZED",
                "NO_MATCH",
                "NO_SPEECH",
                "NO_INPUT_TIMEOUT",
            ]:
                msg = "Wait recognition timeout after " "{} seconds".format(
                    self._max_wait_seconds
                )
                self._logger.warning(msg)
                self.cancel_recognition()
                if self._auto_close:
                    self.close()
                raise RecognitionException("FAILURE", msg)
            else:
                self._ws.on_wait_recognition_finished()
                ret = copy.deepcopy(self._ws.recognition_list)
                # By specification, we clean the recognition list after
                # calling wait_recognition_result
                self._ws.recognition_list = []
                if self._send_audio_thread is not None:
                    self._finish_recognition()
                if self._auto_close:
                    self.close()
                return ret

    def recognize(self, audio_source, lm_list, config=None):
        assert isinstance(lm_list, LanguageModelList)
        if self._ws is None:
            self._connect()
        if self._is_recognizing:
            msg = "Last recognition is still pending."
            self._logger.error(msg)
            raise RecognitionException("FAILURE", msg)
        self._is_recognizing = True
        if not self._ws.is_connected():
            with self._cv_create_session:
                self._cv_create_session.wait(self._max_wait_seconds)
        if self._ws.status != "IDLE":
            self._logger.warning(
                "Recognize timeout after {} " "seconds".format(self._max_wait_seconds)
            )
            return
        self._recog_config = config
        self._audio_source = audio_source
        lm_uris = []
        for lm in lm_list._lm_list:
            if type(lm) == str:
                lm_uris.append(lm)
            elif type(lm) == tuple:
                msg = define_grammar_msg(*lm)
                self._ws._time_define_grammar = time()
                self._ws.send(msg, binary=True)
                self._logger.debug(b"SEND: " + msg)
                with self._cv_define_grammar:
                    self._cv_define_grammar.wait(self._max_wait_seconds)
                lm_uris.append("session:" + lm[0])
        msg = start_recog_msg(lm_uris, self._recog_config)
        self._ws.send(msg, binary=True)
        self._logger.debug(b"SEND: " + msg)
        self._send_audio_thread = Thread(target=self._send_audio_loop)
        self._send_audio_thread.start()

    def _finish_recognition(self):
        self._join_thread = True
        self._send_audio_thread.join(self._max_wait_seconds)
        self._join_thread = False
        if self._send_audio_thread.is_alive():
            self._logger.warning(
                "Send audio thread join timeout after "
                "{} seconds".format(self._max_wait_seconds)
            )
        self._send_audio_thread = None
        self._is_recognizing = False

    def cancel_recognition(self):
        if self._send_audio_thread is not None:
            if not self._ws.terminated:
                self._ws.send(cancel_recog_msg(), binary=True)
            #                with self._cv_wait_recog:
            #                    self._cv_wait_recog.wait(self._max_wait_seconds)
            #                if self._ws.status != "IDLE":
            #                    self._logger.warning("Timeout on waiting Cancel Recognition")
            self._finish_recognition()
            self._ws.recognition_list = []  # Clear result after cancelling
        else:
            msg = "No recognition is being performed to be cancelled."
            raise RecognitionException("FAILURE", msg)

    def close(self):
        try:
            self.cancel_recognition()
        except RecognitionException:
            pass
        else:
            self._logger.warning("Cancelled active recognition on close.")
        self._disconnect()
