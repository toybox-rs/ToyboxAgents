# Autonomous Agents for Explanation using Toybox

## Getting started

ToyboxAgents depends on both the core [Toybox package](https://github.com/toybox-rs/toybox-rs) and the [intervention API](https://github.com/toybox-rs/Toybox/tree/master/toybox/interventions), found in the [Toybox testing repository](https://github.com/toybox-rs/Toybox). Toybox can be installed via pip; the intervention API must clone the testing repository and run `setup.py`. We recommend using a python virtual environment for managing dependencies:

```
python3 -m venv .env
source .env/bin/activate
pip install -r REQUIREMENTS.txt
git clone https://github.com/toybox-rs/Toybox
cd Toybox && python setup.py install
cd .. && rm -rf Toybox
```