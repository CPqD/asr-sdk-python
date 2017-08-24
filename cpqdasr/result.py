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

Result classes implementation, which are pure objects as specified by the
unified API from CPqD SDKs.
"""


class PartialRecognitionResult:
    def __init__(self, speechSegmentIndex, text):
        assert(type(speechSegmentIndex) is int)
        assert(type(text) is str)
        self.speechSegmentIndex = speechSegmentIndex
        self.text = text


class RecognitionResult:
    def __init__(self, resultCode,
                 speechSegmentIndex,
                 lastSpeechSegment,
                 sentenceStartTimeMilliseconds,
                 sentenceEndTimeMilliseconds,
                 alternatives):
        assert(type(resultCode) is str)
        assert(type(speechSegmentIndex) is int)
        assert(type(lastSpeechSegment) is bool)
        assert(type(sentenceStartTimeMilliseconds) is int)
        assert(type(sentenceEndTimeMilliseconds) is int)
        assert(type(alternatives) is list)
        self.resultCode = resultCode
        self.speechSegmentIndex = speechSegmentIndex
        self.lastSpeechSegment = lastSpeechSegment
        self.sentenceStartTimeMilliseconds = sentenceStartTimeMilliseconds
        self.sentenceEndTimeMilliseconds = sentenceEndTimeMilliseconds
        self.alternatives = alternatives
