"""
Experimentation driver loop
"""
from collections import OrderedDict

from ctoybox import Toybox, Input
from toybox.interventions import get_intervener, get_state_object
from toybox.interventions.core import Game, get_property
from toybox.interventions.base import BaseMixin, Collection, SetEq

from copy import copy
from random import choice as sample
from typing import List, Dict, Tuple, Any, Union

from .outcomes import Outcome

try: 
  from ..agents.base import Agents
except:
  from agents.base import Agent

import os


class MalformedInterventionError(Exception):
  
  def __init__(self, diff):
    super().__init__('Overridden keys: {}'.format(','.join(diff)))
    self.diff = diff


class ConditionalIntervention(Exception):

  def __init__(self, diff):
    super().__init__('Intervention changed other keys: {}'.format(','.join(diff)))
    self.diff = diff


class Experiment(object):

  def __init__(self, 
    game_name,
    seed: int, 
    outcome_var: Outcome,
    trace: List[Tuple[Game, str]],
    agentclass: type,  
    agentargs = [], 
    agentkwargs = {},  
    timelag = 1,
    outdir='exp'):
    # presumably the context was manually selected to be true?
    # think about/add this later
    self.mirror = agentclass(*agentargs, **agentkwargs)
    self.mirror.reset(seed=seed)
    self.agent  = agentclass(*agentargs, **agentkwargs)
    self.agent.reset(seed=seed)
    self.game_name = game_name
    self.seed = seed
    self.interventions : Dict[str, List[Any]] = OrderedDict()
    self.outcome_state = trace[-1]
    self.trace = trace[:-1]
    self.timelag = -1 * abs(timelag)
    self.mutation_points = set(Experiment.generate_mutation_points(self.trace[0][0]))
    self.outcome_var = outcome_var
    self.outdir = outdir
    os.makedirs(outdir, exist_ok=True)

  def get_intervention_state(self):
    return self.trace[self.timelag][0]

  def generate_mutation_points(g: BaseMixin, prefix='') -> List[str]:
    """Returns a flat list of all possible mutation points."""
    points : List[str] = []
    for k, v in vars(g).items():
      here = k if prefix == '' else '{0}.{1}'.format(prefix, k)
  
      if isinstance(v, Collection):
        for i, item in enumerate(v.coll):
          this_item = '{0}[{1}]'.format(here, i)
          if isinstance(item, BaseMixin):
            points.extend(Experiment.generate_mutation_points(item, prefix=this_item))
          else: points.append(this_item)
  
      elif isinstance(v, BaseMixin):
        points.extend(Experiment.generate_mutation_points(v, prefix=here))
  
      elif k in g.immutable_fields: continue
  
      else: points.append(here)
  
    return points

  def generate_intervention(self) -> Tuple[str, Any]:
    intervention_state : Game = self.trace[-1 * abs(self.timelag)][0]
    for prop, tried in self.interventions.items():
      new_intervention = eval('intervention_state.' + prop).sample()
      if new_intervention not in tried:
        self.interventions[prop].append(new_intervention)
        return (prop, new_intervention)
    
    # Select a new mutation point
    prop = sample(list(self.mutation_points.difference(set(self.interventions.keys()))))
    print('prop', prop)
    print('type of intervention_state', type(intervention_state))
    print(intervention_state.sample)
    print('type of intervention_state.intervention', type(intervention_state.intervention))
    state = intervention_state.sample(prop)
    value = get_property(state, prop)
    # print('Intervening on {} ...'.format(prop))
    # prop_obj = get_property(intervention_state, prop, get_container=True)
    # value = prop_obj.sample()
    print('Setting {} to {}'.format(prop, value))
    self.interventions[prop] = [value]
    return prop, value

  def forward_simulate(self, state: Game, action: Union[Input, int]) -> Game:
    # takes one step
    with Toybox(self.game_name, withstate=state.encode()) as tb:
      if type(action) is int:
        tb.apply_ale_action(action)
      elif isinstance(action, Input):
        tb.apply_action(action)
      else: assert False
      return state.__class__.decode(tb.state_to_json())    

  def check_unconditional(self, s1: Game, s1_: Game, s2: Game, s2_: Game):
    s1.intervention.eq_mode = SetEq
    s1_.intervention.eq_mode = SetEq
    s2.intervention.eq_mode = SetEq
    s2_.intervention.eq_mode = SetEq
    
    diff1: SetEq = s1 == s1_
    diff2: SetEq = s2 == s2_

    if len(diff2) < len(diff1): 
      raise MalformedInterventionError(diff2.difference(diff1))
    
    elif len(diff2) > len(diff1):
      raise ConditionalIntervention(diff2.difference(diff1))   

    return diff1, diff2


  def run(self):
    while self.timelag < len(self.trace):
      while len(self.interventions) < len(self.mutation_points):
        t = self.timelag
        key, val = self.generate_intervention()
        s1 = self.get_intervention_state()
        s1_ = copy(s1)
        get_property(s1_, key, setval=val)

        sapairs: List[Tuple[Game, str]] = []

        # TODO: make this take a list of tuples [(Breakout, str)]
        original_outcome = self.outcome_var.outcomep(self.trace + [self.outcome_state])

        print("looping from t={} to >0 for {}".format(t, self.agent.__class__.__name__))
        # t is initialized from self.time_lag; which is negative, therefore we count up to zero.
        while t <= 0:
          self.agent.play(self.outdir + os.sep + 'intervened' , 2, save_states=True)
          self.mirror.play(self.outdir + os.sep + 'control', 2, save_states=True)

          game = get_state_object(self.game_name)
          intervention = get_intervener(self.game_name)

          s2  = game.decode(intervention(self.mirror.toybox), self.mirror.toybox.state_to_json(), game)
          s2_ = game.decode(intervention(self.agent.toybox), self.agent.toybox.state_to_json(), game)

          diff1, diff2 = self.check_unconditional(s1, s1_, s2, s2_)

          print('diff1:', diff1)
          print('diff2:', diff2)
          print('agent action:\t', self.agent.actions[-1])
          print('mirror action:\t', self.mirror.actions[-1])

          sapairs.append((s2_, self.agent.actions[-1]))
          t += 1

        print('number of state-action pairs', len(sapairs))

        intervened_outcome = self.outcome_var.outcomep(sapairs)
        
        if intervened_outcome != original_outcome:
          print('original and intervened outcome differ')
          return s1_, intervened_outcome
      
      self.timelag = min(len(self.trace), self.timelag * 2)
