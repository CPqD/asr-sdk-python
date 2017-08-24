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
log_level = "error"  # "error", "warning", "info" or "debug"
slm = 'builtin:slm/general-small'

# Resource config
res = "tests/unit/res/audio/"
phone_wav = res + "phone-1937050211-8k.wav"
phone_raw = res + "phone-1937050211-8k.raw"
previsao_tempo_wav = res + "previsao-tempo-8k.wav"
previsao_tempo_raw = res + "previsao-tempo-8k.raw"
silence_wav = res + "silence-8k.wav"
