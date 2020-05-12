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

# Recognition config
url = "ws://localhost:8025/asr-server/asr"
credentials = ("", "")
log_level = "warning"  # "error", "warning", "info" or "debug"
log_path = "/tmp/asr-sdk-python-test.log"
slm = "builtin:slm/general"
phone_grammar_uri = "builtin:grammar/phone"

# Resource config
res = "tests/unit/res/"
phone_wav = res + "audio/phone-1937050211-8k.wav"
phone_raw = res + "audio/phone-1937050211-8k.raw"
previsao_tempo_wav = res + "audio/previsao-tempo-8k.wav"
previsao_tempo_raw = res + "audio/previsao-tempo-8k.raw"
silence_wav = res + "audio/silence-8k.wav"
yes_wav = res + "audio/yes-8k.wav"
yes_grammar_path = res + "grammar/yes_no.gram"
pizza_wav = res + "audio/pizza-8k.wav"
pizza_multi_wav = res + "audio/pizza-multi-8k.wav"
pizza_grammar_path = res + "grammar/pizza.gram"
gibberish_wav = res + "audio/gibberish-8k.wav"
