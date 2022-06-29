# -*- coding: utf-8 -*-
#
#  Copyright 20122 CPqD. All rights reserved.
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

class WsParser():
  def __init__(self, payload):
    self.payload = payload
    self.command = ""
    self.version = ""
    self.pars = {}
    self.body = ""
    self.length = 0

  def set_payload(self, payload):
    self.__init__(payload)

  def ProcessLine(self, line):
    if line.find("ASR") >= 0:
      self.command = line.split()[2]
      self.version = line.split()[1]
    elif line.count(":") == 1:
      self.pars[line.split(':')[0].lstrip()] = line.split(':')[1].lstrip().rstrip('\r')
    else:
      #print("Not process: {}".format(line))
      pass

  def Parse(self):
    #print(self.payload)
    try:
        payload = self.payload.decode("utf-8")
    except:
        payload = self.payload
    lines = payload.split("\n")
    #print(lines)
    for l in lines:
      if len(l):
        self.ProcessLine(l)
    length = self.pars.get("Content-Length")
    if length != None:
      #print("Length: {}".format(length))
      try:
        self.length = int(length)
        self.body = self.payload[len(self.payload)-self.length:]
      except:
        print("Exception")
        pass

  def get_command(self):
    return self.command

  def get_version(self):
    return self.version

  def get_params(self):
    return self.pars

  def get_body(self):
    return self.body

  def Dump(self):
    str= "ASR {} {}\r\n".format(self.version, self.command)
    for p in self.pars:
      str += "{}: {}\r\n".format(p, self.pars[p])
    if (self.length > 0):
      str += "\r\n{}".format(self.body)
    return str
