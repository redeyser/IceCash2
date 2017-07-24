#!/usr/bin/python2
import pytest
import lsusb


def test_lsserial_1():
    assert sorted(lsusb.lsdir('/dev')) == sorted(lsusb.lsdir_old('/dev'))
    assert sorted(lsusb.lsserial()) == sorted(lsusb.lsserial_old())
