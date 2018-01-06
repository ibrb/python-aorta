from .base import BaseBuffer


class NullBuffer(BaseBuffer):
    """A :class:`BaseBuffer` implementation that does not persist
    messages on durable storage media. Use for testing only. Not
    threadsafe.
    """

    def __init__(self, *args, **kwargs):
        super(BaseBuffer, self).__init__(*args, **kwargs)
        self._queue = []
        self._deliveries = {}

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


        Returns:
            None
        """
        self._deliveries[tag] = message

    def __len__(self):
        return len(self._queue)
