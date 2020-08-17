"""
Experimentation driver loop
"""
from collections import OrderedDict
from copy import copy
from numpy.random import normal
from random import choice as sample
from random import randrange
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

import logging
import math
import os
import scipy
import ujson as json

class MalformedInterventionError(Exception):
  
  def __init__(self, prop, diff):
    assert len(diff) > 0
    super().__init__('\tWashed out; {} overridden'.format(prop))
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


class Result(object):

  def __init__(self):
    self.factual = None
    self.factual_start = None
    self.factual_end = None
    self.ffactual = None

    self.counterfactual = None
    self.counterfactual_start = None
    self.counterfactual_end = None
    self.fcounterfactual = None

    self.expl_var = None
    self.expl_val = None
    self.expl_ffactual = None
    self.expl_fcounterfactual = None
    
    # The timer for the whole process
    self.timer_start = None
    self.timer_end = None

    # The critical timestep (first opportunity for intervention)
    self.tc = None

    self.baselinereps = None

    self.oddsratio = None
    self.oddspvalue = None
    self.spurious = 0

  def __str__(self):
    return 'Factual: {} [{}, {}]'.format(self.factual, self.factual_start, self.factual_end) \
      + '\nCounterfactual: {} [{}, {}]'.format(self.counterfactual, self.counterfactual_start, self.counterfactual_end) \
      + '\nTc: {}'.format(self.factual_end + self.tc) \
      + '\nP(Yf| window, policy) = {}/{}'.format(self.ffactual, self.baselinereps) \
      + '\nP(Yc| window, policy) = {}/{}'.format(self.fcounterfactual, self.baselinereps) \
      + '\nInduced counterfactual with {} = {}'.format(self.expl_var, self.expl_val) \
      + '\nP(Yf | window, policy, do(X)) = {}/{}'.format(self.expl_ffactual, self.baselinereps) \
      + '\nP(Yc | window, policy, do(X)) = {}/{}'.format(self.expl_fcounterfactual, self.baselinereps) \
      + '\nOdds: {} (pvalue, fisher exact test: {})'.format(self.oddsratio, self.oddspvalue)

  def __del__(self):
    print(self)


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
    discretization_cutoff = 10,
    # The percentage of eligible mutation points that are detected as
    # spurious explanations before we determine that this time point 
    # is suceptible to random actions.
    spurious_cutoff = 0.1,
    outdir='exp',
    result=None):
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
    self.lookback = 1
    self.diff_trials = diff_trials
    self.discretization_cutoff = discretization_cutoff
    self.spurious_cutoff = spurious_cutoff
    self.outdir = outdir

    self.mutation_points = self.generate_mutation_points()
    self.interventions : Dict[Var, List[Any]] = OrderedDict()
    os.makedirs(outdir, exist_ok=True)

    self.result = result

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


  def in_critical_period(self):
    # let's see how bad it is to do this sequentially first
    actions = self.agent.toybox.get_legal_action_set()
    t = abs(self.timelag)
    s = self.trace.get_intervention_state(self.agent.toybox, self.timelag)
    factuals = 1
    counterfactuals = 0
  
    for action in actions:
      self.agent.reset()
      self.agent.toybox.write_state_json(s.encode())
      self.agent.toybox.apply_ale_action(action)
      self.agent.play('forward_simulate', maxsteps=t, save_states=True)
      sapairs = list(zip(self.agent.states, self.agent.actions))
      if self.outcome_var.outcomep(sapairs):
        factuals += 1
      if self.counterfactual.outcomep(sapairs):
        counterfactuals += 1
    
    print('factuals: {}\tcounterfactuals: {}'.format(factuals, counterfactuals))
    # It has to be possible to detect both/either of these at the given time point.
    return counterfactuals > 0 and factuals > 0

  def compute_frequency(self, outcome=None, start_state=None, steps=None, reps=100):
    """Computes the frequency of the outcome under the current policy from the input state for steps."""
    self.result.baselinereps = reps
    n = reps
    ct = 0
    while n > 0:
      self.agent.reset()
      self.agent.toybox.write_state_json(start_state.encode())
      self.agent.play('baseline_' + outcome.__class__.__name__, maxsteps=steps, save_states=True)
      sapairs = list(zip(self.agent.states, self.agent.actions))
      if outcome.outcomep(sapairs):
        ct += 1
      n -= 1
    return ct
    

  def run(self):

    original_outcome = self.outcome_var.outcomep(self.trace.full)

    while abs(self.timelag) < len(self.trace):
      print('\nLag between intervention and measured outcome: ', abs(self.timelag))    

      if not self.in_critical_period():
        #self.lookback = int(round(self.lookback + self.lookback * normal(0.0, 1.0)))
        #self.timelag = max(-1 * len(self.trace), self.timelag - self.lookback) # will pick the less negative one
        if abs(self.timelag) > len(self.trace):
          print('No time period in window size {} where a single action difference would change the outcome.'.format(len(self.trace)))
          exit(0)
        self.timelag -= 1
        print('Not yet in critical period; stepping back to', self.timelag)
        continue

      self.result.tc = self.timelag
      self.result.ffactual = self.compute_frequency(
          outcome     = self.outcome_var, 
          start_state = self.trace[self.timelag][0],
          steps       = abs(self.timelag),
          reps        = 100
        )
      self.result.fcounterfactual = self.compute_frequency(
          outcome     = self.counterfactual,
          start_state = self.trace[self.timelag][0],
          steps       = abs(self.timelag),
          reps        = 100
        )
      self.lookback = 1
        
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
          
          # If s2 is None, then the intervention failed immediately and this is a byproduct of the 
          # environment dynamics. Skip it.
          if s2 is None: continue

          s2.intervention.eq_mode = SetEq
          s2_ = control_states[1]
          try:
            self.check_unconditional(prop, s1, s1_, s2, s2_)
          except ConditionalIntervention as err:
            print(err)
          except MalformedInterventionError as err:
            print(err)
            print('\tRemoving {} from mutation list'.format(err.prop))
            self.mutation_points.remove(err.prop)
            if err.prop in self.interventions: del self.interventions[err.prop]
          counterfactual_outcome = self.counterfactual.outcomep(sapairs)
          factual_outcome = self.outcome_var.outcomep(sapairs)
          # s2_ = game.decode(intervention,  self.agent.states[-1].encode(), game)
          if counterfactual_outcome and not factual_outcome:
            print('Original and intervened outcome differ for property', prop)
            print(tabulate([(var, len(items)) for (var, items) in self.interventions.items()], headers=['Property', 'Count']))
            self.result.expl_var = prop
            self.result.expl_val = after 
            self.result.expl_ffactual = self.compute_frequency(
              outcome     = self.outcome_var,
              start_state = s1_,
              steps       = abs(self.timelag),
              reps        = 100
            )
            self.result.expl_fcounterfactual = self.compute_frequency(
              outcome     = self.counterfactual,
              start_state = s1_,
              steps       = abs(self.timelag),
              reps        = 100
            )
            odds_ratio, pvalue = scipy.stats.fisher_exact([
              [self.result.expl_ffactual,        self.result.ffactual],
              [self.result.expl_fcounterfactual, self.result.fcounterfactual]])
            print('odds ratio:', odds_ratio, 'pvalue', pvalue)
            # Using the traditional p-value of 0.05 because the point here is that
            # we can detect an effect that humans would think is sufficiently likely
            # and there is probably an argument to be made that we have all been trained
            # to treat p<0.05 as a significant value.
            if abs(odds_ratio - 1) > 0.1 and pvalue < 0.05:
              return s1_, counterfactual_outcome
            else: 
              print('Intervention did not significantly change the probability of the outcome.')
              self.result.spurious += 1
              if self.result.spurious > 2 and self.result.spurious > self.spurious_cutoff * len(self.mutation_points):
                print('Too many spurious explanations ({}); agent is likely acting randomly.'.format(self.result.spurious))

        except LikelyConstantError as e:
          print('\t' + str(e))
          print('\tRemoving {} from mutation list'.format(e.prop))
          self.mutation_points.remove(e.prop)
          if e.prop in self.interventions: self.interventions.remove(e.prop)


      print(tabulate([(var, len(items)) for (var, items) in self.interventions.items()], headers=['Property', 'Count']))
      self.timelag = max(-1 * (len(self.trace) -1), self.timelag + self.lookback * 2) # will pick the less negative one
      print('Doubling lookback to {}; (trace size is {})\n'.format(self.timelag, len(self.trace)))
      self.interventions = OrderedDict()
      self.mutation_points = self.generate_mutation_points()

    print('No counterfactual-inducing intervention found')
    return None, None