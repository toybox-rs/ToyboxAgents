# Outcomes may not be valid at every timestep.
import toybox.interventions.breakout as breakout
from typing import List, Tuple

def action_taken(actions : List[str], action_not_taken: str):
    # if the agent took the action, returns None for that time step (not appropriate for this query)
    # otherwise, return the action
    return [(a if a != action_not_taken else None) for a in actions]

def missed_ball(states: List[breakout.Breakout]):
    outcomes = [None]*len(states)
    outcomes[-1] = len(states[-1].balls) == 0
    return outcomes

