import toybox.interventions.amidar as ami
import numpy


def tile_to_route_id(intervention, tx, ty):
    return intervention.game.board.width*ty+tx

def tilepoint_lookup(intervention, target_tile_id):
    # target_tile_id == route_id
    ty = target_tile_id // intervention.game.board.width
    tx = target_tile_id - ty * intervention.game.board.width
    return ami.TilePoint(intervention, tx, ty)

def player_on_junction(intervention):
    # convert player position to tile storage id
    ptp = intervention.worldpoint_to_tilepoint(intervention.game.player.position)
    player_tid = tile_to_route_id(intervention, ptp.tx, ptp.ty)
    return player_tid in intervention.game.board.junctions

def index_junctions(intervention):
    # add junctions to set
    # we may discover them more than once iterating over boxes
    # annotate the junction tiles
    board = intervention.game.board
    box_junctions = set()
    for box in board.boxes:
        box_junctions.add((box.top_left.tx, box.top_left.ty))
        box_junctions.add((box.top_left.tx, box.bottom_right.ty))
        box_junctions.add((box.bottom_right.tx, box.top_left.ty))
        box_junctions.add((box.bottom_right.tx, box.bottom_right.ty))

    # now get a graph adjacency matrix from the tile annotation:
    junction_list = list(box_junctions)
    njunctions = len(junction_list)
    # sort the tile ids in box_junctions
    # tile_ids use top left as origin, use sort order (y,x)
    sorted_junction_tiles = sorted(junction_list,
                                   key=lambda x: (x[1], x[0]))
    # get the adjacency matrix for the sorted ids
    adj_mat = numpy.zeros((njunctions, njunctions), numpy.int8)
    # save id order index
    junction_id_to_tile = {}
    junction_tile_to_id = {}
    # first iterate over the horizontal neighbors
    for i, t in enumerate(sorted_junction_tiles):
        junction_id_to_tile[i] = t
        junction_tile_to_id[t] = i
        if i < njunctions - 1:
            if sorted_junction_tiles[i][1] == sorted_junction_tiles[i + 1][1]:
                adj_mat[i, i + 1] = 1
                adj_mat[i + 1, i] = 1

    # re-sort by (x,y)
    sorted_junction_tiles = sorted(junction_list,
                                   key=lambda x: (x[0], x[1]))
    # add vertical neighbors
    for i, t in enumerate(sorted_junction_tiles):
        if i < njunctions - 1:
            if sorted_junction_tiles[i][0] == sorted_junction_tiles[i + 1][0]:
                if abs(sorted_junction_tiles[i][1] - sorted_junction_tiles[i + 1][1]) < 7:
                    tile_id = junction_tile_to_id[t]
                    tile_adj = sorted_junction_tiles[i + 1]
                    tile_adj_id = junction_tile_to_id[tile_adj]
                    adj_mat[tile_id, tile_adj_id] = 1
                    adj_mat[tile_adj_id, tile_id] = 1

    return adj_mat, junction_tile_to_id, junction_id_to_tile

def index_segments(intervention, adj_mat, junction_id_to_tile):
    tile_to_segment_id = {}
    for tile in intervention.filter_tiles(lambda t: t.tag != ami.Tile.Empty):
        tp = intervention.tile_to_tilepoint(tile)
        rid = tile_to_route_id(intervention, tp.tx, tp.ty)
        tile_to_segment_id[rid] = set()
    nsegments = sum(sum(adj_mat))/2
    segments = []
    segment_id_to_tile_set = {}
    for seg in segments:
        segment_id_to_tile_set[seg] = set()
    # add all segment tiles to set
    for e1 in range(adj_mat.shape[0]): # for every self.adj_mat > 1
        for e2 in range(e1,adj_mat.shape[1]): # just loop over triangle
            if adj_mat[e1,e2]:                # adj_mat is symmetric
                segments.append((e1,e2))
                seg_id = len(segments)
                segtiles = set()

                tid_e1 = junction_id_to_tile[e1]
                tid_e2 = junction_id_to_tile[e2]
                if tid_e1[0] == tid_e2[0]:
                    emin = min(tid_e1[1], tid_e2[1])
                    emax = max(tid_e1[1], tid_e2[1])

                    for yy in range(emin, emax+1):
                        tp = ami.TilePoint(intervention, tx=tid_e1[0], ty=yy)
                        rid = tile_to_route_id(intervention, tp.tx, tp.ty)
                        segtiles.add(rid)
                elif tid_e1[1] == tid_e2[1]:
                    emin = min(tid_e1[0], tid_e2[0])
                    emax = max(tid_e1[0], tid_e2[0])

                    for xx in range(emin, emax+1):
                        tp = ami.TilePoint(intervention, tx=xx, ty=tid_e1[1])
                        rid = tile_to_route_id(intervention, tp.tx, tp.ty)
                        segtiles.add(rid)

                # add segment id to tile list
                for rid in segtiles:
                    tile_to_segment_id[rid].add(seg_id)
                segment_id_to_tile_set[seg_id] = segtiles
    for k in segment_id_to_tile_set.keys():
        segment_id_to_tile_set[k] = list(segment_id_to_tile_set[k])
    for k in tile_to_segment_id.keys():
        tile_to_segment_id[k] = list(tile_to_segment_id[k])
    return segments, tile_to_segment_id, segment_id_to_tile_set