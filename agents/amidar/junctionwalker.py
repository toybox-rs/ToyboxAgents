import random
from . import *
from toybox import Input
from . utils import tilepoint_lookup, index_junctions, tile_to_route_id, index_segments

class JunctionWalker(AmidarAgent):

  def __init__(self, *args, **kwargs):
    self.seed = 1984  # party
    super().__init__(seed=self.seed, *args, **kwargs)
    self.heading_tilepoint = None  # amidar.TilePoint()
    # set up junction, segment index
    with amidar.AmidarIntervention(self.toybox) as intervention:
      # crawl the board to get  junction ids and adjacency
      adj_mat, junction_tile_to_id, junction_id_to_tile  = index_junctions(intervention)
      self.adj_mat = adj_mat
      self.junction_tile_to_id = junction_tile_to_id
      self.junction_id_to_tile = junction_id_to_tile
      # junction adjacency defines segments
      segments, tile_to_segment_id, segment_id_to_tile_set = index_segments(intervention, self.adj_mat, junction_id_to_tile)
      self.segments = segments
      self.tile_to_segment_id = tile_to_segment_id
      self.segment_id_to_tile_set = segment_id_to_tile_set
      # segments to junction indexing
      self.segment_junction_lookup = {}
      for segid in self.segment_id_to_tile_set.keys():
        self.segment_junction_lookup[segid] = set()
      for k in self.segment_id_to_tile_set.keys():
        segment_jn_tiles = [rid for rid in segment_id_to_tile_set[k] if rid in intervention.game.board.junctions]
        for j in segment_jn_tiles:
          self.segment_junction_lookup[k].add(j)
      for k in self.segment_junction_lookup.keys():
        self.segment_junction_lookup[k] = list(self.segment_junction_lookup[k])


  def get_new_heading(self, intervention, ptp, junctions_for_player_tile):
    cur_tile_key = (ptp.tx, ptp.ty)
    if cur_tile_key in self.junction_tile_to_id.keys(): # if tile is a junction
      cur_junction_id = self.junction_tile_to_id[cur_tile_key]
      # choose new junction
      new_jrids = self.lookup_junction_adjacency(intervention, cur_junction_id)
      # not in player history
      best_jrids = [jid for jid in new_jrids if jid not in intervention.game.player.history]
      if len(best_jrids):
        # go somewhere new if possible
        next_route_id = random.choice(best_jrids)
      else:
        next_route_id = random.choice(new_jrids)
    else:
      # try to finish this segment
      h = intervention.game.player.history
      # it won't appear in the history if needed to complete segment
      next_route_id = random.choice([t for t in junctions_for_player_tile if t not in h])
    next_tilepoint = tilepoint_lookup(intervention, next_route_id)
    heading_tilepoint = next_tilepoint
    return heading_tilepoint

  def lookup_junction_adjacency(self, intervention, current_junction_id):
    # return junction ids of adjacent junctions for current_junction_id
    ids = [i for i, x  in enumerate(self.adj_mat[current_junction_id]) if x > 0]
    # convert junction ids to route_ids
    junction_tilepoints = [self.junction_id_to_tile[x] for x in ids]
    rids = [tile_to_route_id(intervention, jt[0], jt[1]) for jt in junction_tilepoints]
    return rids

  def lookup_segment_junctions(self, tile_route_id):
    return self.segment_junction_lookup

  def lookup_tilepoint_junctions(self, tp, ):
    rid = tile_to_route_id(intervention, tp.tx, tp.ty)
    segment_ids = [s for s in self.segments if rid in self.segment_id_to_tile_set[s]]
    junctions = [j for j in self.junction_id_to_tile]
    return neighbor_junctions

  def get_action_for_heading_tile(self, player_tp: amidar.TilePoint, input):
    if player_tp.tx - self.heading_tilepoint.tx > 0:
      input.left = True # move left
    elif player_tp.tx - self.heading_tilepoint.tx < 0:
      input.right = True  # move right

    if player_tp.ty - self.heading_tilepoint.ty > 0:
      input.up = True
    elif player_tp.ty - self.heading_tilepoint.ty < 0:
      input.down = True

    return input

  def get_action(self):
    # select neighboring junction to move toward
    with amidar.AmidarIntervention(self.toybox) as intervention:
      game = intervention.game
      ptp = amidar.AmidarIntervention.worldpoint_to_tilepoint(intervention, game.player.position)
      if self.heading_tilepoint is None:
        rid = tile_to_route_id(intervention, ptp.tx, ptp.ty)
        seg = self.tile_to_segment_id[rid][0]
        junctions_for_player_tile = self.segment_junction_lookup[seg] # self.lookup_tilepoint_junctions(ptp)
        self.heading_tilepoint = tilepoint_lookup(intervention, random.choice(junctions_for_player_tile))
      elif self.heading_tilepoint == ptp:
        cur_tile_key = (ptp.tx, ptp.ty)
        cur_junction_id = self.junction_tile_to_id[cur_tile_key]
        junctions_for_player_tile = self.lookup_junction_adjacency(intervention, cur_junction_id)
        #print('on ptp, new options:', junctions_for_player_tile)
        self.heading_tilepoint = self.get_new_heading(intervention, ptp, junctions_for_player_tile)
        print(junctions_for_player_tile, tile_to_route_id(intervention, self.heading_tilepoint.tx, self.heading_tilepoint.ty), self.heading_tilepoint)
        #else:
        #  print("arrived at junction not equal to heading", self.heading_tilepoint, ptp)
        #  cur_junction_id = self.junction_tile_to_id[cur_tile_key]
        #  junctions_for_player_tile = self.lookup_junction_adjacency(cur_junction_id)
        #  self.heading_tilepoint = self.get_new_heading(intervention, ptp, junctions_for_player_tile)

      elif self.heading_tilepoint is not None:
        # check that we can reach the next tilepoint from current tile
        # now carry on to ptp
        pass
      else:  # this should never happen but just in case
        print("MAYDAY")
        rand_tile = amidar.AmidarIntervention.get_random_tile(intervention, lambda t: t.tag != amidar.Tile.Empty and
                                                                              t.tag != amidar.Tile.Painted)
        self.heading_tilepoint = amidar.AmidarIntervention.tile_to_tilepoint(intervention, rand_tile)

    pinput = Input()
    #print(self.heading_tilepoint, ptp)
    pinput = self.get_action_for_heading_tile(ptp, pinput)
    return pinput