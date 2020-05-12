#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 10:06:08 2018

@author: valterf

Common functions for tests
"""
from cpqdasr import SpeechRecognizer, FileAudioSource
from multiprocessing import Process
from time import time
from sys import stdout


def recognize_worker(
    url, asr_kwargs, wav_path, lm_list, recognitions, executions, assertion
):
    error_msg = "Parameters: url:{}, wav_path:{}, lm_list:{}".format(
        url, wav_path, lm_list
    )
    error_msg += "\nOn execution {}/{}\nOn recognition {}/{}"
    error_msg += "\nError from assertion: {}"
    for e in range(executions):
        beg = time()
        asr = SpeechRecognizer(url, **asr_kwargs)
        for r in range(recognitions):
            asr.recognize(FileAudioSource(wav_path), lm_list)
            success, msg = assertion(asr.wait_recognition_result())
            if not success:
                error_msg = error_msg.format(executions, e, recognitions, r, msg)
                assert success, error_msg
        asr.close()
        asr._logger.info("[TIMER] TotalTime: {} s".format(time() - beg))


def stress_recognition(
    url,
    asr_kwargs,
    wav_path,
    lm_list,
    session_range=(0, 1),
    recognitions=1,
    executions=1,
    assertion=lambda x: (True, ""),
):
    """
    Stresses recognition by testing a range of simultaneous sessions.
    This stresses both client and server, and should be useful for simulating
    high workload scenarios.

    :url:           The CPqD ASR Server Websocket URL
    :asr_kwargs:    Dict for the SpeechRecognizer kwargs
    :wav_path:      Path for the wave file to be tested
    :lm_list:       Instance of LanguageModelList to execute tests
    :session_range: Range of simultaneous sessions to test. Statistics for
                    each number will be generated on the log stream with
                    discriminated aliases for each SpeechRecognizer instance.
    :recognitions:  Number of recognitions to be run with each SpeechRecognizer
                    instance.
    :executions:    Number of executions to be run with each worker. The
                    execution involves the full process of creating and
                    destroying SpeechRecognizer instances inside each worker.
    :assertion:     A function which receives a list  RecognitionResult and
                    returns a tuple of bool/string depending on the criterion
                    of success for the running test and the intended message
                    to be passed in case of failure.

    """
    for i in range(*session_range):
        ps = []
        for s in range(i + 1):
            asr_kwargs["alias"] = "Session {}/{} ".format(s + 1, i + 1)
            ps.append(
                Process(
                    target=recognize_worker,
                    args=(
                        url,
                        asr_kwargs,
                        wav_path,
                        lm_list,
                        recognitions,
                        executions,
                        assertion,
                    ),
                )
            )
            ps[-1].start()
        for p in ps:
            p.join()
            assert p.exitcode == 0
