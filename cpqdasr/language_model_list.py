#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 26 16:25:15 2017

@author: valterf
"""
import os


class LanguageModelList:
    def __init__(self, *args):
        self._lm_list = []
        for lm in args:
            error_msg = "Invalid lm: {}".format(lm)
            if type(lm) == str:
                self._lm_list.append(lm)
            elif type(lm) == tuple:
                assert len(lm) == 2, error_msg
                assert type(lm[0]) == str, error_msg
                assert type(lm[1]) == str, error_msg
                self._lm_list.append(lm)
            else:
                assert False, error_msg
        assert len(self._lm_list) > 0, \
            "You need at least 1 LM for instantiating a LanguageModelList"

    @staticmethod
    def fromURI(uri):
        """
        Prepares a URI for building a LanguageModelList

        The only thing this function does is checking if the string is a valid
        URI and returns it for language model list construction.
        You may pass plain strings for the LanguageModelList instead, and the
        ASR server is expected to return informative errors if strings are
        invalid.

        :uri:      A URI in plain text
        """
        assert isinstance(uri, str)
        assert uri.split(':')[0] in ("file", "builtin", "http")
        return uri

    @staticmethod
    def inlineGrammar(alias, body):
        """
        Prepares an inline grammar for building a LanguageModelList

        This is a naive function which checks if both alias and body are
        strings. All significant checks are expected to be done server-side.
        You may pass tuples of strings for the LanguageModelList instead, and
        the ASR server is expected to return informative errors if strings are
        invalid.

        :alias:   the text id for the grammar which will appear in the returned
                  results, marking them as pertaining to the passed grammar
        :body:    the body of the grammar in plain text, either in XML or ABNF
                  format, in compliance with the SRGS specification
                  https://www.w3.org/TR/speech-grammar/
        """
        assert isinstance(alias, str)
        assert isinstance(body, str)
        return (alias, body)

    @staticmethod
    def grammarFromPath(alias, path):
        """
        Reads a grammar file and returns a tuple with its id and body

        :alias:   the text id for the grammar which will appear in the returned
                  results, marking them as pertaining to the passed grammar
        :path:    the full path of the grammar, either in XML or ABNF format,
                  in compliance with the SRGS specification
                  https://www.w3.org/TR/speech-grammar/
        """
        assert isinstance(path, str)
        assert os.path.isfile(path)
        with open(path, 'r') as f:
            body = f.read()
        return (alias, body)
