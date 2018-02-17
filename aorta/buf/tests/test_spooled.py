import tempfile
import unittest

from ..spooled import SpooledBuffer
from .base import BaseBufferImplementationTestCase


class SpooledBufferImplementationTestCase(BaseBufferImplementationTestCase):
    __test__ = True

    def setUp(self):
        super(SpooledBufferImplementationTestCase, self).setUp()
        self.buf = SpooledBuffer(spool=tempfile.mkdtemp())

