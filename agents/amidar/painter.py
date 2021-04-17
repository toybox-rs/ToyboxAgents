import random
from . import *
from numpy import all
from . utils import tile_to_route_id, index_segments


class Painter(AmidarAgent):

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # set up junction, segment index
    with amidar.AmidarIntervention(self.toybox) as intervention:
      segments, segment_junction_lookup, junction_segment_lookup, tilepoint_segment_lookup = segment_lookup(
        intervention)
      self.segments = segments
      self.segment_junction_lookup = segment_junction_lookup
      self.junction_segment_lookup = junction_segment_lookup
      self.tilepoint_segment_lookup = tilepoint_segment_lookup

    self.tile_heading = None

  def get_action_for_goal_tile(self, player_tp, next_tp, input):
    if
    pass

  @staticmethod
  def segment_painted(intervention, seg):
    # segment isn't supported in AmidarIntervention - segment is a construction abstracting over Tiles
    # could be moved to AmidarIntervention in the future
    # keeping this as static class method for now as static

    # check if all tiles painted on this segment
    t1 = seg[0]
    t2 = seg[1]
    if t1.tx == t2.tx:
      seg_tiles = [
        amidar.AmidarIntervention.tilepoint_to_tile(intervention, amidar.TilePoint(intervention, t1.tx, ty))
        for ty in range(t1.ty, t2.ty + 1)]
    else:
      seg_tiles = [
        amidar.AmidarIntervention.tilepoint_to_tile(intervention, amidar.TilePoint(intervention, tx, t1.ty))
        for tx in range(t1.tx, t2.tx + 1)]
    segment_painted = all([t.tag == amidar.Tile.Painted for t in seg_tiles])
    return segment_painted


  def get_action(self):
    input = Input()
    with amidar.AmidarIntervention(self.toybox) as intervention:
      game = intervention.game
      ptp = amidar.AmidarIntervention.worldpoint_to_tilepoint(intervention, game.player.position)
      ptile = intervention.player_tile()
      player_board_id = tile_to_route_id(intervention, ptp.tx, ptp.ty)
      seg = self.tilepoint_segment_lookup(ptp)
      junctions_for_seg = self.junction_segment_lookup(seg)  # this should be len 2
      segment_painted = self.segment_painted(intervention, seg)

      if player_board_id in game.board.junctions:
        # choose new junction to move toward
        adj_segments = [self.junction_segment_lookup[j] for j in junctions_for_seg]
        next_t =None
      elif segment_painted: # get to nearest unpainted junction
        # get adjacent tiles
        adj_tiles = [self.junction_segment_lookup[j] for j in junctions_for_seg]
        adj_walkable = intervention.get_adjacent_tiles(ptp, lambda t: t.tag != amidar.Tile.Empty)
        adj_unpainted = [t for t in adj_walkable if t.tag == amidar.Tile.Unpainted]
        if len(adj_unpainted):
          # if any unpainted, select at random
          next_t = random.choice(adj_unpainted)
        else:
          # otherwise, move in some walkable dir
          next_t = random.choice(adj_walkable)
        input = self.get_action_for_goal_tile()

      elif ptile.tag == amidar.Tile.Empty:  # this should never happen but just in case
        print("RANDOM ACTION")
        input = self.random_action()

      else: # otherwise
        # identify which junction on the tile to move toward in order to paint
        # select the junction that has not been visited
        h = game.player.history
        next_bid = random.choice([t for t in junctions_for_seg if t not in h])
        input = self.get_action_for_goal_tile(player_tid, next_t)



    return input