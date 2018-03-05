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

Audio generation examples.

Generators should always yield bytestrings. Our ASR interface only supports
linear PCM with little-endian signed 16bit samples. Their length may be
variable, as long as they are smaller than the predefined maximum payload size
from the configured websocket connection, and the length of each bytestring
is modulo 0 with the size of the sample (i.e. is even in length).
"""
import soundfile as sf
import pyaudio
import time


class MicAudioSource():
    """
    Simple microphone reader.

    chunk_size is in samples, so the size in bytes of the sent packet is
    sizeof(<sample_type>) * chunk_size. This value should be smaller than the
    predefined maximum payload from the configured websocket connection.

    :sample_rate: Sample rate for the captured audio
    :sample_type: Sample type provided by pyaudio
    :chunk_size: Size of the blocks of audio which will be sent (in samples)
    :yields: bytestrings of size <chunk_size> * sizeof(<sample_type>)

    Does not terminate. When used inside a SpeechRecognition instance, it
    is halted when the recognition instance is cancelled or closed.
    """
    def __init__(self, sample_rate=8000,
                 sample_type=pyaudio.paInt16,
                 chunk_size=4096):
        self._audio = pyaudio.PyAudio()
        self._sample_rate = sample_rate
        self._sample_type = sample_type
        self._chunk_size = chunk_size

    def __enter__(self):
        self._stream = self._audio.open(format=self._sample_type,
                                        channels=1,
                                        rate=self._sample_rate,
                                        input=True,
                                        frames_per_buffer=self._chunk_size)
        return self

    def __exit__(self, etype, value, traceback):
        self._stream.stop_stream()
        self._stream.close()

    def __iter__(self):
        return self

    def __next__(self):
        if not self._stream.is_active:
            raise StopIteration
        return self._stream.read(self._chunk_size)


def FileAudioSource(path, chunk_size=4096):
    """
    Simple audio file reader. Should be compatible with all files supported
    by 'soundfile' package.

    chunk_size is in samples, so the size in bytes of the sent packet is
    2*chunk_size, since we are sending 16-bit signed PCM samples. chunk_size*2
    should be smaller than the predefined maximum payload from the configured
    websocket connection.

    :path: Path to the audio input (any format supported by soundfile package)
    :chunk_size: Size of the blocks of audio which will be sent (in samples)

    :yields: bytestrings of size <chunk_size> * 2

    Terminates when the audio file provided has no more content
    """
    for block in sf.blocks(path, chunk_size):
        # Soundfile converts to 64-bit float ndarray. We convert back to bytes
        bytestr = (block * 2**15).astype('<i2').tobytes()
        yield bytestr


class BufferAudioSource():
    """
    Very simple buffer source.

    This generator has a "write" method which updates its internal buffer,
    which is periodically consumed by the ASR instance in which it is inserted.

    :buffer_size: Size of the internal buffer (in bytes)
    :yields: bytestrings of size <buffer_size>

    Terminates only if the "finish" method is called, in which case the
    remaining buffer is sent regardless of its size.
    """
    def __init__(self, chunk_size=4096):
        self._buffer = b""
        self._chunk_size = chunk_size
        self._finished = False

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            if len(self._buffer) >= self._chunk_size:
                r = self._buffer[:self._chunk_size]
                self._buffer = self._buffer[self._chunk_size:]
                return r
            elif self._finished:
                if self._buffer:
                    r = self._buffer
                    self._buffer = b''
                    return r
                else:
                    raise StopIteration
            time.sleep(.05)

    def write(self, byte_str):
        """
        Writes to the buffer.

        :byte_str: A byte string (char array). Currently only 16-bit signed
                   little-endian linear PCM is accepted.
        """
        self._finished = False
        self._buffer += byte_str

    def finish(self):
        """
        Signals the ASR instance that one's finished writing and is now waiting
        for the recognition result.
        """
        self._finished = True
