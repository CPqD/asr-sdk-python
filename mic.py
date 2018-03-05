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

Example with microphone input
"""
from cpqdasr.speech_recognizer import SpeechRecognizer, LanguageModelList
from cpqdasr.speech_recognizer import RecognitionException
from cpqdasr.audio_source import MicAudioSource
from cpqdasr.listener import RecognitionListener

from sys import argv
from sys import stdout, stderr
import time
import os

class PrinterListener(RecognitionListener):

    def __init__(self, max_char=80):
        self.max_char = 80
        self.last_final = 0
        self.print_str = ""

#    def onPartialRecognition(self, partial):
#        pass
#        if self.print_str:
#            self.print_str += ' '
#        self.print_str += partial.text
#        self.print_str = self.print_str[:self.max_char]
#        print(self.print_str, end='\r')
#        stdout.flush()

    def onRecognitionResult(self, result):
        self.print_str = self.print_str[:self.last_final]
        if 'alternatives' in result and result['alternatives']:
            alt = result['alternatives'][0]
            if 'text' in alt:
                if self.print_str:
                    self.print_str += ' '
                self.print_str += alt['text']
                if len(self.print_str) > self.max_char:
                    i = self.max_char
                    while(self.print_str[i] != ' '):
                        i -= 1
                    clear_spaces = " " * (self.max_char - i)
                    print(self.print_str[:i] + clear_spaces, end='\n')
                    self.print_str = self.print_str[i:]
                    if self.print_str[0] == ' ':
                        self.print_str = self.print_str[1:]
                print(self.print_str, end='\r')
                self.last_final = len(self.print_str)
                stdout.flush()


def usage():
    print("Usage: {} <ws_url> <lang_uri> <wav_path> [ <user> <password> ]"
          .format(argv[0]))
    print("   eg: {} ws://127.0.0.1:8025/asr-server/asr "
          "builtin:grammar/samples/phone".format(argv[0]))
    print("  eg2: {} wss://contact/cpqd/and/request/a/key/ "
          "builtin:slm/general myusername mypassword".format(argv[0]))
    exit()


if __name__ == "__main__":
    ostream = open('log.txt', 'a')
    argc = len(argv)
    if argc != 3 and argc != 5:
        usage()

    url = argv[1]
    if os.path.isfile(argv[2]):
        lm = LanguageModelList(
                LanguageModelList.grammarFromPath(
                        os.path.basename(argv[2]), argv[2]
                )
             )
    else:
        lm = LanguageModelList(
                 LanguageModelList.fromURI(argv[2])
             )
    credentials = ("", "")
    if(argc == 5):
        credentials = (argv[3], argv[4])

    asr = SpeechRecognizer(url, credentials=credentials,
                           logStream=ostream,
                           listener=PrinterListener(),
                           logLevel="warning")

    with MicAudioSource() as mic:
        try:
            asr.recognize(mic, lm)
            result = asr.waitRecognitionResult()
            if result:
                if result[0].resultCode == "RECOGNIZED":
                    print(result[0].alternatives[0]['text'])
                else:
                    print(result[0].resultCode)
        except KeyboardInterrupt:
            print("Caught interrupt. Closing ASR instance...", file=stderr)
            try:
                asr.cancelRecognition()
            except RecognitionException:
                pass  # Ignores exceptions on canceling
    asr.close()
