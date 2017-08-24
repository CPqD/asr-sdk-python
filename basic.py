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

Basic example with an audio file input.
"""
from cpqdasr import SpeechRecognizer
from cpqdasr.audio_source import FileAudioSource
from sys import argv


def usage():
    print("Usage: {} <ws_url> <lang_uri> <wav_path> [ <user> <password> ]"
          .format(argv[0]))
    print("   eg: {} ws://127.0.0.1:8025/asr-server/asr "
          "builtin:grammar/samples/phone /path/to/audio.wav".format(argv[0]))
    print("  eg2: {} wss://contact/cpqd/and/request/a/key/ "
          "builtin:slm/general /path/to/audio.wav "
          "myusername mypassword".format(argv[0]))
    exit()


if __name__ == "__main__":
    ostream = open('log.txt', 'a')
    argc = len(argv)
    if argc != 4 and argc != 6:
        usage()

    url = argv[1]
    lm = argv[2]
    apath = argv[3]
    credentials = ("", "")
    if(argc == 6):
        credentials = (argv[4], argv[5])

    asr = SpeechRecognizer(url, credentials=credentials,
                           logStream=ostream,
                           logLevel="info")
    asr.recognize(FileAudioSource(apath), [lm])
    res = asr.waitRecognitionResult()
    if res:
        print(res[0].alternatives)
    else:
        print("Empty result! Check log.txt for more info.")
    asr.close()
