#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=no-self-use, pointless-statement, missing-docstring, invalid-name
import pytest

import time

from .. import guess_file_info


def case1():
    return guess_file_info(u'Fear.and.Loathing.in.Las.Vegas.FRENCH.ENGLISH.720p.HDDVD.DTS.x264-ESiR.mkv')


def case2():
    return guess_file_info(u'Movies/Fantastic Mr Fox/Fantastic.Mr.Fox.2009.DVDRip.{x264+LC-AAC.5.1}{Fr-Eng}{Sub.Fr-Eng}-™.[sharethefiles.com].mkv')


def case3():
    return guess_file_info(u'Series/dexter/Dexter.5x02.Hello,.Bandit.ENG.-.sub.FR.HDTV.XviD-AlFleNi-TeaM.[tvu.org.ru].avi')


def case4():
    return guess_file_info(u'Movies/The Doors (1991)/09.03.08.The.Doors.(1991).BDRip.720p.AC3.X264-HiS@SiLUHD-English.[sharethefiles.com].mkv')


@pytest.mark.benchmark(
    group="Performance Tests",
    min_time=1,
    max_time=2,
    min_rounds=5,
    timer=time.time,
    disable_gc=True,
    warmup=False
)
@pytest.mark.skipif(True, reason="Disabled")
class TestBenchmark(object):
    def test_case1(self, benchmark):
        ret = benchmark(case1)
        assert ret

    def test_case2(self, benchmark):
        ret = benchmark(case2)
        assert ret

    def test_case3(self, benchmark):
        ret = benchmark(case3)
        assert ret

    def test_case4(self, benchmark):
        ret = benchmark(case4)
        assert ret

