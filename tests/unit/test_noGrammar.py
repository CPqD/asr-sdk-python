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

Tests with statistical language models
"""
from cpqdasr.speech_recognizer import SpeechRecognizer, LanguageModelList
from cpqdasr.audio_source import FileAudioSource
from .config import url, credentials, slm, phone_wav, silence_wav
from .config import log_level, log_path


asr_kwargs = {'credentials': credentials,
              'logLevel': log_level,
              'logStream': open(log_path, 'w')}


# =============================================================================
# Test cases
# =============================================================================
def testBasicSLM():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(FileAudioSource(phone_wav),
                  LanguageModelList(slm))
    result = asr.waitRecognitionResult()[0]
    asr.close()
    assert len(result.alternatives[0]['text']) > 0
    assert int(result.alternatives[0]['score']) > 90


def testNoMatch():
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(FileAudioSource(silence_wav),
                  LanguageModelList(slm))
    result = asr.waitRecognitionResult()[0]
    asr.close()
    # NO_SPEECH occurs with enabled endpointer, and NO_MATCH with disabled
    assert result.resultCode in ("NO_SPEECH", "NO_MATCH")
