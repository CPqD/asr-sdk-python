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

ASR Server WebSocket API connection handler.
"""
import json
from sys import stderr
from threading import Condition
from ws4py.client.threadedclient import WebSocketClient

from .result import PartialRecognitionResult, RecognitionResult
from .listener import RecognitionListener
from .logger import Logger
from .config import VERSION


def create_session_msg(user_agent=None):
    msg = "{} CREATE_SESSION\n".format(VERSION)
    if user_agent is not None:
        msg += "User-Agent: {}\n"
        msg = msg.format(user_agent)
    msg = msg.encode()
    return msg


def set_parameters_msg(parameters):
    msg = "{} SET_PARAMETERS\n".format(VERSION)
    for key in parameters:
        msg += "{}: {}\n".format(key, parameters[key])
    msg = msg.encode()
    return msg


def define_grammar_msg(grammar_id, grammar_body):
    msg = "{} DEFINE_GRAMMAR\n".format(VERSION)
    msg += "Content-Type: application/srgs\n"
    msg += "Content-ID: {}\n".format(grammar_id)
    msg += "Content-Length: {}\n\n"
    # TODO: Check why we need to sum 2
    payload = grammar_body.encode()
    msg = msg.format(len(payload)).encode()
    msg += grammar_body
    return msg


def start_recog_msg(uri_list):
    msg = "{} START_RECOGNITION\n".format(VERSION)
    msg += "Accept: application/json\n"
    msg += "Content-Type: text/uri-list\n"
    msg += "Content-Length: {}\n\n"
    langs = '\n'.join(uri_list)
    msg = msg.format(len(langs)).encode()
    msg += langs.encode()
    return msg


def send_audio_msg(payload, last=False):
    """
    Payload should be a valid bytestring representing a raw waveform. Every
    2 bytes (16bit) should represent a little-endian sample.
    """
    if last:
        last = "true"
    else:
        last = "false"
    msg = "{} SEND_AUDIO\n".format(VERSION)
    msg += "LastPacket: {}\n".format(last)

    # Brackets are a placeholder for payload size
    msg += "Content-Length: {}\n"
    msg += "Content-Type: application/octet-stream\n\n"

    # Adding payload size and converting to binary
    msg = msg.format(len(payload)).encode()
    msg += payload  # Adding payload at the end of the message
    return msg


def release_session_msg():
    return "{} RELEASE_SESSION".format(VERSION).encode()


def cancel_recog_msg():
    return "{} CANCEL_RECOGNITION".format(VERSION).encode()


def parse_response(msg):
    """
    Parses CPqD ASR messages and returns a string corresponding to the
    response type and two dicts, the first one corresponding to the
    header, and the second one to the JSON body.
    """
    msg = msg.data
    msg = msg.replace(b'\r', b'')
    msg = msg.split(b'\n\n')
    header = msg[0].decode().split('\n')
    h = {}
    r = header[0].split()[-1]
    for l in header[1:]:
        split = [x.strip() for x in l.split(':')]
        key = split[0]
        val = ':'.join(split[1:])
        h[key] = val

    body = b'\n\n'.join(msg[1:])
    if body:
        b = json.loads(body.decode())
    else:
        b = {}
    return r, h, b


class ASRClient(WebSocketClient):
    def __init__(self, url,
                 cv_define_grammar, cv_start_recog, cv_send_audio,
                 cv_wait_recog, cv_wait_cancel,
                 listener=RecognitionListener(),
                 user_agent=None,
                 config=None,
                 logger=Logger(stderr),
                 debug=False,
                 protocols=None,
                 extensions=None,
                 heartbeat_freq=None,
                 ssl_options=None,
                 headers=None,):
        super(ASRClient, self).__init__(url,
                                        protocols,
                                        extensions,
                                        heartbeat_freq,
                                        ssl_options,
                                        headers)
        assert isinstance(cv_define_grammar, Condition)
        assert isinstance(cv_start_recog, Condition)
        assert isinstance(cv_send_audio, Condition)
        assert isinstance(cv_wait_recog, Condition)
        assert isinstance(cv_wait_cancel, Condition)
        self._user_agent = user_agent
        self._listener = listener
        self._config = config
        self._logger = logger
        self._status = "DISCONNECTED"
        self._cv_define_grammar = cv_define_grammar
        self._cv_start_recog = cv_start_recog
        self._cv_send_audio = cv_send_audio
        self._cv_wait_recog = cv_wait_recog
        self._cv_wait_cancel = cv_wait_cancel
        self._cv_opened = Condition()
        self.recognition_list = []
        self.daemon = False

    def __del__(self):
        self.close()

    def isConnected(self):
        return(self._status != "DISCONNECTED" and
               self._status != "WAITING_CONFIG")

    def _finish_connect(self):
        with self._cv_start_recog:
            self._status = "IDLE"
            self._cv_start_recog.notify_all()

    def _abort(self):
        self._status = "ABORTED"
        self._logger.debug("Aborting")
        with self._cv_define_grammar:
            self._logger.debug("Aborting define grammar")
            self._cv_define_grammar.notify_all()
        with self._cv_start_recog:
            self._logger.debug("Aborting start recog")
            self._cv_start_recog.notify_all()
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

    def onWaitRecognitionFinished(self):
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
        if call not in ["RESPONSE",
                        "START_OF_SPEECH",
                        "END_OF_SPEECH",
                        "RECOGNITION_RESULT"]:
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
                    self._logger.debug("Grammar defined")
                    with self._cv_define_grammar:
                        self._cv_define_grammar.notify_all()
                else:
                    self._logger.warning("Error on defining grammar: "
                                         "{}".format(msg.data))
                    self._abort()
                return
            if h["Method"] == "START_RECOGNITION":
                if h["Result"] == "SUCCESS":
                    self._logger.debug("Starting recognition")
                    self._status = "LISTENING"
                    with self._cv_send_audio:
                        self._cv_send_audio.notify_all()
                else:
                    self._logger.warning("Error on start recognition: "
                                         "{}".format(msg.data))
                    self._abort()
                return

        if "Session-Status" in h:
            session_status = h["Session-Status"]
        else:
            session_status = h["Result"]

        # Treats the expected message when first "CREATE_SESSION" is sent
        if self._status == "DISCONNECTED":
            if call != "RESPONSE":
                self._logger.warning("Invalid received message on open "
                                     "connection: expected RESPONSE, got "
                                     "{}".format(session_status))
            elif session_status != "IDLE":
                self._logger.warning("Invalid status on open connection: "
                                     "expected IDLE, got "
                                     "{}".format(session_status))
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
                self._logger.warning("Non-fatal error in API call: Code "
                                     "{}".format(h["Error-Code"]))
                self._abort()

            elif h['Method'] == "CANCEL_RECOGNITION":
                with self._cv_wait_cancel:
                    self._cv_wait_cancel.notify_all()
                    self._status = "IDLE"

            # Default response case which is ignored
            else:
                self._logger.info("Ignored {} response".format(h['Method']))
            return

        if call == "RECOGNITION_RESULT":
            if h["Result-Status"] == "PROCESSING":
                self._listener.onPartialRecognition(
                    PartialRecognitionResult(
                        0,
                        b['alternatives'][0]['text'].strip()
                    )
                )
            else:
                if 'alternatives' in b:
                    result = b['alternatives']
                else:
                    result = []
                if 'last_segment' in b:
                    last_segment = b['last_segment']
                else:
                    last_segment = True
                self.recognition_list.append(
                    RecognitionResult(
                        resultCode=h["Result-Status"],
                        speechSegmentIndex=0,
                        lastSpeechSegment=last_segment,
                        sentenceStartTimeMilliseconds=0,
                        sentenceEndTimeMilliseconds=0,
                        alternatives=result
                    )
                )
                self._listener.onRecognitionResult(b)
                if last_segment:
                    with self._cv_wait_recog:
                        self._status = "RECOGNIZED"
                        self._cv_wait_recog.notify_all()


if __name__ == "__main__":
    cv = Condition()
    listener = RecognitionListener()
    listener.onRecognitionResult = lambda x: print(x)
    url = "ws://localhost:8025/asr-server/asr"
    ws = ASRClient(url, Condition(), listener,
                   logger=Logger(stderr, debug=True))
    ws.connect()
    ws.disconnect()
