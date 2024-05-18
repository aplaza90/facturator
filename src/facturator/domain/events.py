from dataclasses import dataclass


class Event:
    pass


@dataclass
class RepeatedPayer(Event):
    nif: str
