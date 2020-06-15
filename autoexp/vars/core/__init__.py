from typing import List, Set, Union, Tuple, Any

from toybox.interventions.base import BaseMixin
from toybox.interventions.core import get_property, Game, Collection

from .. import Var
from ..derived import Derived

import re

class Core(Var):

  def get(self, g: Game):
    return get_property(g, self.name)

  @staticmethod
  def excludep(prop: str, pattern: str) -> bool:
    return bool(re.match(pattern, prop))
  
  def sample(self, state: Game) -> Tuple[Any, Game, Any]:
    before = get_property(state, self.name)
    intervened_state = state.sample(self.name)
    after = get_property(intervened_state, self.name)
    return before, intervened_state, after

def get_core_attributes(g: BaseMixin, prefix='') -> List[str]:
  """Returns a flat list of all possible mutation points."""
  points : List[str] = []
  for k, v in vars(g).items():
    if k not in g.eq_keys: continue
    here = k if prefix == '' else '{0}.{1}'.format(prefix, k)

    if isinstance(v, Collection):
      for i, item in enumerate(v.coll):
        this_item = '{0}[{1}]'.format(here, i)
        if isinstance(item, BaseMixin):
          points.extend(get_core_attributes(item, prefix=this_item))
        else: points.append(this_item)

    elif isinstance(v, BaseMixin):
      points.extend(get_core_attributes(v, prefix=here))

    elif k in g.immutable_fields: continue

    else: points.append(here)

  return points


def get_core_vars(g: BaseMixin, modelmod, exclude: Set[str] = set(), derived: Set[Derived] = set()) -> List[Core]:
  all_points : List[str] = get_core_attributes(g)
  assert len(all_points)
  # first filter out the attributes that contribute to the derived vars
  for d in derived: 
    for c in d.corevars:
      if c in all_points:
        all_points.remove(c)
  # now filter out anything we explicitly exclude
  retval = []
  for thing in all_points:
    doexclude = False
    for constraint in exclude:
      if Core.excludep(thing, constraint):
        doexclude = True; break
    if not doexclude:
      retval.append(Core(thing, modelmod))
  return retval