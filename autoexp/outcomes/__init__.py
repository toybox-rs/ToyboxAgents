from abc import ABC, abstractmethod
from toybox.interventions import Game
from typing import List, Tuple, Union

def sign(n):
  return -1 if n < 0 else 1 if n > 0 else 0

class OutcomeException(Exception): pass

class InadequateWindowError(OutcomeException):

    def __init__(self, got, expecting, outcome):
        self.got = got
        self.expecting = expecting
        self.outcome = outcome
        super().__init__('Need at least {} states to determine {}; got {}'.format(expecting, outcome, got))

    @staticmethod
    def check_window(pairs: List[Tuple[Game, str]], expecting: int, outcome: type):
        got = len(pairs)
        if got < expecting: raise InadequateWindowError(got, expecting, outcome.__name__)


class Outcome(ABC):

    def __init__(self, minwindow):
        self.minwindow = minwindow

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def outcomep(self, pairs: List[Tuple[Game, Union[str, int]]]) -> bool: pass

    def get_name(self): return self.__class__.__name__
