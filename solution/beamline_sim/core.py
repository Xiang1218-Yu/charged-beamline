import math
class InputError(ValueError): pass
def num(x,n):
 if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x): raise InputError(f'{n} must be finite')
 return float(x)
def vec(x,n):
 if not isinstance(x,list) or len(x)!=2: raise InputError(f'{n} must be a 2-element list')
 return num(x[0],n+'[0]'),num(x[1],n+'[1]')
def parse(r):
 if not isinstance(r,dict): raise InputError('request must be an object')
 ps=r.get('particles')
 if not isinstance(ps,list) or not ps: raise InputError('particles must be non-empty')
 e=vec(r.get('electric_field'),'electric_field'); B=num(r.get('magnetic_field'),'magnetic_field'); dt=num(r.get('dt'),'dt'); R=num(r.get('aperture_radius'),'aperture_radius'); st=r.get('steps')
 if dt<=0 or R<=0 or isinstance(st,bool) or not isinstance(st,int) or st<0: raise InputError('invalid dt, aperture_radius, or steps')
 out=[]; seen=set()
 for i,p in enumerate(ps):
  if not isinstance(p,dict): raise InputError('particle must be an object')
  ident=p.get('id'); m=num(p.get('mass'),f'particles[{i}].mass'); q=num(p.get('charge'),f'particles[{i}].charge'); x,y=vec(p.get('position'),f'particles[{i}].position'); vx,vy=vec(p.get('velocity'),f'particles[{i}].velocity')
  if not isinstance(ident,str) or not ident or ident in seen or m<=0 or q==0 or x*x+y*y>=R*R: raise InputError('invalid particle')
  seen.add(ident);out.append([ident,m,q,x,y,vx,vy])
 return out,e,B,dt,st,R
def simulate(r):
 ps,E,B,dt,steps,R=parse(r); losses=[]
 for step in range(1,steps+1):
  alive=[]; now=[]
  for ident,m,q,x,y,vx,vy in ps:
   h=q*dt/(2*m); vx+=h*E[0];vy+=h*E[1];t=h*B;s=2*t/(1+t*t); vpx=vx+vy*t;vpy=vy-vx*t;vx+=vpy*s;vy-=vpx*s;vx+=h*E[0];vy+=h*E[1];x+=vx*dt;y+=vy*dt
   (now if x*x+y*y>=R*R else alive).append((ident,m,q,x,y,vx,vy))
  losses.extend({'id':z[0],'step':step} for z in sorted(now));ps=alive
 ps.sort();losses.sort(key=lambda z:(z['step'],z['id']))
 parts=[{'id':i,'mass':m,'charge':q,'position':[x,y],'velocity':[vx,vy]} for i,m,q,x,y,vx,vy in ps]
 return {'status':'ok','time':steps*dt,'particles':parts,'losses':losses,'diagnostics':{'kinetic_energy':sum(.5*m*(vx*vx+vy*vy) for _,m,_,_,_,vx,vy in ps),'mechanical_momentum':[sum(m*vx for _,m,_,_,_,vx,vy in ps),sum(m*vy for _,m,_,_,_,vx,vy in ps)],'total_charge':sum(q for _,_,q,_,_,_,_ in ps),'survivor_count':len(ps)}}
