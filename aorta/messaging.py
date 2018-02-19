import os
import uuid

import proton

import aorta.const


class Message(proton.Message):
    """Augment :class:`proton.Message` with additional methods and
    properties.
    """
    pass


class AortaMessage(Message):
    """The base class for all Aorta message types."""
    message_class = None

    def __init__(self, *args, **kwargs):
        Message.__init__(self, *args, **kwargs)
        if not isinstance(self.properties, dict):
            self.properties = {
                aorta.const.P_AORTA_ID: uuid.UUID(bytes=os.urandom(16)).hex,
                aorta.const.P_ENCRYPTED: False,
                aorta.const.P_SIGNED: False
            }
        assert self.message_class is not None,\
            "%s.message_class is None" % type(self).__name__
        self.properties[aorta.const.P_MESSAGE_CLASS] = self.message_class

    def set_object_type(self, name):
        """Sets the object type in the application properties."""
        self.properties[aorta.const.P_OBJECT_TYPE] = name


class EventMessage(AortaMessage):
    message_class = 'event'
