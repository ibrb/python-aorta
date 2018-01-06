import datetime


class BaseBuffer:
    """Specifies the interface for all outbound message buffer
    implementations.
    """

    def delay(self, delay=None):
        """Return a tuple containing two :class:`datetime.datetime`
        objects, representing the queued-at time and no-transmission-before
        time.
        """
        assert (delay or 0) >= 0,\
            "`delay` must be a positive integer"
        tzinfo = datetime.timezone(datetime.timedelta(hours=0))
        qat = nbf = datetime.datetime.utcnow().replace(tzinfo=tzinfo)
        if delay:
            nbf += datetime.timedelta(seconds=delay)
        return qat, nbf

    def put(self, message, delay=None):
        """Place a new message on the message queue."""
        return self.queue(message, *self.delay(delay))

    def queue(self, message, qat, nbf):
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

    def on_transmitted(self, delivery, message):
        """Assumed to be invoked when the sender has transmitted
        the AMQP message to the remote and received a delivery
        tag i.e. immediately after the :meth:`proton.Sender.send()`
        call.

        Args:
            delivery: a :class:`proton.Delivery` instance representing
                the transfer.
            message: a :class:`proton.Message` instance containing the
                AMQP message.

        Returns:
            None
        """
        raise NotImplementedError
