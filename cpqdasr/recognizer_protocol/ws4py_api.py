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

ASR Server ws4py connection handler
"""
from time import time
from sys import stderr
from threading import Condition
from ws4py.client.threadedclient import WebSocketClient
import logging

from ..recognizer.listener import RecognitionListener
from ..recognizer.result import (
    RecognitionResult,
    PartialRecognitionResult,
    AgeResult,
    GenderResponse,
    EmotionResponse,
)
from .protocol import (
    create_session_msg,
    set_parameters_msg,
    release_session_msg,
    parse_response,
)


class ASRClient(WebSocketClient):
    def __init__(
        self,
        url,
        cv_define_grammar,
        cv_create_session,
        cv_send_audio,
        cv_wait_recog,
        cv_wait_cancel,
        listener=RecognitionListener(),
        user_agent=None,
        config=None,
        debug=False,
        protocols=None,
        extensions=None,
        heartbeat_freq=None,
        ssl_options=None,
        headers=None,
    ):
        super(ASRClient, self).__init__(
            url, protocols, extensions, heartbeat_freq, ssl_options, headers
        )
        assert isinstance(cv_define_grammar, Condition)
        assert isinstance(cv_create_session, Condition)
        assert isinstance(cv_send_audio, Condition)
        assert isinstance(cv_wait_recog, Condition)
        assert isinstance(cv_wait_cancel, Condition)
        self._user_agent = user_agent
        self._listener = listener
        self._config = config
        self._logger = logging.getLogger("cpqdasr")
        self._status = "DISCONNECTED"
        self._cv_define_grammar = cv_define_grammar
        self._time_define_grammar = 0
        self._cv_create_session = cv_create_session
        self._time_create_session = 0
        self._cv_send_audio = cv_send_audio
        self._time_send_audio = 0
        self._cv_wait_recog = cv_wait_recog
        self._time_wait_recog = 0
        self._cv_wait_cancel = cv_wait_cancel
        self._cv_opened = Condition()
        self.recognition_list = []
        self.daemon = False

    def __del__(self):
        self.close()

    def is_connected(self):
        return self._status != "DISCONNECTED" and self._status != "WAITING_CONFIG"

    def _finish_connect(self):
        with self._cv_create_session:
            self._status = "IDLE"
            self._cv_create_session.notify_all()

    def _abort(self):
        self._status = "ABORTED"
        self._logger.debug("Aborting")
        with self._cv_define_grammar:
            self._logger.debug("Aborting define grammar")
            self._cv_define_grammar.notify_all()
        with self._cv_create_session:
            self._logger.debug("Aborting create session")
            self._cv_create_session.notify_all()
        with self._cv_send_audio:
            self._logger.debug("Aborting send audio")
            self._cv_send_audio.notify_all()
        with self._cv_wait_recog:
            self._logger.debug("Aborting wait recog")
            self._cv_wait_recog.notify_all()

    def disconnect(self):
        msg = release_session_msg()
        self.send(msg, binary=True)
        self._logger.debug(b"SEND: " + msg)

    @property
    def status(self):
        return self._status

    def on_wait_recognition_finished(self):
        self._status = "IDLE"

    def opened(self):
        msg = create_session_msg(self._user_agent)
        self.send(msg, binary=True)
        self._logger.debug(b"SEND: " + msg)

    def closed(self, code, reason=None):
        self._status = "DISCONNECTED"
        self._logger.info("ASR WS closed down {}, {}".format(code, reason))
        self._abort()

    def received_message(self, msg):
        # Parsing and returning error if bad response
        self._logger.debug(msg.data)
        call, h, b = parse_response(msg)
        age_scores = None
        gender_scores = None
        emotion_scores = None
        if call not in [
            "RESPONSE",
            "START_OF_SPEECH",
            "END_OF_SPEECH",
            "RECOGNITION_RESULT",
        ]:
            self.warning("Bad response:\n\n{}".format(call))
            return

        # Close if this is a RELEASE_SESSION response
        if "Method" in h:
            if h["Method"] == "RELEASE_SESSION":
                self.close()
                self._status = "DISCONNECTED"
                return
            if h["Method"] == "DEFINE_GRAMMAR":
                if h["Result"] == "SUCCESS":
                    self._logger.info(
                        "[TIMER] GrammarDefinitionTime: {} s".format(
                            time() - self._time_define_grammar
                        )
                    )
                    self._logger.debug("Grammar defined")
                    with self._cv_define_grammar:
                        self._cv_define_grammar.notify_all()
                else:
                    self._logger.warning(
                        "Error on defining grammar: " "{}".format(msg.data)
                    )
                    self._abort()
                return
            if h["Method"] == "START_RECOGNITION":
                if h["Result"] == "SUCCESS":
                    self._logger.debug("Starting recognition")
                    self._status = "LISTENING"
                    with self._cv_send_audio:
                        self._cv_send_audio.notify_all()
                else:
                    self._logger.warning(
                        "Error on start recognition: " "{}".format(msg.data)
                    )
                    self._abort()
                return

        if "Session-Status" in h:
            session_status = h["Session-Status"]
        else:
            session_status = h["Result"]

        # Treats the expected message when first "CREATE_SESSION" is sent
        if self._status == "DISCONNECTED":
            if call != "RESPONSE":
                self._logger.warning(
                    "Invalid received message on open "
                    "connection: expected RESPONSE, got "
                    "{}".format(session_status)
                )
            elif session_status != "IDLE":
                self._logger.warning(
                    "Invalid status on open connection: "
                    "expected IDLE, got "
                    "{}".format(session_status)
                )
            else:
                # Sends config message if set, otherwise the client will
                # use the server's default parameters
                if self._config is not None:
                    msg = set_parameters_msg(self._config)
                    self.send(msg, binary=True)
                    self._logger.debug(b"SEND: " + msg)
                    self._status = "WAITING_CONFIG"
                else:
                    self._finish_connect()
            return

        if call == "RESPONSE":
            # If returning from set_config, finishes connection process
            # and enables recognition
            if self._status == "WAITING_CONFIG":
                self._finish_connect()

            # If an error occurs, do not halt the client. Instead, log
            # the error
            elif "Error-Code" in h:
                self._logger.warning(
                    "Non-fatal error in API call: Code " "{}".format(h["Error-Code"])
                )
                self._abort()

            elif h["Method"] == "CANCEL_RECOGNITION":
                with self._cv_wait_cancel:
                    self._cv_wait_cancel.notify_all()
                    self._status = "IDLE"

            # Default response case which is ignored
            else:
                self._logger.info("Ignored {} response".format(h["Method"]))
            return

        if call == "RECOGNITION_RESULT":
            if h["Result-Status"] == "PROCESSING":
                self._listener.on_partial_recognition(
                    PartialRecognitionResult(0, b["alternatives"][0]["text"].strip())
                )
            else:
                if "alternatives" in b:
                    result = b["alternatives"]
                else:
                    result = []
                if "last_segment" in b:
                    last_segment = b["last_segment"]
                if "age_scores" in b:
                    age_scores = AgeResult(
                        event=b["age_scores"]["event"],
                        age=b["age_scores"]["age"],
                        p=b["age_scores"]["p"],
                        age_50=b["age_scores"]["age_50"],
                        age_80=b["age_scores"]["age_80"],
                        age_99=b["age_scores"]["age_99"],
                    )
                if "gender_scores" in b:
                    gender_scores = GenderResponse(
                        event=b["gender_scores"]["event"],
                        p=b["gender_scores"]["p"],
                        gender=b["gender_scores"]["gender"],
                    )
                if "emotion_scores" in b:
                    emotion_scores = EmotionResponse(
                        event=b["emotion_scores"]["event"],
                        p=b["emotion_scores"]["p"],
                        emotion=b["emotion_scores"]["emotion"],
                    )
                else:
                    last_segment = True
                self.recognition_list.append(
                    RecognitionResult(
                        result_code=h["Result-Status"],
                        speech_segment_index=0,
                        last_speech_segment=last_segment,
                        sentence_start_time_milliseconds=0,
                        sentence_end_time_milliseconds=0,
                        alternatives=result,
                        age_scores=age_scores,
                        gender_scores=gender_scores,
                        emotion_scores=emotion_scores,
                    )
                )
                self._listener.on_recognition_result(b)
                if last_segment:
                    self._logger.info(
                        "[TIMER] RecogTime: {} s".format(time() - self._time_wait_recog)
                    )
                    with self._cv_wait_recog:
                        self._status = h["Result-Status"]
                        self._cv_wait_recog.notify_all()


if __name__ == "__main__":
    cv = Condition()
    listener = RecognitionListener()
    listener.on_recognition_result = lambda x: print(x)
    url = "ws://localhost:8025/asr-server/asr"
    ws = ASRClient(url, Condition(), listener, logger=Logger(stderr, debug=True))
    ws.connect()
    ws.disconnect()
