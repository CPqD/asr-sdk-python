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

Tests with audio sources
"""

from cpqdasr import (
    SpeechRecognizer,
    LanguageModelList,
    FileAudioSource,
    BufferAudioSource,
)
from .config import url, credentials, slm, phone_wav

import soundfile as sf


asr_kwargs = {"credentials": credentials}


# =============================================================================
# Test cases
# =============================================================================
def test_equivalence_file_buffer():

    # File
    asr = SpeechRecognizer(url, **asr_kwargs)
    asr.recognize(FileAudioSource(phone_wav), LanguageModelList(slm))
    result_file = asr.wait_recognition_result()[0].alternatives[0]["text"]
    asr.close()

    # Buffer
    asr = SpeechRecognizer(url, **asr_kwargs)
    source = BufferAudioSource()
    asr.recognize(source, LanguageModelList(slm), wav=False)
    sig, rate = sf.read(phone_wav)
    source.write((sig * 2 ** 15).astype("int16").tobytes())
    source.finish()
    result_buffer = asr.wait_recognition_result()[0].alternatives[0]["text"]
    asr.close()

    assert result_file == result_buffer


def test_empty_buffer():
    # Buffer
    asr = SpeechRecognizer(url, **asr_kwargs)
    source = BufferAudioSource()
    asr.recognize(source, LanguageModelList(slm), wav=False)
    source.finish()
    res = asr.wait_recognition_result()
    assert len(res[0].alternatives) == 0
    asr.close()
