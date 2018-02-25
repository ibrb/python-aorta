import glob
import logging

import yaml

from aorta.router.schema import RuleSchema
from aorta.router.exc import UnknownField
from aorta.router.exc import InvalidComparison


class Router(object):
    """Determines to which channels events are to be
    routed.
    """
    logger = logging.getLogger('aorta.router')
    schema = RuleSchema(many=True, strict=True)

    def __init__(self, rules=None, always_route=None, sink=None):
        self.rules = rules or []
        self.always_route = set(always_route or [])
        self.sink = sink
        self.config = []

    def load_config(self, path):
        """Loads a ruleset configuration from the given `path`."""
        self.logger.debug("Loading routes from %s", path)
        with open(path, 'r') as f:
            rules, _ = self.schema.load(yaml.safe_load(f.read()))
        self.rules.extend(rules)
        self.config.append(path)

    def glob_config(self, pattern):
        """Glob `pattern` to find ruleset configurations."""
        for path in glob.glob(pattern):
            self.load_config(path)

    def get_possible_routes(self):
        """Return a set containing all possible routes for the current
        configuration.
        """
        routes = set()
        for rule in self.rules:
            routes |= set(rule.destinations)

        if self.sink:
            routes.add(self.sink)

        if self.always_route:
            routes |= self.always_route

        return routes

    def route(self, dto):
        """Matches the event contained in the Data Transfer Object
        (DTO) and returns a tuple of destinations that it should
        be forwared to.
        """
        routes = set()
        exclude = set()
        for rule in self.rules:
            try:
                if not rule.match(dto):
                    continue

            # If an exception occurs, no further rules are
            # processed and the event is sent to the sink.
            except (InvalidComparison, UnknownField) as e:
                self.logger.critical(
                    "Invalid rule spec led to exception: %s",
                    repr(e)
                )
                routes = set()
                break
            except Exception as e:
                self.logger.exception("Fatal exception during event routing.")
                routes = set()
                break

            dest, excl = rule.get_destinations()
            routes |= set(dest)
            exclude |= excl

        # If matching was succesful, the event may also be forwarded
        # to the channels that were specified to always route to.
        if routes:
            routes |= self.always_route

        # Else, the event is sent to the sink.
        if not routes and self.sink:
            routes |= set([self.sink])

        return routes ^ exclude
