"""
Experimentation driver loop
"""
from collections import OrderedDict

from ctoybox import Toybox, Input
from toybox.interventions import get_intervener, get_state_object
from toybox.interventions.core import Game, get_property, parse_property_access
from toybox.interventions.base import BaseMixin, Collection, SetEq

from copy import copy
from random import choice as sample
from tabulate import tabulate
from typing import List, Dict, Tuple, Any, Union

from .outcomes import Outcome, InadequateWindowError

try: 
  from ..agents.base import Agents, action_to_string, string_to_input
except:
  from agents.base import Agent, action_to_string, string_to_input

import logging
import math
import os


class MalformedInterventionError(Exception):
  
  def __init__(self, prop, diff):
    assert len(diff) > 0
    super().__init__('{} overrode keys: {}'.format(prop, ','.join([t[0] for t in diff])))
    self.diff = diff
    self.prop = prop


class ConditionalIntervention(Exception):

  def __init__(self, prop, diff):
    super().__init__('Intervention {} changed other keys: {}'.format(prop, ', '.join([t[0] for t in diff])))
    self.diff = diff
    self.prop = prop


class LikelyConstantError(Exception):

  def __init__(self, prop, value, trials):
    super().__init__('Property {} is likely a constant ({}, determined after {} trials)'.format(prop, value, trials))
    self.prop = prop
    self.value = value
    self.trials = trials


class Experiment(object):

  def __init__(self, 
    game_name,
    seed: int, 
    outcome_var: Outcome,
    trace: List[Tuple[Game, str]],
    agent: Agent,  
    timelag = 1,
    diff_trials = 30,
    discretization_cutoff = 10,
    outdir='exp'):
    # presumably the context was manually selected to be true?
    # think about/add this later
    self.agent  = agent
    self.game_name = game_name
    self.seed = seed
    self.interventions : Dict[str, List[Any]] = OrderedDict()
    self.outcome_state = trace[-1]
    self.trace = trace[:-1]
    self.timelag = -1 * abs(timelag)
    self.diff_trials = diff_trials
    self.discretization_cutoff = discretization_cutoff
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
      if k not in g.eq_keys: continue
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

  def generate_intervention(self) -> Tuple[Game, str, Any]:
    assert self.timelag < 0
    intervention_state : Game = self.trace[self.timelag][0]

    for prop, tried in self.interventions.items():
      before = get_property(intervention_state, prop)
      intervened_state = intervention_state.sample(prop)
      new_intervention = get_property(intervened_state, prop)

      if type(new_intervention) is float:
        if all([math.isclose(new_intervention, val) for val in tried]):
          continue
        elif new_intervention < min(tried) or new_intervention > max(tried):
          # allow samples from the tails
          # print('Setting {} to {} from {}'.format(prop, new_intervention, before))
          self.interventions[prop].append(new_intervention)
          return (intervened_state, prop, new_intervention)
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
            if new_intervention >= low and new_intervention <= high:
              elts = [v for v in tried if v >= low and v <= high]
              # print('{} values in bin [{}, {}]'.format(len(elts), low, high))
              # if len(elts):
              #   print('\tNot adding {}'.format(new_intervention))
              #   break
              # else:
              if len(elts) == 0:
                # print('\tSetting {} to {} from {}'.format(prop, new_intervention, before))
                self.interventions[prop].append(new_intervention)
                return (intervened_state, prop, new_intervention)
            low = high
            high = high + h
              
      elif new_intervention not in tried and new_intervention != before:
        self.interventions[prop].append(new_intervention)
        # print('Setting {} to {} from {}'.format(prop, new_intervention, before))
        return (intervened_state, prop, new_intervention)
    
    # Select a new mutation point
    prop = sample(list(self.mutation_points.difference(set(self.interventions.keys()))))
    before = get_property(intervention_state, prop)
    after = before
    counter = self.diff_trials
    
    while before == after and counter > 0:
      state = intervention_state.sample(prop)
      after = get_property(state, prop)
      if before != after: break
      counter -= 1

    if before == after: raise LikelyConstantError(prop, after, self.diff_trials)

    # print('Setting {} to {} from {}'.format(prop, after, before))
    
    if prop in self.interventions:
      self.interventions[prop].append(after)
    else:
      self.interventions[prop] = [after]
    return state, prop, after

  def forward_simulate(self, state: Game, action: Union[Input, int]) -> Game:
    # takes one step
    tb = state.intervention.toybox
    if type(action) is int:
      tb.apply_ale_action(action)
    elif isinstance(action, Input):
      tb.apply_action(action)
    else: assert False
    return state.__class__.decode(tb.state_to_json())    

  def check_unconditional(self, prop, s1: Game, s1_: Game, s2: Game, s2_: Game):    
    diff1: SetEq = s1 == s1_
    diff2: SetEq = s2 == s2_

    #print('check_unconditional: ', diff1, diff2)

    if len(diff2) < len(diff1): 
      raise MalformedInterventionError(prop, diff1.difference(diff2))
    
    elif len(diff2) > len(diff1):
      raise ConditionalIntervention(prop, diff2.difference(diff1))   

    return diff1, diff2


  def run(self):

    original_outcome = self.outcome_var.outcomep(self.trace + [self.outcome_state])

    while abs(self.timelag) < len(self.trace):
      print('\n\nLag between intervention and measured outcome: ', abs(self.timelag))    
      # For each time slice, randomly sample from the set of mutation points.
      # While the list of tried mutation points is less than the list of
      # possible mutation points...
      while len(self.interventions) < len(self.mutation_points):
        mutations_attempted = sum([len(tried) for tried in self.interventions.values()])
        if len(self.interventions) and ((mutations_attempted % 100) == 0):
          # print('\n\tInterventions attempted:\n\t=======================\n\tVariable\tCount\n\t----------------------' + \
          #   ''.join(['\n\t{}:\t{}'.format(k, len(v)) for k, v in self.interventions.items()]))
          # print('\t---------------------')
          print('{} possible mutation points; {} interventions attempted so far'.format(len(self.mutation_points), mutations_attempted))
          print(tabulate([(var, len(items)) for (var, items) in self.interventions.items()], 
            headers=['Property', 'Count']))
        t = self.timelag
        sapairs: List[Tuple[Game, str]] = [] # the window
        game         = get_state_object(self.game_name)
        intervention = get_intervener(self.game_name)(self.agent.toybox, 'breakout', eq_mode=SetEq)
        s1 = game.decode(intervention, self.get_intervention_state().encode(), game)

        try:
          s1_, prop, _ = self.generate_intervention()
          self.agent.toybox.write_state_json(s1_.encode())
        except LikelyConstantError as e:
          print('\t' + str(e))
          print('\tRemoving {} from mutation list'.format(e.prop))
          self.mutation_points.remove(e.prop)
          if e.prop in self.interventions: self.interventions.remove(e.prop)
          continue

        # print("\tLooping from t={} to 0 for {}".format(t, self.agent.__class__.__name__))
        self.agent.reset()

        while t < 0:
          self.agent.play(self.outdir + os.sep + 'intervened', 1, save_states=True)
          s2_ = game.decode(intervention,  self.agent.toybox.state_to_json(), game)
          with Toybox(self.game_name, seed=self.seed, withstate=s1.encode()) as tb:
            for i, action in enumerate(self.agent.actions):
              #if self.trace[len(self.trace) - (len(self.agent.actions))]
              # print('\t\tMirroring action', action_to_string(action))
              tb.apply_action(action)
            s2 = game.decode(intervention, tb.state_to_json(), game)
          #print('\t\tCheck mutated property', get_property(s2, prop), get_property(s2_, prop))
          try:
            same1, same2 = self.check_unconditional(prop, s1, s1_, s2, s2_)
          except MalformedInterventionError as e:
            print('\t\t'+str(e))
            print('\t\tRemoving {} from mutation list'.format(e.diff))
            for m in e.diff:
              if m[0] in self.mutation_points:
                self.mutation_points.remove(m[0])
              if m[0] in self.interventions:
                del self.interventions[m[0]]
          except ConditionalIntervention as e:
            print('\t\t'+str(e))
            print('\t\tRemoving {} from mutation list'.format(e.diff))
            for m in e.diff:
              if m[0] in self.interventions:
                del self.interventions[m[0]]
              if m[0] in self.mutation_points:
                self.mutation_points.remove(m[0])
          sapairs.append((s2_, self.agent.actions[-1]))
          t += 1
        # print('\tNumber of state-action pairs', len(sapairs))
        try:
          intervened_outcome = self.outcome_var.outcomep(sapairs)
          if intervened_outcome != original_outcome:
            print('Original and intervened outcome differ!')
            return s1_, intervened_outcome
          # print('Intervention had no effect on outcome')
        except InadequateWindowError as e:
          print(e)
          print('Resetting timelag to minimum window of {}'.format(e.expecting))
          self.timelag = -1 * e.expecting

      self.timelag = max(-1 * len(self.trace), self.timelag * 2)
      print('Doubling lookback to {}\n'.format(self.timelag))
      self.mutation_points = set(Experiment.generate_mutation_points(self.trace[0][0]))
