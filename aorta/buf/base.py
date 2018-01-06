import contextlib
import datetime
import os
import uuid


class BaseBuffer:
    """Specifies the interface for all outbound message buffer
    implementations.

    All :class:`BaseBuffer` implementations hold the following
    assumptions:

    -   AMQP links are named correctly. This means that if the link,
        for whatever reason, gets interrupted, it can be re-established
        and the deliveries resumed. It also allows the :class:`BaseBuffer`
        implementations to distinguish deliveries from different links.
    -   The preceding item implies that containers must also be properly
        named, as the AMQP 1.0 specification states in section 2.6.1:
        *"A link’s name uniquely identifies the link from the container
        of the source to the container of the target node, e.g. if the
        container of the source node is A, and the container of the target
        node is B, the link may be globally identified by the (ordered)
        tuple (A,B,<name>)."*
    -   :class:`BaseBuffer` implementations assume that container ids
        a globally unique in the AMQP network.
    -   :class:`BaseBuffer` also assumes that the ``delivery-tag`` on
        message transfers is **globally** unique. This deviates from the
        AMQP 1.0 specification, section 2.6.12, which only states *"Each
        delivery MUST be identified by a delivery-tag chosen by the sending
        application. The delivery-tag MUST be unique amongst all deliveries
        that could be considered unsettled by either end of the Link."*.
        This decision was made to prevent collisions between the delivery
        tags that were auto-generated by the :mod:`proton` library, on
        different links in different processes, but using the same data
        store.
    """

    def generate_tag(self):
        """Generates a globally unique delivery tag."""
        return uuid.UUID(bytes=os.urandom(16)).hex

    def now(self):
        """Return an aware :class:`datetime.datetime` instance
        representing the current date and time.
        """
        tzinfo = datetime.timezone(datetime.timedelta(hours=0))
        return datetime.datetime.utcnow().replace(tzinfo=tzinfo)

    def delay(self, delay=None):
        """Return a tuple containing two :class:`datetime.datetime`
        objects, representing the queued-at time and no-transmission-before
        time.
        """
        assert (delay or 0) >= 0,\
            "`delay` must be a positive integer"
        qat = nbf = self.now()
        if delay:
            nbf += datetime.timedelta(seconds=(delay/1000))
        return qat, nbf

    def put(self, message, delay=None):
        """Place a new message on the message queue."""
        return self.enqueue(message, *self.delay(delay))

    def enqueue(self, message, qat, nbf):
        """Queue a new message for transmission.

        Args:
            message (proton.Message): the message to enqueue.
            qat (datetime.datetime): the date and time at which
                the message was queued.
            nbf (datetime.datetime): the date and time before which
                the message may not be transmitted.

        Returns:
            None
        """
        raise NotImplementedError

    def pop(self):
        """Return the next :class:`proton.Message` instance
        that is queued for transmission. This may delete the
        message data from the persistent storage medium.
        """
        raise NotImplementedError



    def transfer(self, host, source, target, sender):
        """Transmit the next message in the queue to the AMQP remote
        peer.

        Args:
            host (str): a string in the format ``host:port`` identifying
                the remote AMQP peer.
            source (str): the name of the source (local) container.
            target (str): the name of the target (remote) container.
            sender (proton.Sender): the link over which the message will
                be sent.

        Returns:
            None
        """
        addr, port = host.split(':')
        assert port.isdigit(), "Invalid host: %s" % host
        with self.transaction():
            message = self.pop()
            if message is None:
                return

            tag = self.generate_tag()
            delivery = sender.send(self.pop(), tag)

            assert delivery.tag == tag
            self.track(host, port, source, target, sender.name,
                delivery.tag, message)

    def track(self, host, port, source, target, link, tag, message):
        """Track the delivery of `message` to the AMQP remote peer.

        Args:


        Returns:
            None
        """
        raise NotImplementedError

    @contextlib.contextmanager
    def transaction(self):
        """Start a transaction. The default implementation does nothing;
        :class:`BaseBuffer` implementations should define their own
        transactional behavior. It is assumed that the transaction
        begins when the context manager yields, commits when the context
        is exited, and rollbacks when an exception occurs.
        """
        yield

    def __len__(self):
        raise NotImplementedError
