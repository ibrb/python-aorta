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

    def publish(self, message):
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
        self.backend.put(message)

    def on_settled(self, tag, state, disposition):
        """Invoked when the AMQP peers agree on the state of a transfer.

        A transfer has three possible final outcomes (terminal delivery
        states):

        -   ``ACCEPTED``
        -   ``REJECTED``
        -   ``RELEASED``
        -   ``MODIFIED``

        The ``ACCEPTED`` outcome means that the remote has accepted
        the message and fullfills the conditions specified in the
        message headers e.g. durability.

        The ``REJECTED`` outcome means that the remote does not wish to handle
        the AMQP message because it is invalid and/or unprocessable.

        The ``RELEASED`` outcome indicates that the message was
        not (and will not be) processed.

        The ``MODIFIED`` outcome indicates that the message was modified,
        but not processed.

        For more information on terminal delivery states, consult the
        documentation on their respective methods or the AMQP 1.0
        specification, section 3.4.

        Args:
            tag (str): identifies the delivery that was settled.
            state (proton.DispositionType): specifies the final outcome of
                the message transfer.
            disposition (proton.Disposition): the message disposition
                describing the remote outcome

        Returns:
            None
        """
        if state == Disposition.ACCEPTED:
            self.backend.on_accepted(delivery, self.backend.get(tag))
        if state == Disposition.REJECTED:
            self.backend.on_rejected(delivery, self.backend.get(tag))
        if state == Disposition.RELEASED:
            self.backend.on_released(delivery, self.backend.get(tag))
        if state == Disposition.MODIFIED:
            self.backend.on_modified(delivery, self.backend.get(tag))
