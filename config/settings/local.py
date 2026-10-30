from .base import *  # noqa: F403, F405

DEBUG = True

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

MIDDLEWARE = [  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]
