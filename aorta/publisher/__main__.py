#!/usr/bin/env python3
import argparse
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


class MessagePublisher(MessagingHandler):
    framerate = 10

    @property
    def sendables(self):
        # TODO: Also check if the links are actually established
        # and alives.
        return [x for x in self.senders if x.credit]

    def __init__(self, remotes, channel, spool='/var/spool/aorta', buf=None):
        super(MessagePublisher, self).__init__(auto_settle=False)
        self.remotes = remotes
        self.buf = buf or SpooledBuffer(spool=spool)
        self.channel = channel
        self.senders = []
        self.must_stop = False
        self.injector = EventInjector()
        self.thread = threading.Thread(target=self.main_event_loop,
            daemon=True)

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Invoked when the program receives an interrupt signal
        from the operating system.
        """
        if signum == signal.SIGHUP:
            pass
        if signum in (signal.SIGINT, signal.SIGTERM):
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
            sender = event.container.create_sender(addr)
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
        self.flush(link=event.link)

    def on_settled(self, event):
        self.buf.on_settled(delivery=event.delivery,
            remote_state=event.delivery.remote_state,
            disposition=event.delivery.remote)
        event.delivery.settle()

    def flush(self, link, limit=20):
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


def main(argv):
    args = parser.parse_args(argv)
    handler = MessagePublisher(args.peers,
        channel=args.ingress_channel, spool=args.spool)
    Container(handler).run()


if __name__ == '__main__':
    main(sys.argv[1:])
