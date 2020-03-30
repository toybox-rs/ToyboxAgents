import os
import tarfile
import imageio
import ujson
from collections import defaultdict
from tqdm import tqdm

def load_data(archive, load_state=False, load_images=False):
    if not (load_data or load_state):
        raise ValueError('Need to load at least one of load_state or load_images')

    images = defaultdict(dict)
    states = defaultdict(dict)
    actions = defaultdict(dict)

    with tarfile.open(archive, 'r:gz') as tar:
        for f in tqdm(tar.getmembers()):
            if f.isfile():
                agent, seed, filename = f.name.split(os.sep)[-3:]
                extracted = tar.extractfile(f)

                if agent not in states:
                    agent_images = defaultdict(list)
                    agent_states = defaultdict(list)
                    images[agent] = agent_images
                    states[agent] = agent_states


                if filename.endswith('json'):
                    if load_state:
                        # JSON has 
                        states[agent][seed].append((f.name, ujson.load(extracted)))
                elif filename.endswith('png'):
                    if load_images:
                        images[agent][seed].append((f.name, imageio.read(extracted, format='png', pilmode='RGBA')))
                elif filename.endswith('act'):
                    if load_state:
                        a = [(str(i + 1).zfill(5), action) for (i, action) in enumerate(extracted.readlines())]
                        # There is one more frame than action
                        actions[agent][seed] = a + [(str(len(a) + 1).zfill(5), '')]
                else:
                    print('file type not recognized:', f.name) 
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
