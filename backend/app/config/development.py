"""Development configuration."""

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    TESTING = False
