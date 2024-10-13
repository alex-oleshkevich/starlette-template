import enum


class Environment(enum.StrEnum):
    LOCAL = "local"
    PROD = "production"
    UNITTEST = "unittest"
