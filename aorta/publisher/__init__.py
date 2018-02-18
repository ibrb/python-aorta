import os
import uuid

from aorta import const
from aorta.lib import timezone
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

    def publish(self, name, params, on_settled=None, observed=None,
        occurred=None):
        """Published a message representing observed event `name` with
        the given parameters `params`.

        Args:
            name (str): the fully-qualified name of the observed
                event.
            params (dict): a dictionary containing the event parameters.
            observed (int): the number of milliseconds since the UNIX epoch,
                specifying the date and time at which the event was observed.
            occurred (int): the number of milliseconds since the UNIX epoch,
                specifying the date and time at which the event occurred.

        Returns:
            None
        """
        message = EventMessage()
        message.set_object_type(name)
        message.body = params
        message.properties[const.APROP_EVENT_OBSERVED] =\
            observed or timezone.now()
        message.properties[const.APROP_EVENT_OCCURRED] =\
            occurred or timezone.now()
        return super(EventPublisher, self).publish(message,
            on_settled=on_settled)
