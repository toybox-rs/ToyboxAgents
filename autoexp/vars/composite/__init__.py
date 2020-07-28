from toybox.interventions import Game
from typing import List, Any, Union

from toybox.interventions.core import distr

from toybox.interventions.breakout import query_hack

from .. import Var

import importlib
import os


class Composite(Var):

  def __init__(self, name, modelmod):
    super().__init__(name, modelmod)
    self.modelmod = modelmod
    self.atomicvars : List[Var] = []
    self.compositevars : List[Composite] = []

  def make_models(self, modelmod, data: List[Game]):
    outdir = modelmod.replace('.', '/') + os.sep
    distr(outdir + self.name, [self.get(d) for d in data])
    for v in self.compositevars:
      v.make_models(modelmod, data)

  def _sample_composite(self) -> Any:
    mod = importlib.import_module(self.modelmod + '.' + self.name)
    return mod.sample()

  def _sample_var(self, ivar_name) -> Any:
    ivar = importlib.import_module(self.modelmod + '.' + query_hack(ivar_name))
    return ivar.sample()

  def _get_atomic_from_composite(self) -> List[Var]:
    retval = [v for v in self.atomicvars]
    for v in self.compositevars:
      retval.extend(v._get_atomic_from_composite())
    return retval

  def _get_composite(self, name: Union[str, type]) -> Var:
    for var in self.compositevars:
      if name == var.name:
        return var      
    raise ValueError('No composite var named {} found in {}\'s composite vars.'.format(name, self.name))

  def _get_composite_dependencies(self) -> List[Var]:
    retval = [v for v in self.compositevars]
    for v in self.compositevars:
      retval.extend(v._get_composite_dependencies())
    return retval