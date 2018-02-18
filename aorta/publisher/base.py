import functools
import logging
import os
import uuid

from proton import Disposition

from aorta.lib import timezone
from aorta.buf.null import NullBuffer


class BasePublisher:
    """The base class for all message publisher implementations.

    Args:
        backend: the :class:`~aorta.publisher.storage.base.BaseOutboundBuffer`
            implementation that is used to persist messages until the
            remote AMQP peer accepts them.
    """
    retransmission_delay = 5.0

    def __init__(self, backend=None, logger=None):
        self.logger = logger or logging.getLogger('aorta.publisher')
        self.backend = backend
        if self.backend is None:
            self.backend = NullBuffer()

    def delay(self, n):
        """Calculates the delay in seconds before retransmitting a
        message, based on the delivery count.
        """
        return int(self.retransmission_delay*(1.25**n))

    def clean_properties(self, message):
        """Hook to validate the application properties of an AMQP
        message.

        The default implementation always succesfully validates the
        properties. Subclasses that override :meth:`validate_properties()`
        should raise a :exc:`~aorta.exc.ValidationError` on validation
        failure.

        Implementations that wish to modify the properties during cleaning
        and validation should update the :class:`~Message` instance by setting
        its :attr:`~aorta.datastructures.message.Message.properties` attribute.

        Args:
            message: a :class:`~aorta.datastructures.Message` instance.

        Returns:
            dict: the cleaned and validated application properties.

        Raises:
            aorta.exc.ValidationError: the application properties were
                not valid.
        """
        return message.properties

    def publish(self, message, on_settled=None):
        """Publish :class:`proton.Message` `message`. Set all properties
        required by the Aorta framework and forward the message to
        the persistence backend for outbound queueing.

        For all messages in the Aorta environment, the framework
        mandates that the following properties are defined:

        -   ``creation_time``
        -   ``id``
        -   ``correlation_id``

        The :meth:`publish()` must ensure that these properties are
        either set by the caller, or provide values. For the `id`
        and `correlation_id`, random UUIDs are generated if they are
        not provided.

        Args:
            message: a :class:`proton.Message` instance.
            on_settled: a callable that is invoked, with the message
                as its first positional argument, when the durability
                responsiblity is transferred from the caller to the
                backend.

        Returns:
            None
        """
        # The Aorta framework considers protection against data-loss one
        # of its core features. The `durable` property of a message is
        # for this reason set to True. This does mean, however` that
        # intermediaries, that do no have the ability to take responsibility
        # of message persistence, may reject the message.
        message.durable = True

        # Ensure that the delivery count property is correctly initialized
        # to 0.
        message.delivery_count = 0

        if not message.creation_time:
            message.creation_time = timezone.now()
        message.creation_time = int(message.creation_time)

        if message.id is None:
            message.id = uuid.UUID(bytes=os.urandom(16))

        if message.correlation_id is None:
            message.correlation_id = uuid.UUID(bytes=os.urandom(16))

        # Make some assertions to ensure the state is as we expect. This
        # should never fail in production environments, however.
        assert isinstance(message.creation_time, (int,float)),\
            repr(message.creation_time)
        assert isinstance(message.id, uuid.UUID), repr(message.id)
        assert isinstance(message.correlation_id, uuid.UUID),\
            repr(message.correlation_id)

        message.id = message.id.hex
        message.correlation_id = message.correlation_id.hex

        # Run validation on the application properties. The default
        # implementation is expected to do nothing. Subclasses may
        # override this method to implement domain-specific validation.
        self.clean_properties(message)

        # Place the message on the outbound message queue and have the
        # backend schedule it for transission to the remote AMQP peer.
        if on_settled is not None:
            on_settled = functools.partial(self.on_responsibility_transferred,
                on_settled)
        self.backend.put(message, on_settled=on_settled)

    def on_responsibility_transferred(self, func, message):
        """Invoke `func` when the responsibility regarding the persistence
        of `message` is released from the caller.
        """
        func(message)
