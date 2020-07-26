"""
Experimentation driver loop
"""
from collections import OrderedDict
from copy import copy
from random import choice as sample
from tabulate import tabulate
from typing import List, Dict, Tuple, Any, Union, Set

from ctoybox import Toybox, Input
from toybox.interventions import get_intervener, get_state_object
from toybox.interventions.core import Game, get_property, parse_property_access
from toybox.interventions.base import BaseMixin, Collection, SetEq


from .outcomes import Outcome, InadequateWindowError
from .vars import Var
from .vars.composite import Composite
from .vars.atomic import get_core_vars


try: 
  from ..agents.base import Agents, action_to_string, string_to_input
except:
  from agents.base import Agent, action_to_string, string_to_input

import ujson as json
import logging
import math
import os


class MalformedInterventionError(Exception):
  
  def __init__(self, prop, diff):
    assert len(diff) > 0
    super().__init__('\tWashed out; {} overrode keys: {}'.format(prop, ','.join([t[0] for t in diff if not t[0]==prop])))
    self.diff = diff
    self.prop = prop


class ConditionalIntervention(Exception):

  def __init__(self, prop, diff1, diff2):
    super().__init__('\tIntervention {} changed other keys: {}'.format(prop, ', '.join([t[0] for t in diff2 if not t[0] == prop])))
    self.to_remove = diff1
    self.changed = diff2
    self.prop = prop


class LikelyConstantError(Exception):

  def __init__(self, prop, value, trials):
    super().__init__('Property {} is likely a constant ({}, determined after {} trials)'.format(prop, value, trials))
    self.prop = prop
    self.value = value
    self.trials = trials


class Trace(object):

  def __init__(self, game_name: str, modelmod: str, seed: int, trace: List[Tuple[Game, str]]):
    self.game_name = game_name
    self.modelmod = modelmod
    self.seed = seed
    self.full = trace
    self.outcome_state = trace[-1][0]
    self._trace = trace[:-1]

  def __len__(self):
    return len(self.full)

  def __getitem__(self, i):
    return self.full[i]

  def get_state_trace(self) -> List[Game]:
    game = get_state_object(self.game_name)
    intervener = get_intervener(self.game_name)
    with Toybox(self.game_name, seed=self.seed) as tb:
      with intervener(tb, modelmod=self.modelmod, eq_mode=SetEq) as i:
        # make fresh objects
        return [game.decode(i, t[0].encode(), game) for t in self._trace]

  def get_trace(self) -> List[Tuple[Game, str]]:
    game = get_state_object(self.game_name)
    intervener = get_intervener(self.game_name)
    with Toybox(self.game_name, seed=self.seed) as tb:
      with intervener(tb, modelmod=self.modelmod, eq_mode=SetEq) as i:
        # make fresh objects
        return [(game.decode(i, t.encode(), game), a) for t, a in self._trace]

  def get_intervention_state(self, tb: Toybox, timelag: int) -> Game:
    """Returns a fresh copy of the intervention state."""
    game = get_state_object(self.game_name)
    intervener = get_intervener(self.game_name)(tb, modelmod=self.modelmod, eq_mode=SetEq)
    return game.decode(intervener, self.get_state_trace()[timelag].encode(), game)


class Experiment(object):

  def __init__(self, 
    game_name,
    seed: int, 
    modelmod: str, 
    outcome_var: Outcome,
    counterfactual: Outcome,
    trace: List[Tuple[Game, str]],
    agent: Agent,  
    # Now the optional inputs
    composite_vars: Set[Composite] = set(),
    # For learning marginals
    sample_data_dir = '',
    # An input slice that can potentially make learning faster
    data_range = slice(2000),
    atomic_constraints: Set[str] = set(), #regexes
    timelag = 1,
    diff_trials = 30,
    discretization_cutoff = 5,
    outdir='exp'):
    # presumably the context was manually selected to be true?
    # think about/add this later
    self.game_name = game_name
    self.seed = seed
    self.modelmod = modelmod

    self.outcome_var = outcome_var
    self.counterfactual = counterfactual

    self.trace = Trace(game_name, modelmod, seed, trace)
    self.agent = agent

    self.composite_vars = composite_vars
    self.atomic_constraints = atomic_constraints
    self.compute_distributions(sample_data_dir, data_range)

    self.timelag = -1 * max(abs(timelag), (outcome_var.minwindow + 1) * agent.action_repeat)
    self.diff_trials = diff_trials
    self.discretization_cutoff = discretization_cutoff
    self.outdir = outdir

    self.mutation_points = self.generate_mutation_points()
    self.interventions : Dict[Var, List[Any]] = OrderedDict()
    os.makedirs(outdir, exist_ok=True)

  def compute_distributions(self, sample_data_dir, data_range):
    data = []
    if not sample_data_dir: 
      try:
        import importlib
        importlib.import_module(self.modelmod)
        print('Using already-learned distributions in ', self.modelmod)
      except Exception as e: 
        print(e)
        print('Model module is either not accessible or path is wrong.')
      return 
    else:
      print('Learning distributions and saving in', self.modelmod.replace('.', os.sep))
      name = self.agent.__class__.__name__
      game = get_state_object(self.game_name)
      intervener = get_intervener(self.game_name)
      with Toybox(self.game_name) as tb:
        print('Loading data from', sample_data_dir)
        print('Creating module', self.modelmod)
        for seed in sorted(os.listdir(sample_data_dir)):
          if seed.startswith('.'): continue
          trial = sample_data_dir + os.sep + seed
          for f in sorted(os.listdir(trial))[data_range]:
            if f.endswith('json'):
              with open(trial + os.sep + f, 'r') as state:
                state = game.decode(intervener(tb, eq_mode=SetEq), json.load(state), game)
              data.append(state) 

        # compute distributions for core variables
        with intervener(tb, modelmod=self.modelmod, data=data): pass
    
    for var in self.composite_vars:
      var.make_models(self.modelmod, data)

  def get_intervention_state(self, tb: Toybox):
    return self.trace.get_intervention_state(tb, self.timelag)

  def generate_mutation_points(self) -> Set[Var]:
    # Doing it this way to get contravariance working for retval
    # If I set:
    # retval : Set[Var] = self.composite_vars
    # then mypy appears to immediately refine retval to Set[Composite]
    retval : List[Var] = []
    retval.extend(self.composite_vars)
    retval.extend(get_core_vars(self.trace.outcome_state, 
      modelmod=self.modelmod, 
      exclude=self.atomic_constraints,
      derived=self.composite_vars))
    assert len(retval), 'Must have more than zero mutation points to run an experiment!'
    return set(retval)

  def generate_intervention(self, tb: Toybox) -> Tuple[Game, Var, Any]:
    assert self.timelag < 0

    for var, tried in self.interventions.items():
      intervention_state : Game = self.get_intervention_state(tb)
      before, after = var.sample(intervention_state)

      if type(after) is float:
        if all([math.isclose(after, val) for val in tried]):
          continue
        elif after < min(tried) or after > max(tried):
          # allow samples from the tails
          print('Setting {} to {} from {} (extrema were [{}, {}]'.format(var, after, before, min(tried), max(tried)))
          self.interventions[var].append(after)
          return (intervention_state, var, after)
        elif len(tried) > self.discretization_cutoff:
          # h = (3.49 * sample_var) / (cube root n)
          n = len(tried)
          sample_mean = sum(tried) / n
          sample_var = sum([(x - sample_mean)**2 for x in tried]) / (n - 1)
          h = (3.49 * sample_var) / (n**(1/3))
          low = min(tried)
          high = h + low
          while low < max(tried):
            # goal is to find out whether we are in the appropriate bin
            # and whether there is already a sample in that bin.
            if after >= low and after <= high:
              elts = [v for v in tried if v >= low and v <= high]
              # print('{} values in bin [{}, {}]'.format(len(elts), low, high))
              # if len(elts):
              #   print('\tNot adding {}'.format(new_intervention))
              #   break
              # else:
              if len(elts) == 0:
                print('Setting {} to {} from {} (bucket size {}; extrema are [{}, {}])'.format(var, after, before, h, min(tried), max(tried)))
                self.interventions[var].append(after)
                return (intervention_state, var, after)
            low = high
            high = high + h
              
      elif after not in tried and after != before:
        self.interventions[var].append(after)
        print('Setting {} to {} from {}'.format(var, after, before))
        return (intervention_state, var, after)
    
    # Select a new mutation point
    prop : Var = sample(list(self.mutation_points.difference(set(self.interventions.keys()))))
    counter = self.diff_trials
    
    while counter > 0:
      intervention_state = self.get_intervention_state(tb)
      before, after = prop.sample(intervention_state)
      if before != after: 
        print('Setting {} to {} from {}'.format(prop, after, before))
        if prop in self.interventions:
          self.interventions[prop].append(after)
        else:
          self.interventions[prop] = [after]
        return intervention_state, prop, after
      counter -= 1
    
    raise LikelyConstantError(prop, after, self.diff_trials)


  def check_unconditional(self, prop, s1: Game, s1_: Game, s2: Game, s2_: Game):    
    diff1: SetEq = s1 == s1_
    diff2: SetEq = s2 == s2_


    if len(diff2) < len(diff1): 
      # print('Washed out Intervention\ndiff1:', diff1, '\tdiff2:', diff2)
      raise MalformedInterventionError(prop, diff1.difference(diff2))
    
    elif len(diff2) > len(diff1):
      # print('Conditional Intervention\ndiff1:', diff1, '\tdiff2:', diff2)
      raise ConditionalIntervention(prop, diff1.differs, diff2.difference(diff1))   

    # print('check_unconditional: ', diff1, diff2)

    return diff1, diff2


  def run_control(self, game, intervention, prop, after, control_state, record=False) -> List[Game]:

    if record:
      d = self.outdir + os.sep + 'control' + os.sep + str(prop) + os.sep + str(after)
      os.makedirs(d, exist_ok=True)
      f = d + os.sep + self.agent.__class__.__name__
    states = []

    with Toybox(self.game_name, seed=self.seed, withstate=control_state.encode()) as tb:
      if record:
        with open(f + '00001.json', 'w') as js:
          json.dump(tb.state_to_json(), js)
        tb.save_frame_image(f + '00001.png')

      for i, action in enumerate(self.agent.actions, start=2):
        if record:
          with open(f + str(i).zfill(5) + '.json' , 'w') as js:
            json.dump(tb.state_to_json(), js)
          tb.save_frame_image(f + str(i).zfill(5) + '.png')

        if isinstance(action, Input):
          tb.apply_action(action)
        elif type(action) == int:
          tb.apply_ale_action(action)
        elif action is None:
          pass
        else:
          raise ValueError('Unknown action type:', type(action))

        states.append(game.decode(intervention, tb.state_to_json(), game))
    return states


  def run(self):

    original_outcome = self.outcome_var.outcomep(self.trace.full)

    while abs(self.timelag) < len(self.trace):
      print('\nLag between intervention and measured outcome: ', abs(self.timelag))    

      while len(self.interventions) < len(self.mutation_points):
        mutations_attempted = sum([len(tried) for tried in self.interventions.values()])
        t = self.timelag
        sapairs: List[Tuple[Game, str]] = [] # the window

        game         = get_state_object(self.game_name)
        intervention = get_intervener(self.game_name)(self.agent.toybox, self.game_name, eq_mode=SetEq)
        s1           = game.decode(intervention, self.get_intervention_state(intervention.toybox).encode(), game)

        try:
          s1_, prop, after = self.generate_intervention(intervention.toybox)
          prop.set(after, s1_)
          assert s1 != s1_
          intervention_dir = self.outdir + os.sep + 'intervened' + os.sep + str(prop) + os.sep + str(after)
          self.agent.reset()  
          self.agent.toybox.write_state_json(s1_.encode())
          self.agent.play(intervention_dir, maxsteps=t, save_states=True, startstate=s1_)
          assert self.agent.states, (self.agent.toybox.game_over(), t, prop, self.agent.done if hasattr(self.agent, 'done') else None)
          assert self.agent.actions
          # print(len(self.agent.states), len(self.agent.actions))
          sapairs.extend(zip(self.agent.states, self.agent.actions))
          # This happens when an intervention causes a reset; skip it.
          if len(sapairs) < self.outcome_var.minwindow: continue
          # generate control
          control_states = self.run_control(game, intervention, prop, after, s1, record=True)
          s2 = self.agent.states[1]
          s2.intervention.eq_mode = SetEq
          s2_ = control_states[1]
          try:
            self.check_unconditional(prop, s1, s1_, s2, s2_)
          except ConditionalIntervention as err:
            print(err)
          except MalformedInterventionError as err:
            print(err)
            print('\tRemoving {} from mutation list'.format(e.prop))
            self.mutation_points.remove(e.prop)
            if e.prop in self.interventions: self.interventions.remove(e.prop)
          intervened_outcome = self.counterfactual.outcomep(sapairs)
          # s2_ = game.decode(intervention,  self.agent.states[-1].encode(), game)
          if intervened_outcome:
            print('Original and intervened outcome differ for property', prop)
            print(tabulate([(var, len(items)) for (var, items) in self.interventions.items()], headers=['Property', 'Count']))
            return s1_, intervened_outcome          

        except LikelyConstantError as e:
          print('\t' + str(e))
          print('\tRemoving {} from mutation list'.format(e.prop))
          self.mutation_points.remove(e.prop)
          if e.prop in self.interventions: self.interventions.remove(e.prop)


      print(tabulate([(var, len(items)) for (var, items) in self.interventions.items()], headers=['Property', 'Count']))
      self.timelag = max(-1 * len(self.trace), self.timelag * 2) # will pick the less negative one
      print('Doubling lookback to {}\n'.format(self.timelag))
      self.interventions = OrderedDict()
      self.mutation_points = self.generate_mutation_points()

    print('No counterfactual-inducing intervention found')
    return None, None