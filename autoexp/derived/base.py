from abc import ABC, abstractmethod
from toybox.interventions import Game
from typing import List, Tuple, Any

from ..outcomes.base import InadequateWindowError

def get_attribute_override(lst, fn, self, name, value):
  lst.add(name)
  return fn(self, name, value)

def derive(g, fn) -> List[str]:
  # override getattribute so we can track which ones 
  # are used
  old_getattribute = g.__getattribute__
  lst : List[str] = []
  g.__getattribute__ = lambda self, name, value: get_attribute_override(lst, old_getattribute, self, name, value)
  return lst


class Derived(ABC):

  @abstractmethod
  def sample(self, state: Game) -> Any: pass