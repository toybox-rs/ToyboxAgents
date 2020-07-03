from toybox.interventions import Game
from typing import List, Any

from toybox.interventions.core import distr

from toybox.interventions.breakout import query_hack

from .. import Var

import importlib
import os


class Composite(Var):

  def __init__(self, name, modelmod):
    super().__init__(name, modelmod)
    self.atomicvars = []

  def make_models(self, modelmod, data: List[Game]):
    outdir = modelmod.replace('.', '/') + os.sep
    distr(outdir + self.name, [self.get(d) for d in data])

  def _sample_composite(self) -> Any:
    mod = importlib.import_module(self.modelmod + '.' + self.name)
    return mod.sample()

  def _sample_var(self, ivar_name) -> Any:
    ivar = importlib.import_module(self.modelmod + '.' + query_hack(ivar_name))
    return ivar.sample()
