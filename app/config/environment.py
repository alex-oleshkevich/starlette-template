import enum


class Environment(enum.StrEnum):
    LOCAL = "local"
    PRODUCTION = "production"
    UNITTEST = "unittest"
