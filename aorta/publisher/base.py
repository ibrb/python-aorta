import logging
import os
import uuid

from proton import Disposition

from aorta.lib import timezone
from aorta.storage.null import NullOutboundBuffer


class BasePublisher:
    """The base class for all message publisher implementations.

    Args:
        backend: the :class:`~aorta.publisher.storage.base.BaseOutboundBuffer`
            implementation that is used to persist messages until the
            remote AMQP peer accepts them.
    """
    retransmission_delay = 5.0

    def __init_(self, backend=None, logger=None):
        self.logger = logger or logging.getLogger('aorta.publisher')
        self.backend = backend or NullOutboundBuffer()

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

        # Run validation on the application properties. The default
        # implementation is expected to do nothing. Subclasses may
        # override this method to implement domain-specific validation.
        self.clean_properties(message)

        # Place the message on the outbound message queue and have the
        # backend schedule it for transission to the remote AMQP peer.
        self.backend.put(message)

    def on_settled(self, delivery, state, disposition):
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
            delivery (proton.Delivery): the message transfer that is being
                settled.
            state (proton.DispositionType): specifies the final outcome of
                the message transfer.
            disposition (proton.Disposition): the message disposition
                describing the remote outcome

        Returns:
            None
        """
        if state == Disposition.ACCEPTED:
            self.on_accepted(delivery, self.backend.get(delivery.tag),
                disposition)
        if state == Disposition.REJECTED:
            self.on_rejected(delivery, self.backend.get(delivery.tag),
                disposition)
        if state == Disposition.RELEASED:
            self.on_released(delivery, self.backend.get(delivery.tag),
                disposition)
        if state == Disposition.MODIFIED:
            self.on_modified(delivery, self.backend.get(delivery.tag),
                disposition)

    def on_accepted(self, delivery, message, disposition):
        """Invoked when the remote has indicated that it accepts the message.

        Args:
            delivery (proton.Delivery): described the final state of the
                message tranfer.
            message (proton.Message): the AMQP message.
            disposition (proton.Disposition): the message disposition
                describing the remote outcome

        Returns:
            None
        """
        pass

    def on_rejected(self, delivery, message, disposition):
        """Invoked when the remote has terminated the transfer with the
        ``REJECTED`` outcome.

        The rejected outcome is described in the AMQP 1.0 specification,
        section 3.4.3: *"At the target, the rejected outcome is used to
        indicate that an incoming message is invalid and therefore
        unprocessable. The rejected outcome when applied to a message
        will cause the delivery-count to be incremented in the header of
        the rejected message."*

        This outcome indicates that the message was semantically invalid
        or otherwise unprocessable by the remote.

        Args:
            delivery (proton.Delivery): described the final state of the
                message transfer.
            message (proton.Message): the AMQP message.
            disposition (proton.Disposition): the message disposition
                describing the remote outcome.

        Returns:
            None
        """
        message.delivery_count += 1
        self.backend.error(delivery.tag, message)

    def on_released(self, delivery, message, disposition):
        """Invoked when the remote decides to release a message. Requeue
        message transmission with a delay of :attr:`retransmission_delay`
        seconds.

        Section 3.4.4 of the AMQP 1.0 specification states about the
        ``RELEASED`` outcome: *"At the source the released outcome means
        that the message is no longer acquired by the receiver, and has
        been made available for (re-)delivery to the same or other targets
        receiving from the node. The message is unchanged at the node (i.e.,
        the delivery-count of the header of the released message MUST NOT be
        incremented). As released is a terminal outcome, transfer of payload
        data will not be able to be resumed if the link becomes suspended. A
        delivery can become released at the source even before all transfer
        frames have been sent. This does not imply that the remaining
        transfers for the delivery will not be sent. The source MAY
        spontaneously attain the released outcome for a message (for example
        the source might implement some sort of time-bound acquisition lock,
        after which the acquisition of a message at a node is revoked to
        allow for delivery to an alternative consumer)."*

        Args:
            delivery (proton.Delivery): described the final state of the
                message transfer.
            message (proton.Message): the AMQP message.
            disposition (proton.Disposition): the message disposition
                describing the remote outcome.

        Returns:
            None
        """
        self.backend.put(message, delay=self.delay(message.delivery_count))

    def on_modified(self, delivery, message, disposition):
        """Invoked when the remote modified the message.

        Section 3.4.5. of the AMQP 1.0 specification describes the
        ``MODIFIED`` outcome: *"At the target, the modified outcome is
        used to indicate that a given transfer was not and will not be
        acted upon, and that the message SHOULD be modified in the specified
        ways at the node."

        Args:
            delivery (proton.Delivery): described the final state of the
                message transfer.
            message (proton.Message): the AMQP message.
            disposition (proton.Disposition): the message disposition
                describing the remote outcome.

        Returns:
            None
        """
        if disposition.undeliverable:
            self.backend.error(delivery.tag, message, undeliverable=True)
            return
        self.backend.put(message, delay=self.delay(message.delivery_count))
