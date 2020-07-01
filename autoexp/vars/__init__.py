from abc import ABC, abstractmethod
from typing import Any

from toybox.interventions import Game

class Var(ABC): 

  def __init__(self, name, modelmod):
    self.name = name
    self.modelmod = modelmod

  def __str__(self):
    return self.name

  def __repr__(self):
    return self.name

  def __hash__(self):
    return hash(self.name)

  @abstractmethod
  def get(self, state: Game) -> Any: pass

  @abstractmethod
  def sample(self, g:Game) -> Any: pass

