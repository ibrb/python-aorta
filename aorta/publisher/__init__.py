import os

from aorta.messaging import EventMessage
from aorta.buf.spooled import SpooledBuffer
from .base import BasePublisher


class EventPublisher(BasePublisher):
    """A :class:`BasePublisher` implementation that provides
    additional functionality to publish event messages.
    """

    def __init__(self, spool=None, *args, **kwargs):
        buf = SpooledBuffer(spool=spool or os.getenv('AORTA_SPOOL_DIR'))
        BasePublisher.__init__(self, backend=buf)

    def publish(self, name, params, on_settled=None):
        """Published a message representing observed event `name` with
        the given parameters `params`.

        Args:
            name (str): the fully-qualified name of the observed
                event.
            params (dict): a dictionary containing the event parameters.

        Returns:
            None
        """
        message = EventMessage()
        message.set_object_type(name)
        message.body = params
        return super(EventPublisher, self).publish(message,
            on_settled=on_settled)
