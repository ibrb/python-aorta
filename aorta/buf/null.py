from .base import BaseBuffer


class NullBuffer(BaseBuffer):
    """A :class:`BaseBuffer` implementation that does not persist
    messages on durable storage media. Use for testing only. Not
    threadsafe.
    """

    @property
    def failed(self):
        return len(self._errors)

    @property
    def deliveries(self):
        return len(self._deliveries)

    @property
    def queued(self):
        return len(self._queue)

    def __init__(self, *args, **kwargs):
        super(BaseBuffer, self).__init__(*args, **kwargs)
        self._queue = []
        self._deliveries = {}
        self._errors = {}

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
        self._queue.append([message, qat, nbf])

    def pop(self):
        """Return the next :class:`proton.Message` instance
        that is queued for transmission. This may delete the
        message data from the persistent storage medium.
        """
        now = self.now()
        for i, item in enumerate(self._queue):
            message, qat, nbf = item
            if nbf > now:
                continue

            break
        else:
            return None

        return self._queue.pop(i)[0]

    def track(self, host, port, source, target, link, tag, message):
        """Track the delivery of `message` to the AMQP remote peer.

        Args:
            host (str): IP address of the AMQP peer.
            port (int): port at which the AMQP peer is listening.
            source (str): source name, if applicable.
            target (str): target name, if applicable.
            link (str): link identifier.
            tag (str): unique delivery tag.
            message (proton.Message): the AMQP message.

        Returns:
            None
        """
        self._deliveries[tag] = message

    def error(self, tag, message, undeliverable=False):
        """Invoked when a message could not be delivered.

        Args:
            tag (str): identifies the delivey.
            message (proton.Message): the message that errored.
            undeliverable (bool): indicates if the message was
                undeliverable. If `undeliverable` is ``False``,
                the message was rejected by the remote, it this
                parameter is ``True``, it could not be delivered
                to the remote.

        Returns:
            None
        """
        self._errors[tag] = message

    def __len__(self):
        return len(self._queue)
