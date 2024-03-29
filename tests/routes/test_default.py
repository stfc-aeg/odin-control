"""
Test cases for oding.http.routes.default DefaultRoute class.

Tim Nicholls, STFC Application Engineering
"""
import logging
import re

import pytest

from odin.http.routes.default import DefaultRoute
from tests.utils import log_message_seen

class TestDefaultRoute():
    """Test DefaultRoute class."""

    def test_default_route_relative_path(self):
        """Test DefaultRoute resolves relative path for static content."""
        path = '.'
        def_route = DefaultRoute(path)
        #assert_regexp_matches(def_route.default_handler_args['path'], '.')
        assert path in def_route.default_handler_args['path']

    def test_default_route_absolute_path(self):
        """Test DefaultRoute treats absolute path for static content correctly."""
        path = '/absolute/path'
        def_route = DefaultRoute(path)
        assert path in def_route.default_handler_args['path']

    def test_default_route_bad_path(self, caplog):
        """Test DefaultRoute logs warning about bad path to static content."""
        path = '../missing_path'
        def_route = DefaultRoute(path)
        assert path in def_route.default_handler_args['path']

        assert log_message_seen(caplog, logging.WARNING,
            'Default handler static path does not exist')