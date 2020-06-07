import json
import os

from typing import List

from ctoybox import Toybox
from toybox.interventions import Game, get_state_object, get_intervener


def learn_models(datadir: str, modelmod:str, game: str) -> List[Game]:
  states : List[Game] = []
  with Toybox(game) as tb:
    for dd in datadir:
      for f in os.listdir(dd):
        if f.endswith('json'):
          with open(datadir + os.sep + f, 'r') as state:
            g : Game = get_state_object(game)
            states.append(g.decode(tb, json.load(state), g)) 
    
    intervener = get_intervener(game)
    with intervener(tb, modelmod=modelmod, data=states): pass # this should just make the model
    return states
