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

RecognitionLister interface for recognition callbacks
"""


class RecognitionListener():
    """
    Class with callback methods called in certain recognition states.

    You should subclass this class, reimplementing methods which you wish
    to add functionality.
    """
    def onListening(self):
        """
        Called when recognition enters on Listening state, i.e. when the
        speech recogntion server recieves acknowledges the first audio packet.
        """
        pass

    def onSpeechStart(self, time):
        """
        Called when the speech recognition server detects speech activity on
        the sent packages.

        :time: The time since "onListening", in milliseconds
        """
        pass

    def onSpeechStop(self, time):
        """
        Called when the speech recognition server detects end of speech on the
        sent packages.

        :time: The time since "onListening", in milliseconds
        """
        pass

    def onPartialRecognition(self, partial):
        """
        Called when a partial result is available.

        :partial: Instance of PartialRecognitionResult
        """
        pass

    def onRecognitionResult(self, result):
        """
        Called when a final result is available.

        :result: Instance of RecognitionResult
        """
        pass

    def onError(self, error):
        pass
