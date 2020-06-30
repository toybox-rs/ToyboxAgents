from toybox.interventions import Game
from typing import List

from toybox.interventions.core import distr

from .. import Var


import os


class Composite(Var):

  def __init__(self, name, modelmod):
    super().__init__(name, modelmod)
    self.atomicvars = []

  def make_models(self, modelmod, data: List[Game]):
    outdir = modelmod.replace('.', '/') + os.sep
    distr(outdir + self.name, [self.get(d) for d in data])
