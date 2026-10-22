import argparse,json,os,sys,tempfile
from .core import InputError,simulate
def main():
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 try:
  with open(a.input,encoding='utf-8') as f:r=simulate(json.load(f))
  d=os.path.dirname(os.path.abspath(a.output));fd,t=tempfile.mkstemp(prefix='.beam-',dir=d,text=True)
  try:
   with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(r,f,sort_keys=True,separators=(',',':'));f.write('\n');f.flush();os.fsync(f.fileno())
   os.replace(t,a.output)
  finally:
   if os.path.exists(t):os.unlink(t)
  return 0
 except (InputError,ValueError,OSError,json.JSONDecodeError) as e: print('INPUT_ERROR: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
