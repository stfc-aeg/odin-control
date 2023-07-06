"""ODIN server main functions.

This module implements the main entry point for the ODIN server. It handles parsing
configuration options, loading adapters and creating the appropriate HTTP server instances.

Tim Nicholls, STFC Application Engineering Group
"""
import sys
import logging
import signal
import threading

import tornado.ioloop

from odin.http.server import HttpServer
from odin.config.parser import ConfigParser, ConfigError
from odin.logconfig import add_graylog_handler


def shutdown_handler():  # pragma: no cover
    """Handle interrupt signals gracefully and shutdown IOLoop."""
    logging.info('Interrupt signal received, shutting down')
    tornado.ioloop.IOLoop.instance().stop()


def main(argv=None):
    """Run the odin-control server.

    This function is the main entry point for the odin-control server. It parses configuration
    options from the command line and any files, resolves adapters and launches the main
    API server before entering the IO processing loop.

    :param argv: argument list to pass to parser if called programatically
    """
    config = ConfigParser()

    # Define configuration options and add to the configuration parser
    config.define('http_addr', default='0.0.0.0', option_help='Set HTTP server address')
    config.define('http_port', default=8888, option_help='Set HTTP server port')
    config.define('debug_mode', default=False, option_help='Enable tornado debug mode')
    config.define('access_logging', default=None, option_help="Set the tornado access log level",
                  metavar="debug|info|warning|error|none")
    config.define('static_path', default='./static', option_help='Set path for static file content')
    config.define('enable_cors', default=False,
                  option_help='Enable cross-origin resource sharing (CORS)')
    config.define('cors_origin', default='*', option_help='Specify allowed CORS origin')
    config.define('graylog_server', default=None, option_help="Graylog server address and :port")
    config.define('graylog_logging_level', default=logging.INFO, option_help="Graylog logging level")
    config.define('graylog_static_fields', default=None,
                  option_help="Comma separated list of key=value pairs to add to every log message metadata")

    # Parse configuration options and any configuration file specified
    try:
        config.parse(argv)
    except ConfigError as e:
        logging.error('Failed to parse configuration: %s', e)
        return 2

    if config.graylog_server is not None:
        add_graylog_handler(
            config.graylog_server,
            config.graylog_logging_level,
            config.graylog_static_fields
        )

    # Launch the HTTP server with the parsed configuration
    http_server = HttpServer(config)
    http_server.listen(config.http_port, config.http_addr)

    logging.info('HTTP server listening on %s:%s', config.http_addr, config.http_port)

    # Register a SIGINT signal handler only if this is the main thread
    if isinstance(threading.current_thread(), threading._MainThread):  # pragma: no cover
        signal.signal(signal.SIGINT, lambda signum, frame: shutdown_handler())

    # Enter IO processing loop
    tornado.ioloop.IOLoop.instance().start()

    # At shutdown, clean up the state of the loaded adapters
    http_server.cleanup_adapters()

    logging.info('ODIN server shutdown')

    return 0


def main_deprecate(argv=None):  # pragma: no cover
    """Deprecated main entry point for running the odin control server.

    This method adds an entry point for running odin control server that is run by the
    deprecated odin_server command. It simply runs the main entry point as normal having
    printing a deprecation warning.
    """
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('always', DeprecationWarning)
        message = """

The odin_server script entry point is deprecated and will be removed in future releases. Consider
using \'odin_control\' instead

            """
        warnings.warn(message, DeprecationWarning, stacklevel=1)

    main(argv)


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
