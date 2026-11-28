from .base import *  # noqa: F403, F405

MAILERS = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
        "OPTIONS": {
            "host": env("SMTP_HOST", default="localhost"),  # noqa: F405
            "port": env.int("SMTP_PORT", default=25),  # noqa: F405
            "username": env("SMTP_USERNAME", default=""),  # noqa: F405
            "password": env("SMTP_PASSWORD", default=""),  # noqa: F405
            "use_tls": env.bool("SMTP_USE_TLS", default=False),  # noqa: F405
            "use_ssl": env.bool("SMTP_USE_SSL", default=False),  # noqa: F405
        },
    },
}
