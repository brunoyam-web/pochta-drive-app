from dataclasses import dataclass


@dataclass
class Config:
    PORT: int = 8000


class ConfigParser:
    __config: Config

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    @classmethod
    def getConfig(cls):
        if not cls.__config:
            cls.__config = Config()
        return cls.__config
