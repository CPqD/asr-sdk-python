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
from cpqdasr import LanguageModelList
from .config import url, credentials
from .config import slm, pizza_grammar_path, pizza_wav, gibberish_wav
from .common import stress_recognition


def expect_success_assertion(results):
    success = False
    for i, result in enumerate(results):
        if result.alternatives:
            alt = result.alternatives[0]
        else:
            continue
        if not len(alt["text"]) > 0:
            continue
        if not int(alt["score"]) > 80:
            continue
        success = True
    return success, "Expected at least one successful result"


def expect_failure_assertion(results):
    for i, result in enumerate(results):
        if result.alternatives:
            alt = result.alternatives[0]
        else:
            continue
        alt = result.alternatives[0]
        if int(alt["score"]) > 75:
            return (
                False,
                (
                    "Expected failure but result {} had score of {}".format(
                        i, int(alt["score"])
                    )
                ),
            )
    return True, ""


# =============================================================================
# Test cases
# =============================================================================
def test_grammar_match():
    lm = LanguageModelList(
        LanguageModelList.grammarFromPath("pizza", pizza_grammar_path)
    )
    stress_recognition(
        url,
        {"credentials": credentials, "max_wait_seconds": 600},
        pizza_wav,
        lm,
        (0, 25),
        10,
        10,
        assertion=expect_success_assertion,
    )


def test_grammar_nomatch():
    lm = LanguageModelList(
        LanguageModelList.grammarFromPath("pizza", pizza_grammar_path)
    )
    stress_recognition(
        url,
        {"credentials": credentials, "max_wait_seconds": 600},
        gibberish_wav,
        lm,
        (0, 25),
        10,
        10,
        assertion=expect_failure_assertion,
    )


def test_slm_match():
    lm = LanguageModelList(slm)
    stress_recognition(
        url,
        {"credentials": credentials, "max_wait_seconds": 600},
        pizza_wav,
        lm,
        (0, 25),
        10,
        10,
        assertion=expect_success_assertion,
    )


def test_slm_nomatch():
    lm = LanguageModelList(slm)
    stress_recognition(
        url,
        {
            "credentials": credentials,
            "max_wait_seconds": 600,
        },
        gibberish_wav,
        lm,
        (0, 25),
        10,
        10,
        assertion=expect_failure_assertion,
    )
