"""Settings to override default settings."""

import logging

#
# Override settings
#
DEBUG = True

HTTP_PORT = 3333
HTTP_ADDRESS = '0.0.0.0'

#
# Set logging level
#
logging.getLogger().setLevel(logging.DEBUG)

JOB_CLASS_PACKAGES = ['app']
STATIC_DIR_PATH = './static'
TEMPLATE_DIR_PATH = './static'