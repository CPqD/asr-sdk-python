#!/usr/bin/env python3
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
@author: valterf

Example with the buffer interface. Uses the same parameters as basic.py
"""
from cpqdasr import SpeechRecognizer, LanguageModelList
from cpqdasr import BufferAudioSource
from sys import argv
import soundfile as sf
import os


def usage():
    print(
        "Usage: {} <ws_url> <lang_uri_or_path> <wav_path> [ <user> <password> ]".format(
            argv[0]
        )
    )
    print(
        "   eg: {} ws://127.0.0.1:8025/asr-server/asr "
        "builtin:grammar/samples/phone /path/to/audio.wav".format(argv[0])
    )
    print(
        "  eg2: {} wss://contact/cpqd/and/request/a/key/ "
        "builtin:slm/general /path/to/audio.wav "
        "myusername mypassword".format(argv[0])
    )
    print(
        "  eg3: {} ws://127.0.0.1:8025/asr-server/asr "
        "/path/to/my/grammar /path/to/audio.wav".format(argv[0])
    )
    exit()


if __name__ == "__main__":
    argc = len(argv)
    if argc != 4 and argc != 6:
        usage()

    url = argv[1]
    if os.path.isfile(argv[2]):
        lm = LanguageModelList(LanguageModelList.grammar_from_path("asdasdas", argv[2]))
    else:
        lm = LanguageModelList(LanguageModelList.from_uri(argv[2]))
    apath = argv[3]
    credentials = ("", "")
    if argc == 6:
        credentials = (argv[4], argv[5])

    asr = SpeechRecognizer(
        url,
        credentials=credentials,
        max_wait_seconds=600,
    )

    source = BufferAudioSource()
    asr.recognize(source, lm)
    audio, rate = sf.read(apath)

    # From float32 to int16, and then to raw bytes
    source.write((audio * 2 ** 15).astype("int16").tobytes())
    source.finish()
    res = asr.wait_recognition_result()

    if res:
        for k in res:
            print(k.alternatives)
    else:
        print("Empty result!")

    asr.close()
