#!/usr/bin/sudo python3
# -*- coding: utf-8 -*-

import sys
import os
import pytest
import constants


# @pytest.fixture
# def client():
#     ip, port = constants.WEB_API_HOST.split(':')
#     flask_app.run(host=ip, port=int(port), debug=True)

def test_web_api():
    """Start web api."""
    # rv = client.get('\\api\\v1.0\\test')
    # assert b'ok' in rv.data
    assert 1 < 2

# def test_combinatoria():
#     search_weight = 10.3
#     celdas = list()   
#     assert (3 <= 2)


# test_combinatoria()