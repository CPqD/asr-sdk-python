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
Created on Wed Jan  3 10:07:49 2018

@author: Akira Miasato

Stability tests, which take a while to run.
"""
from cpqdasr.speech_recognizer import SpeechRecognizer, LanguageModelList
from cpqdasr.audio_source import FileAudioSource
from multiprocessing import Process
from time import time
from .config import url, credentials, slm, pizza_wav, gibberish_wav
from .config import pizza_grammar_path, log_level, log_path
from sys import stdout


asr_kwargs = {'credentials': credentials,
              'logLevel': 'info',
              'maxWaitSeconds': 600}


def recognize_worker(wav_path, lm_list, asr_kwargs,
                     recognitions, executions, expect_success):
    for e in range(executions):
        beg = time()
        asr = SpeechRecognizer(url, **asr_kwargs)
        for r in range(recognitions):
            asr.recognize(FileAudioSource(wav_path), lm_list)
            success = False
            for result in asr.waitRecognitionResult():
                if result.alternatives:
                    alt = result.alternatives[0]
                else:
                    continue
                if expect_success:
                    assert len(alt['text']) > 0
                    assert int(alt['score']) > 80,\
                        "Score was {}".format(int(alt['score']))
                    success = True
                else:
                    alt = result.alternatives[0]
                    assert int(alt['score']) < 75,\
                        "Score was {}".format(int(alt['score']))
            if not success and expect_success:
                assert False, "Expected at least one successful result"
        asr.close()
        asr._logger.info("[TIMER] TotalTime: {} s"
                         .format(time() - beg))


def stress_recognition(wav_path, lm_list,
                       session_range=(1, 1),
                       recognitions=1,
                       executions=1,
                       expect_success=True,
                       log_stream=stdout):
    asr_kwargs_c = asr_kwargs
    asr_kwargs_c['logStream'] = log_stream
    for i in range(*session_range):
        ps = []
        for s in range(i+1):
            asr_kwargs_c['alias'] = 'Session {}/{} '.format(s+1, i+1)
            ps.append(Process(target=recognize_worker,
                              args=(wav_path,
                                    lm_list,
                                    asr_kwargs_c,
                                    recognitions,
                                    executions,
                                    expect_success)))
            ps[-1].start()
        for p in ps:
            p.join()
            assert p.exitcode == 0


# =============================================================================
# Test cases
# =============================================================================
def testGrammarMatch():
    lm = LanguageModelList(
             LanguageModelList.grammarFromPath('pizza', pizza_grammar_path)
         )
    with open('testGrammarMatch.log', 'w') as f:
        stress_recognition(pizza_wav, lm, (0, 25), 1, 50,
                           expect_success=True,
                           log_stream=f)


def testGrammarNoMatch():
    lm = LanguageModelList(
             LanguageModelList.grammarFromPath('pizza', pizza_grammar_path)
         )
    with open('testGrammarNoMatch.log', 'w') as f:
        stress_recognition(gibberish_wav, lm, (0, 25), 1, 50,
                           expect_success=False,
                           log_stream=f)


def testSlmMatch():
    lm = LanguageModelList('builtin:slm/general')
    with open('testSlmMatch.log', 'w') as f:
        stress_recognition(pizza_wav, lm, (0, 25), 1, 50,
                           expect_success=True,
                           log_stream=f)


def testSlmNoMatch():
    lm = LanguageModelList('builtin:slm/general')
    with open('testSlmNoMatch.log', 'w') as f:
        stress_recognition(gibberish_wav, lm, (0, 25), 1, 50,
                           expect_success=False,
                           log_stream=f)
