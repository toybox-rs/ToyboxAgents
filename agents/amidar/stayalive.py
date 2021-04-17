from . import *

class StayAlive(AmidarAgent):
    """The simplest agent. Moves in uniform random directions away from enemies."""

    def __init__(self, *args, **kwargs):
        self.heading = None
        self.goal = None
        self.thresh = 5
        super().__init__(*args, **kwargs)

    def get_action(self):
        input = Input()
        with amidar.AmidarIntervention(self.toybox) as intervention:
            enemy_dists = intervention.player_enemy_distances()

            if any([x < self.thresh for x in enemy_dists]):
                # then evade
                input = self.evade_action()
            elif self.goal is not None:
                # move towards goal
                input = self.goto(self.goal)
            elif not intervention.player_on_painted():
                # then paint unpainted current tile
                input = self.paint_action()
            else:
                # or choose new point to move toward
                # random new direction
                target_tile = intervention.get_random_tile(intervention.is_tile_walkable)
                self.goal = target_tile
                input = self.goto(intervention, self.goal)

        return input

    def goto(self, intervention, target_tile):
        # go to nearest junction in heading
        pass

    def evade_action(self, intervention):
        # move away from & out of enemy path
        self.goal = None # forget our earlier plans
        # get directions for current player tile
        ptp = intervention.player_tile(intervention)
        next_options = [intervention.get_tile_by_pos(ptp.tx-1, ptp.ty),
                        intervention.get_tile_by_pos(ptp.tx+1, ptp.ty),
                        intervention.get_tile_by_pos(ptp.tx, ptp.ty+1),
                        intervention.get_tile_by_pos(ptp.tx, ptp.ty)-1]
        next_options = [t for t in next_options if amidar.AmidarIntervention.is_tile_walkable(t.tag)]
        #dir = intervention.get_random_dir_for_tile(ptile)
        # choose direction that moves away from closest enemy & take corners around junctions
        e_dists = []
        pass

    def paint_action(self, intervention):
        # paint the current tile
        # get the
        pass

    def find_goal(self, intervention):
        # choose a new goal tile with simple heuristics
        # complete the box

        pass
