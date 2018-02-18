#!/usr/bin/env python3
import argparse
import os
import sys

from proton.handlers import MessagingHandler
from proton.reactor import Container

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
parser.add_argument('--ingress-channel', default='aorta.messages.ingress',
    help="the ingress message channel at the AMQP peer (default: %(default)s)")


class MessagePublisher(MessagingHandler):

    def __init__(self, remotes, channel, spool='/var/spool/aorta'):
        super(MessagePublisher, self).__init__(auto_settle=False)
        self.remotes = remotes
        self.buf = SpooledBuffer(spool=spool)
        self.channel = channel

    def on_start(self, event):
        self.container = event.container
        self.senders = []
        for addr in self.remotes:
            sender = event.container.create_sender(addr,
                name='test.ibrb.io')
            self.senders.append(sender)

    def on_sendable(self, event):
        self.flush(link=event.link)

    def on_settled(self, event):
        self.buf.on_settled(delivery=event.delivery,
            remote_state=event.delivery.remote_state,
            disposition=event.delivery.remote)
        event.delivery.settle()

    def flush(self, link):
        host = self.container.get_connection_address(link.connection)
        while link.credit:
            tag = self.buf.transfer(host,
                source=link.source.address,
                target=link.target.address,
                sender=link, channel=self.channel)
            if tag is None:
                break


def main(argv):
    args = parser.parse_args(argv)
    handler = MessagePublisher(args.peers,
        channel=args.ingress_channel, spool=args.spool)
    try:
        Container(handler, container_id='test.ibrb.io').run()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main(sys.argv[1:])
