import unittest

from ..null import NullBuffer
from .base import BaseBufferImplementationTestCase


class NullBufferImplementationTestCase(BaseBufferImplementationTestCase):
    __test__ = True

    def setUp(self):
        super(NullBufferImplementationTestCase, self).setUp()
        self.buf = NullBuffer()
