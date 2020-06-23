import json
import os

from typing import List, Tuple, Union

from ctoybox import Toybox, Input
from toybox.interventions import Game, get_state_object, get_intervener

from .outcomes import Outcome

def load_states(datadir: str, game:str) -> List[Game]:
  states : List[Game] = []
  with Toybox(game) as tb:
    for f in os.listdir(datadir):
      if f.endswith('json'):
        with open(datadir + os.sep + f, 'r') as state:
          g : Game = get_state_object(game)
          i = get_intervener(game)(tb, game)
          states.append(g.decode(i, json.load(state), g))
  return states  


def learn_models(states: List[Game], modelmod:str, game: str):
  intervener = get_intervener(game)
  with Toybox(game) as tb:  
    with intervener(tb, modelmod=modelmod, data=states): 
      pass # this should just make the model


def find_outcome_window(outcome: Outcome, states: List[Tuple[Game, Union[str, int, Input]]], window: int) -> List[Tuple[Game, Union[str, int, Input]]]:
  """Search over the input game states for the window that terminates in the outcome being true."""
  i = 0
  while i + outcome.minwindow <= len(states):
    dat = states[i:i+outcome.minwindow]
    if outcome.outcomep(dat):
      return states[max(0, i + outcome.minwindow - window):i+outcome.minwindow]
    i += 1
  return []
