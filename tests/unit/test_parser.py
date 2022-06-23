# -*- coding: utf-8 -*-
#
#  Copyright 2022 CPqD. All rights reserved.
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
@author: Fabiano Zaruch Chinasso

ASR Server WebSocket parser test
"""

from cpqdasr import WsParser

payload = \
"ASR 1.0 RESPONSE\r\n" \
"Handle: 201604081523970032\r\n" \
"Method: CREATE_SESSION\r\n" \
"Status: IDLE\r\n" \
"Content-Length: 68\r\n" \
"Result: SUCCESS\r\n\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf"
parser = WsParser(payload)
parser.Parse()
str = parser.Dump()
assert str == payload
assert "RESPONSE" == parser.get_command()
assert "1.0" == parser.get_version()
assert "body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf" == parser.get_body()

payload2 = \
"ASR 1.0 RESPONSE\r\n" \
"Handle:201604081523970032\r\n" \
"Method:CREATE_SESSION\r\n" \
"Status:IDLE\r\n" \
"Content-Length:68\r\n" \
"Result:SUCCESS\r\n\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf"

parser.set_payload(payload2)
parser.Parse()
str = parser.Dump()
#print(str)
assert str == payload
assert "RESPONSE" == parser.get_command()
assert "1.0" == parser.get_version()
assert "body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf" == parser.get_body()

payload3 = \
"ASR 1.0 RESPONSE\r\n\r\n" \
"Handle:201604081523970032\r\n" \
"Method:CREATE_SESSION\r\n" \
"Status:IDLE\r\n" \
"Content-Length:68\r\n" \
"Result:SUCCESS\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf"

parser.set_payload(payload3)
parser.Parse()
str = parser.Dump()
assert str == payload
assert "RESPONSE" == parser.get_command()
assert "1.0" == parser.get_version()
assert "body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf" == parser.get_body()

payload4 = \
"ASR 1.0 RESPONSE\r\n\r\n" \
"Handle:201604081523970032\r\n" \
"Method:CREATE_SESSION\r\n" \
"Status:IDLE\r\n" \
"Content-Length:70\r\n" \
"Result:SUCCESS\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf\r\n"

p_ref4 = \
"ASR 1.0 RESPONSE\r\n" \
"Handle: 201604081523970032\r\n" \
"Method: CREATE_SESSION\r\n" \
"Status: IDLE\r\n" \
"Content-Length: 70\r\n" \
"Result: SUCCESS\r\n\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf\r\n"
parser.set_payload(payload4)
parser.Parse()
str = parser.Dump()
#print(str)
#print(len(str))
#print(p_ref4)
#print(len(p_ref4))

assert str == p_ref4
assert "RESPONSE" == parser.get_command()
assert "1.0" == parser.get_version()
assert "body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf\r\n" == parser.get_body()

payload5 = \
"Handle:201604081523970032\r\n" \
"Method:CREATE_SESSION\r\n" \
"ASR 1.0 RESPONSE\r\n\r\n" \
"Result:SUCCESS\r\n" \
"Status:IDLE\r\n" \
"Content-Length:68\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf"
p_ref5 = \
"ASR 1.0 RESPONSE\r\n" \
"Handle: 201604081523970032\r\n" \
"Method: CREATE_SESSION\r\n" \
"Result: SUCCESS\r\n" \
"Status: IDLE\r\n" \
"Content-Length: 68\r\n\r\n" \
"body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf"
parser.set_payload(payload5)
parser.Parse()
str = parser.Dump()
assert str == p_ref5
assert "RESPONSE" == parser.get_command()
assert "1.0" == parser.get_version()
assert "body\nsdfsidkf sdfsldk sldkfslfsidlfsidksldijfsdifldfk sodfjsdlfkjsdf" == parser.get_body()
