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

Tests with grammars
"""
from cpqdasr.speech_recognizer import RecognitionException
from cpqdasr.speech_recognizer import SpeechRecognizer, LanguageModelList
from cpqdasr.audio_source import FileAudioSource
from .config import url, credentials, phone_wav, silence_wav, yes_wav
from .config import log_level, log_path, phone_grammar_uri, yes_grammar_path
import soundfile as sf
import time


# =============================================================================
# Test package definition
# =============================================================================
asr_kwargs = {'credentials': credentials,
              'logLevel': log_level,
              'logStream': open(log_path, 'a')}


def DelayedFileAudioSource(path, blocksize=512):
    """
    Simulates real-time decoding with a time.sleep corresponding to the
    duration of the audio packet sent at each yield (assumes 8kHz)

    :path: Path to the audio input (any format supported by soundfile package)
    :blocksize: Size of the blocks of audio which will be sent (in samples)
    """
    for block in sf.blocks(path, blocksize):
        # Soundfile converts to 64-bit float ndarray. We convert back to bytes
        bytestr = (block * 2**15).astype('<i2').tobytes()
        time.sleep(blocksize / 8000. / 2.)  # 8kHz
        yield bytestr


# =============================================================================
# Test cases
# =============================================================================
def testBasicGrammar():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(FileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    result = asr.waitRecognitionResult()
    asr.close()
    alt = None
    for res in result:
        if len(res.alternatives) > 0:
            alt = res.alternatives[0]
            break
    assert(alt is not None)
    assert(len(alt['text']) > 0)
    assert(len(alt['interpretations']) > 0)
    assert(int(alt['score']) > 90)


def testInlineGrammar():
    with open(yes_grammar_path) as f:
        body = f.read()
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(FileAudioSource(yes_wav),
                  LanguageModelList(("yes_no", body)))
    result = asr.waitRecognitionResult()
    asr.close()
    alt = None
    for res in result:
        if len(res.alternatives) > 0:
            alt = res.alternatives[0]
            break
    assert(alt is not None)
    assert(len(alt['text']) > 0)
    assert(len(alt['interpretations']) > 0)
    assert(int(alt['score']) > 90)


def testNoInputTimeout():
    config = {
              'decoder.startInputTimers': 'true',
              'noInputTimeout.value': '100',
              'noInputTimeout.enabled': 'true',
             }
    asr = SpeechRecognizer(url, recogConfig=config, **asr_kwargs)
    asr.recognize(DelayedFileAudioSource(silence_wav),
                  LanguageModelList(phone_grammar_uri))
    result = asr.waitRecognitionResult()
    asr.close()
    assert(result[0].resultCode in ("NO_INPUT_TIMEOUT", "NO_MATCH"))


def testRecognizeBufferAudioSource():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(DelayedFileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    result = asr.waitRecognitionResult()[0].alternatives[0]
    asr.close()
    assert(len(result['text']) > 0)
    assert(len(result['interpretations']) > 0)
    assert(int(result['score']) > 90)


# Won't be implemented, as python generators are convenient enough to avoid
# usage of internal buffers for the recognizer.
def testRecognizeBufferBlockRead():
    pass


def testMaxWaitSecondsThreadResponse():
    asr = SpeechRecognizer(url, maxWaitSeconds=2, **asr_kwargs)
    asr.recognize(DelayedFileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    try:
        asr.waitRecognitionResult()
        asr.close()
    except RecognitionException as e:
        asr.close()
        assert(e.code == "FAILURE")
    else:
        asr.close()
        assert(False)


def testCloseOnRecognize():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(DelayedFileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    time.sleep(2)
    asr.close()
    result = asr.waitRecognitionResult()
    assert(len(result) == 0)


def testCloseWithoutRecognize():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.close()


def testCancelOnRecognize():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(DelayedFileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    time.sleep(2)
    asr.cancelRecognition()
    result = asr.waitRecognitionResult()
    assert(len(result) == 0)


def testCancelWithoutRecognize():
    asr = SpeechRecognizer(url, **asr_kwargs)
    try:
        asr.cancelRecognition()
    except RecognitionException as e:
        assert(e.code == "FAILURE")
    else:
        assert(False)


def testWaitRecognitionResultNoRecognizer():
    asr = SpeechRecognizer(url, **asr_kwargs)
    result = asr.waitRecognitionResult()
    assert(len(result) == 0)


def testWaitRecognitionResultDuplicate():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(FileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    result = asr.waitRecognitionResult()[0].alternatives[0]
    result_empty = asr.waitRecognitionResult()
    asr.close()
    assert(len(result['text']) > 0)
    assert(len(result['interpretations']) > 0)
    assert(int(result['score']) > 90)
    assert(len(result_empty) == 0)


def testDuplicateRecognize():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(DelayedFileAudioSource(phone_wav),
                  LanguageModelList(phone_grammar_uri))
    time.sleep(2)
    try:
        asr.recognize(DelayedFileAudioSource(phone_wav),
                      LanguageModelList(phone_grammar_uri))
    except RecognitionException as e:
        assert(e.code == "FAILURE")
    else:
        assert(False)
    result = asr.waitRecognitionResult()[0].alternatives[0]
    asr.close()
    assert(len(result['text']) > 0)
    assert(len(result['interpretations']) > 0)
    assert(int(result['score']) > 90)


def testMultipleRecognize():
    asr = SpeechRecognizer(url, **asr_kwargs)
    results = []
    for i in range(3):
        asr.recognize(DelayedFileAudioSource(phone_wav),
                      LanguageModelList(phone_grammar_uri))
        results.append(asr.waitRecognitionResult()[0].alternatives[0])
    asr.close()
    for result in results:
        assert(len(result['text']) > 0)
        assert(len(result['interpretations']) > 0)
        assert(int(result['score']) > 90)
