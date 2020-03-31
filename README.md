# Autonomous Agents for Explanation using Toybox

## Getting started

ToyboxAgents depends on both the core [Toybox package](https://github.com/toybox-rs/toybox-rs) and the [intervention API](https://github.com/toybox-rs/Toybox/tree/master/toybox/interventions), found in the [Toybox testing repository](https://github.com/toybox-rs/Toybox). We recommend running with a virtual environment and installing via pip:

`pip -r REQUIREMENTS.txt`

## Generating data

Once you load up your virtual environment, you can see usage, e.g., via `python -m agents`, executed from the top-level directory. The [Tutorials](https://github.com/KDL-umass/ToyboxAgents/wiki/Tutorials) page in the wiki has detailed information on how to run things. Note that wiki pages can be downloaded for offline perusal.


## Troubleshooting

### ModuleNotFound error in notebook
If you are using the browser-based IDE, navigate to this directory and execute `jupyter notebook raw_data.ipynb`.

If you are using VS code, you will need to [set the notebook file root](https://stackoverflow.com/questions/55491046/how-to-set-the-running-file-path-of-jupyter-in-vscode/55500191#55500191). For VS Code version 1.43.1 on a Mac, this involved following the menu options:

Code > Preferences > Settings

and searching for "Notebook root". The first hit should be "Python > Data Science: Notebook File Root". Set this to be `${workspaceFolder}/analysis`.