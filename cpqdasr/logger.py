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

Logger class implementation.
"""
from datetime import datetime


class Logger:
    """
    Simple logger which accepts any output stream and levels of verbosity.

    :ostream: The output stream (stderr, files or other compatible objects)
    :alias: A string which will be pre-appended to the log. Useful for
            logs shared across processes.
    :log_level: A string which may be, in order of increasing verbosity:
                "error", "warning", "info" or "debug"
    """

    def __init__(self, ostream, alias="", log_level="warning"):
        self._ostream = ostream
        if log_level == "error":
            self._log_level = 0
        elif log_level == "info":
            self._log_level = 2
        elif log_level == "debug":
            self._log_level = 3
        else:
            self._log_level = 1
        self._alias = alias

    def _write_log(self, s, log_level):
        if self._ostream is not None:
            self._ostream.write(
                "[{}] [{}] [{}]: {}\n".format(
                    str(datetime.now()), self._alias, log_level, s
                )
            )
            self._ostream.flush()

    def error(self, s):
        if self._log_level >= 0:
            self._write_log(s, "ERROR")

    def warning(self, s):
        if self._log_level >= 1:
            self._write_log(s, "WARNING")

    def info(self, s):
        if self._log_level >= 2:
            self._write_log(s, "INFO")

    def debug(self, s):
        if self._log_level >= 3:
            self._write_log(s, "DEBUG")
