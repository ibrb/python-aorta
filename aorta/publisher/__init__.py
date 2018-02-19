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

    def publish(self, name, params=None, on_settled=None, observed=None,
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
            on_settled: a callback function that is invoked, with the
                :class:`~aorta.messaging.EventMessage` as its first
                positional argument, when durability responsibility
                is transferred to the backend.

        Returns:
            None

        The :meth:`publish()` method ensures that all properties and
        annotations (refer to the AMQP 1.0 specification for their
        meanings) required by the Aorta framework are set on each
        outgoing message. For ``Event`` messages specifically,
        :meth:`publish()` provides defaults for the following
        properties:

        - `aorta.const.P_EVENT_OBSERVED`
        - `aorta.const.P_EVENT_OCCURRED`

        This is in addition to the properties set by the :class:`EventPublisher`
        superclasses.

        It also guarantees that the message body is a :class:`dict`.
        """
        message = EventMessage()
        message.set_object_type(name)
        message.body = params or {}
        message.properties[const.APROP_EVENT_OBSERVED] =\
            observed or timezone.now()
        message.properties[const.APROP_EVENT_OCCURRED] =\
            occurred or timezone.now()
        return super(EventPublisher, self).publish(message,
            on_settled=on_settled)
