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
from cpqdasr import SpeechRecognizer, LanguageModelList
from cpqdasr import RecognitionException
from cpqdasr import MicAudioSource
from cpqdasr import RecognitionListener

from sys import argv
from sys import stdout, stderr
import os
import getopt



class PrinterListener(RecognitionListener):
    def __init__(self, max_char=80, result_parse = False):
        self.max_char = max_char
        self.result_parse = result_parse
        self.last_final = 0
        self.print_str = ""
        self.result_str = ""

    #    def on_partial_recognition(self, partial):
    #        pass
    #        if self.print_str:
    #            self.print_str += ' '
    #        self.print_str += partial.text
    #        self.print_str = self.print_str[:self.max_char]
    #        print(self.print_str, end='\r')
    #        stdout.flush()

    def on_recognition_result(self, result):
        self.result_str = "{}".format(result)
        self.print_str = self.print_str[: self.last_final]
        if "alternatives" in result and result["alternatives"]:
            alt = result["alternatives"][0]
            if "text" in alt:
                if self.print_str:
                    self.print_str += " "
                self.print_str += alt["text"]
                if len(self.print_str) > self.max_char:
                    i = self.max_char
                    while self.print_str[i] != " ":
                        i -= 1
                    clear_spaces = " " * (self.max_char - i)
                    if not self.result_parse:
                        print(self.print_str[:i] + clear_spaces, end="\n")
                    self.print_str = self.print_str[i:]
                    if self.print_str[0] == " ":
                        self.print_str = self.print_str[1:]
                if not self.result_parse:
                    print(self.print_str, end="\r")
                self.last_final = len(self.print_str)
                stdout.flush()

def usage():
    print(
        "Usage: {} -j -w <ws_url> -l <lang_uri> [ -u <user> -p <password> ]\n"
        "                -j: parse json result".format(argv[0])
    )
    print(
        "   eg: {} -w ws://127.0.0.1:8025/asr-server/asr "
        "-l builtin:grammar/samples/phone".format(argv[0])
    )
    print(
        "  eg2: {} -w wss://contact/cpqd/and/request/a/key/ "
        "-l builtin:slm/general myusername mypassword".format(argv[0])
    )
    exit()


if __name__ == "__main__":
    user = ""
    password = ""
    pars = {}
    result_parse = False
    try:
        opts, args = getopt.getopt(argv[1:], "hjw:l:u:p:v:")
    except getopt.GetoptError:
        usage()

    for opt, arg in opts:
        if opt == "-w":
            url = arg
            #print("URL= {}".format(url))
        elif opt == "-l":
            lang_uri_or_path = arg
            #print("Language= {}".format(lang_uri_or_path))
        elif opt == "-u":
            user = arg
            print("User {}".format(user))
        elif opt == "-v":
            v = arg.split("=")
            pars[v[0]] = v[1]
        elif opt == "-p":
            password = arg
            print("User {}".format(password))
        elif opt == "-j":
            result_parse = True
        elif opt == "-h":
            usage(0)

    if os.path.isfile(lang_uri_or_path):
        lm = LanguageModelList(
            LanguageModelList.grammar_from_path(os.path.basename(lang_uri_or_path), lang_uri_or_path)
        )
    else:
        lm = LanguageModelList(LanguageModelList.from_uri(lang_uri_or_path))
    credentials = (user, password)

    listener=PrinterListener(result_parse = result_parse)
    asr = SpeechRecognizer(
        url,
        credentials=credentials,
        listener=listener,
    )

    with MicAudioSource() as mic:
        try:
            asr.recognize(mic, lm, wav=False, config=pars)
            result = asr.wait_recognition_result()
            if result:
                if result[0].result_code == "RECOGNIZED":
                    if (result_parse):
                        out = listener.result_str.replace("'", "\"")
                        out = out.replace("True", "\"True\"")
                        out = out.replace("False", "\"False\"")
                        cmd = "echo '{}' | jq --raw-output".format(out)
                        os.system(cmd)
                    else:
                        print(result[0].alternatives[0]["text"])
                else:
                    print(result[0].result_code)
        except KeyboardInterrupt:
            print("Caught interrupt. Closing ASR instance...", file=stderr)
            try:
                asr.cancel_recognition()
            except RecognitionException:
                pass  # Ignores exceptions on canceling
    asr.close()
