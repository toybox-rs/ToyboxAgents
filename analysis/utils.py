import os
import tarfile
import zipfile
import imageio
try:
    import ujson
except:
    import json as ujson
from collections import defaultdict
from tqdm import tqdm
import typing

def load_data(archive, load_state=False, load_images=False):
    if not (load_data or load_state):
        raise ValueError('Need to load at least one of load_state or load_images')

    images = defaultdict(dict)
    states = defaultdict(dict)
    actions = defaultdict(dict)

    if archive.endswith('zip'):
        open_archive = lambda filename: zipfile.ZipFile(archive, 'r')
        getmembers = lambda zfile: zfile.infolist()
        isdir = lambda zinfo: zinfo.is_dir()
        class Readable(object):
            def __init__(self, zfile, zinfo):
                self.zfile = zfile
                self.zinfo = zinfo
            def read(self):
                return self.zfile.read(self.zinfo)
            def readlines(self):
                lines = []
                with self.zfile.open(self.zinfo) as f:
                    for line in f:
                        lines.append(line)
                return lines
        extractfile = lambda zfile, zinfo: Readable(zfile, zinfo)
        getfilename = lambda zinfo: zinfo.filename
    elif archive.endswith('gz'):
        open_archive = lambda filename: tarfile.open(filename, 'r:gz')
        getmembers = lambda tfile: tfile.getmembers()
        isdir = lambda tinfo: not tinfo.isfile()
        extractfile = lambda tfile, tinfo: tfile.extractfile(tinfo)
        getfilename = lambda tinfo: tinfo.name
    else:
        raise ValueError('unknown archive: %s' % archive)


    with open_archive(archive) as tar:
        for f in tqdm(getmembers(tar)):
            if isdir(f): continue

            agent, seed, filename = getfilename(f).split(os.sep)[-3:]
            extracted = extractfile(tar, f)

            if agent not in states:
                agent_images = defaultdict(list)
                agent_states = defaultdict(list)
                images[agent] = agent_images
                states[agent] = agent_states
            if filename.endswith('json'):
                if load_state:
                    # JSON has 
                    states[agent][seed].append((filename, ujson.load(extracted)))
            elif filename.endswith('png'):
                if load_images:
                    images[agent][seed].append((filename, imageio.read(extracted, format='png', pilmode='RGBA')))
            elif filename.endswith('act'):
                if load_state:
                    a = [(str(i + 1).zfill(5), action) for (i, action) in enumerate(extracted.readlines())]
                    # There is one more frame than action
                    actions[agent][seed] = a + [(str(len(a) + 1).zfill(5), '')]
            else:
                print('file type not recognized:', getfilename(f)) 
    if load_state:
        for agent, seeddict in states.items():
            for seed in seeddict:
                msg1 = 'No actions recorded for agent %s' % agent
                msg2 = 'No actions recorded for agent %s with seed %s' % (agent, seed)
                assert agent in actions, msg1
                assert seed in actions[agent], msg2
                assert len(actions[agent]), msg2
    return {'images': images, 'states': states, 'actions': actions}

def make_videos(images):
    for agent, seeddict in images.items():
        for seed, imagelist in seeddict.items():
            filename = '{0}_{1}.mp4'.format(agent, seed)
            with imageio.get_writer(filename, fps=24) as writer:
                for (_, image) in tqdm(sorted(imagelist, key=lambda t: t[0])):
                    im = image.get_next_data()
                    writer.append_data(im)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    args = parser.parse_args()

    dat = load_data(args.file, load_images=True)
    make_videos(dat['images'])
