#!/usr/bin/env python3
import argparse
import logging
import os
import random
import signal
import sys
import threading
import time

from proton.handlers import MessagingHandler
from proton.reactor import ApplicationEvent
from proton.reactor import Container
from proton.reactor import EventInjector
import proton

from aorta.buf.spooled import SpooledBuffer


parser = argparse.ArgumentParser(
    prog='aorta publisher',
    description="Publish to the messaging infrastructure from the local spool.")
parser.add_argument('-R', dest='peers', default=[], action='append',
    help="specifies the remote AMQP peers by ip:port.")
parser.add_argument('--spool', type=os.path.abspath, default='/var/spool/aorta',
    help="specifies the spool directory (default: %(default)s)")
parser.add_argument('--loglevel', default='INFO',
    choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
    help="specifies the logging verbosity (default: %(default)s)")
parser.add_argument('--ingress-channel', default='aorta.ingress',
    help="the ingress message channel at the AMQP peer (default: %(default)s)")
parser.add_argument('--no-sasl', action='store_true',
    help="disable SASL.")


class MessagePublisher(MessagingHandler):
    framerate = 20
    target = 'aorta.ingress'

    @property
    def sendables(self):
        # TODO: Also check if the links are actually established
        # and alives.
        return [x for x in self.senders if x.credit]

    def __init__(self, remotes, channel, spool='/var/spool/aorta', buf=None,
        loglevel='INFO', use_sasl=True):
        """Initialize a new :class:`MessagePublisher` instance."""
        super(MessagePublisher, self).__init__(auto_settle=False)
        self.remotes = remotes
        self.use_sasl = use_sasl
        self.buf = buf or SpooledBuffer(spool=spool)
        self.loglevel = getattr(logging, loglevel)
        self.channel = channel
        self.senders = []
        self.must_stop = False
        self.injector = EventInjector()
        self.thread = threading.Thread(target=self.main_event_loop,
            daemon=True)

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        # Conigure the logger to send everything to stdout.
        self.logger = logging.getLogger()
        self.loghandler = logging.StreamHandler(sys.stdout)
        fmt = logging.Formatter(
            "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            datefmt="[%Y-%m-%d %H:%M:%S %z]")
        self.loghandler.setFormatter(fmt)
        self.logger.addHandler(self.loghandler)
        self.loghandler.setLevel(self.loglevel)
        self.logger.setLevel(self.loglevel)

    def signal_handler(self, signum, frame):
        """Invoked when the program receives an interrupt signal
        from the operating system.
        """
        if signum == signal.SIGHUP:
            pass
        if signum in (signal.SIGINT, signal.SIGTERM):
            self.stop()

    def stop(self):
        """Stops sending messages to the AMQP remote and exit the
        main event loop.
        """
        self.must_stop = True
        self.injector.trigger(ApplicationEvent('teardown'))

    def main_event_loop(self):
        """Ensure that the :class:`MessagePublisher` keeps
        receiving beats.
        """
        while True:
            if self.must_stop:
                break
            self.injector.trigger(ApplicationEvent('beat'))
            time.sleep(1/self.framerate)

    def on_start(self, event):
        self.container = event.container
        for addr in self.remotes:
            connection = None
            if not self.use_sasl:
                connection = event.container.connect(addr,
                    sasl_enabled=False)
            sender = event.container.create_sender(connection or addr,
                target=self.target)
            self.senders.append(sender)

        event.container.selectable(self.injector)
        self.thread.start()

    def on_beat(self, event):
        """Periodically invoked to check for new messages in the
        spool directory.
        """
        if not self.sendables:
            return

        # TODO: Distribute the messages more intelligently over
        # all AMQP peers.
        self.flush(random.choice(self.sendables))

    def on_teardown(self, event):
        """Close all links, connections and release all other
        resources.
        """
        # Wait for the beat thread to stop before closing the
        # EventInjector.
        self.thread.join()

        self.injector.close()
        for link in self.sendables:
            link.close()
        self.container.stop()

    def on_sendable(self, event):
        link = event.link
        peer = self.get_peer_address(link)
        self.logger.debug(
            "AMQP link sendable (target: %s, name: %s, host: %s, credit: %s)",
            link.target.address, link.name, self.get_peer_address(link),
            link.credit)
        self.flush(link=link)

    def on_accepted(self, event):
        self.logger.debug("Delivery %s accepted (host: %s)",
            event.delivery.tag, self.get_peer_address(event.link))

    def on_rejected(self, event):
        self.logger.debug("Delivery %s rejected (host: %s)",
            event.delivery.tag, self.get_peer_address(event.link))

    def on_released(self, event):
        self.logger.debug("Delivery %s released (host: %s)",
            event.delivery.tag, self.get_peer_address(event.link))

    def on_settled(self, event):
        self.buf.on_settled(delivery=event.delivery,
            remote_state=event.delivery.remote_state,
            disposition=event.delivery.remote)
        event.delivery.settle()
        self.logger.debug("Delivery %s settled (host: %s)",
            event.delivery.tag, self.get_peer_address(event.link))

    def flush(self, link, limit=100):
        # Ensure that we do not start sending messages if
        # we must stop.
        if self.must_stop:
            return

        for i in range(limit):
            if not link.credit:
                break
            host = self.container.get_connection_address(link.connection)
            tag = self.buf.transfer(host,
                source=link.source.address,
                target=link.target.address,
                sender=link, channel=self.channel)

    def get_peer_address(self, obj):
        """Return the remote AMQP address and port for the given
        :class:`proton.Link` or :class:`proton.Connection`.
        """
        if isinstance(obj, proton.Link):
            obj = obj.connection
        return self.container.get_connection_address(obj)


def main(argv):
    args = parser.parse_args(argv)
    handler = MessagePublisher(args.peers,
        channel=args.ingress_channel, spool=args.spool,
        loglevel=args.loglevel, use_sasl=not args.no_sasl)
    Container(handler).run()


if __name__ == '__main__':
    main(sys.argv[1:])
