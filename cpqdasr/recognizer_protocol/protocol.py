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

ASR Server WebSocket API message builders/parsers
"""
import json


VERSION = "ASR 2.4"


def create_session_msg(user_agent=None, channel_identifier=None):
    msg = "{} CREATE_SESSION\n".format(VERSION)
    if user_agent is not None:
        msg += "User-Agent: {}\n"
        msg = msg.format(user_agent)
    if channel_identifier is not None:
        msg += "Channel-Identifier: {}\n"
        msg = msg.format(channel_identifier)
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
    payload = grammar_body.encode()
    msg = msg.format(len(payload)).encode()
    msg += payload
    return msg


def start_recog_msg(uri_list, config):
    msg = "{} START_RECOGNITION\n".format(VERSION)
    msg += "Accept: application/json\n"
    if config:
        for k, v in config.items():
            msg += "{}: {}\n".format(k, v)
    msg += "Content-Type: text/uri-list\n"
    msg += "Content-Length: {}\n\n"
    langs = "\n".join(uri_list)
    msg = msg.format(len(langs)).encode()
    msg += langs.encode()
    return msg


def start_input_timers_msg():
    msg = "{} START_INPUT_TIMERS\n".format(VERSION)
    msg = msg.encode()
    return msg


def send_audio_msg(payload, last=False, audio_wav=True):
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
    if audio_wav:
        msg += "Content-Type: audio/wav\n\n"
    else:
        msg += "Content-Type: audio/raw\n\n"

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
    msg = msg.replace(b"\r", b"")
    msg = msg.split(b"\n\n")
    header = msg[0].decode().split("\n")
    h = {}
    r = header[0].split()[-1]
    for l in header[1:]:
        split = [x.strip() for x in l.split(":")]
        key = split[0]
        val = ":".join(split[1:])
        h[key] = val

    body = b"\n\n".join(msg[1:])
    if body:
        b = json.loads(body.decode())
    else:
        b = {}
    return r, h, b
