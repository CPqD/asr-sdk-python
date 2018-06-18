# -*- coding: utf-8 -*-
#
#  Copyright 2018 CPqD. All rights reserved.
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
Created on Fri Jan  5 13:08:39 2018

@author: valterf

Tests with multiple segments in a single file.
These tests only work with specific server configurations.
"""
from cpqdasr import LanguageModelList
from .config import url, credentials, log_level
from .config import slm, pizza_grammar_path, pizza_multi_wav
from .common import stress_recognition


def multi_assertion(results):
    if len(results) <= 3:
        return False, ("Number of results is {} when expected are at least 3"
                       .format(len(results)))
    res = 0
    for i, result in enumerate(results):
        if result.result_code == "RECOGNIZED":
            alt = result.alternatives[0]
            print(alt, end='\n\n\n')
            res += 1
        else:
            continue
        alt = result.alternatives[0]
        if int(alt['score']) < 70:
            return False, ("Score from result {} is too low: its value is {}"
                           .format(i, int(alt['score'])))
    return res == 3, ("Number of valid results is {} when expected are 3"
                      .format(res))


# =============================================================================
# Test cases
# =============================================================================
def test_slm_multi():
    lm = LanguageModelList(slm)
    with open('test_slm_multi.log', 'w') as f:
        stress_recognition(url,
                           {'credentials': credentials,
                            'log_level': log_level,
                            'max_wait_seconds': 600,
                            'log_stream': f},
                           pizza_multi_wav, lm,
                           (0, 25), 10, 10,
                           assertion=multi_assertion)


def test_grammar_multi():
    lm = LanguageModelList(
             LanguageModelList.grammar_from_path('pizza', pizza_grammar_path)
         )
    with open('test_grammar_multi.log', 'w') as f:
        stress_recognition(url,
                           {'credentials': credentials,
                            'log_level': log_level,
                            'max_wait_seconds': 600,
                            'log_stream': f},
                           pizza_multi_wav, lm,
                           (0, 25), 10, 10,
                           assertion=multi_assertion)
