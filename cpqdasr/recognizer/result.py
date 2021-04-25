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
    def __init__(self, speech_segment_index, text):
        assert type(speech_segment_index) is int
        assert type(text) is str
        self.speechSegmentIndex = speech_segment_index
        self.text = text


class AgeResult:
    def __init__(
            self,
            event,
            age,
            p,
            age_50,
            age_80,
            age_99
    ):
        self.event = event
        self.age = age
        self.p = p
        self.age_50 = age_50
        self.age_80 = age_80
        self.age_99 = age_99


class GenderResponse:
    def __init__(
            self,
            event,
            p,
            gender
    ):
        self.event = event
        self.p = p
        self.gender = gender


class EmotionResponse:
    def __init__(
            self,
            p,
            event,
            emotion
    ):
        self.p = p
        self.event = event
        self.emotion = emotion


class RecognitionResult:
    def __init__(
            self,
            result_code,
            speech_segment_index,
            last_speech_segment,
            sentence_start_time_milliseconds,
            sentence_end_time_milliseconds,
            alternatives,
            age_scores=None,
            gender_scores=None,
            emotion_scores=None
    ):
        assert type(result_code) is str
        assert type(speech_segment_index) is int
        assert type(last_speech_segment) is bool
        assert type(sentence_start_time_milliseconds) is int
        assert type(sentence_end_time_milliseconds) is int
        assert type(alternatives) is list
        self.result_code = result_code
        self.speech_segment_index = speech_segment_index
        self.last_speech_segment = last_speech_segment
        self.sentence_start_time_milliseconds = sentence_start_time_milliseconds
        self.sentence_end_time_milliseconds = sentence_end_time_milliseconds
        self.alternatives = alternatives
        self.age_scores = age_scores
        self.gender_scores = gender_scores
        self.emotion_scores = emotion_scores
