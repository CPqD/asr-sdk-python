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
from cpqdasr import SpeechRecognizer, LanguageModelList
from cpqdasr import FileAudioSource
from sys import argv, exit
import os
import getopt

config = {
    "Infer-age-enabled": False,
    "Infer-gender-enabled": False,
    "Infer-emotion-enabled": False,
    "Verify-Buffer-Utterance": False,
}


def usage(error=0):
    print(
        "Usage: {} -w <ws_url> -l <lang_uri_or_path> -a <wav_path> [ -u <user> -p <password> -v <parameter=value> ]".format(
            argv[0]
        )
    )
    print(
        "   eg: {} -w ws://127.0.0.1:8025/asr-server/asr "
        "-l builtin:grammar/samples/phone -a /path/to/audio.wav".format(argv[0])
    )
    print(
        "  eg2: {} -w ws://contact/cpqd/and/request/a/key/ "
        "-l builtin:slm/general -a /path/to/audio.wav "
        "-u myusername -p mypassword".format(argv[0])
    )
    print(
        "  eg3: {} -w ws://127.0.0.1:8025/asr-server/asr "
        "-l /path/to/my/grammar -a /path/to/audio.wav".format(argv[0])
    )
    print(
        "   eg4: {} -w ws://127.0.0.1:8000/ws/v1/recognize/ "
        "-l builtin:grammar/samples/phone -a /path/to/audio.wav "
        "-v Infer-age-enabled=true".format(argv[0])
    )
    exit(error)


if __name__ == "__main__":
    url = ""
    apath = ""
    lang_uri_or_path = ""
    user = ""
    password = ""
    pars = {}
    try:
        opts, args = getopt.getopt(argv[1:], "hw:l:a:u:p:v:")
    except getopt.GetoptError:
        usage(1)

    print("\nOptions:")
    for opt, arg in opts:
        if opt == "-w":
            url = arg
            print("URL= {}".format(url))
        elif opt == "-l":
            lang_uri_or_path = arg
            print("Language= {}".format(lang_uri_or_path))
        elif opt == "-a":
            apath = arg
            print("Audio path= {}".format(apath))
        elif opt == "-u":
            user = arg
            print("User {}".format(user))
        elif opt == "-v":
            v = arg.split("=")
            pars[v[0]] = v[1]
        elif opt == "-p":
            password = arg
            print("User {}".format(password))
        elif opt == "-h":
            usage(0)

    if len(url) == 0 or len(lang_uri_or_path) == 0 or len(apath) == 0:
        usage(2)

    if os.path.isfile(lang_uri_or_path):
        lm = LanguageModelList(
            LanguageModelList.grammar_from_path("asdasdas", lang_uri_or_path)
        )
    else:
        lm = LanguageModelList(LanguageModelList.from_uri(lang_uri_or_path))
    credentials = ("", "")
    if len(user) and len(password):
        credentials = (user, password)

    wav = True
    if apath[-4:] == ".raw":
        wav = False

    config["Media-Type"] = "audio/" + apath[-3:]

    if wav:
        print("Recognizing audio with header")

    if len(pars):
        config = pars
        print("Recognition parameters: {}".format(pars))

    asr = SpeechRecognizer(
        url,
        credentials=credentials,
        max_wait_seconds=600,
    )
    asr.recognize(FileAudioSource(apath), lm, wav=wav, config=config)
    res = asr.wait_recognition_result()

    if res:
        print("\nResults:")
        for k in res:
            print(k.alternatives)
            if k.age_scores.age != None:
                print(
                    "Event {}: {} years old".format(
                        k.age_scores.event, k.age_scores.age
                    )
                )
            if k.gender_scores.gender != None:
                print(
                    "Event {}: {}".format(k.gender_scores.event, k.gender_scores.gender)
                )
            if k.emotion_scores.emotion != None:
                print(
                    "Emotion {}: {}".format(
                        k.emotion_scores.event, k.emotion_scores.emotion
                    )
                )
    else:
        print("\nEmpty result!")
    asr.close()
