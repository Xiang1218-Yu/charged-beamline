import argparse,json
from .core import simulate
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
with open(a.input) as f: data=json.load(f)
with open(a.output,'w') as f: json.dump(simulate(data),f)
