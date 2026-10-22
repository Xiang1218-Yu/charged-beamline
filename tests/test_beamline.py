import json, math, os, pathlib, subprocess, sys, tempfile
PROGRAM_DIR = pathlib.Path(os.environ.get('PROGRAM_DIR', '/app'))
def particle(i,m=1,q=1,p=(0,0),v=(0,0)): return {'id':i,'mass':m,'charge':q,'position':list(p),'velocity':list(v)}
def req(ps, **kw):
 d={'particles':ps,'electric_field':[0.,0.],'magnetic_field':0.,'dt':.1,'steps':1,'aperture_radius':10.};d.update(kw);return d
def run(data, old=None):
 with tempfile.TemporaryDirectory() as td:
  inp=pathlib.Path(td)/'input.json'; out=pathlib.Path(td)/'result.json'; inp.write_text(json.dumps(data),encoding='utf-8')
  if old is not None: out.write_bytes(old)
  env=os.environ.copy();env['PYTHONPATH']=str(PROGRAM_DIR)
  p=subprocess.run([sys.executable,'-m','beamline_sim','--input',str(inp),'--output',str(out)],cwd=PROGRAM_DIR,env=env,text=True,capture_output=True)
  return p, (json.loads(out.read_text()) if p.returncode==0 else None), (out.read_bytes() if out.exists() else None), list(pathlib.Path(td).glob('.beam-*'))
def byid(d,i): return next(x for x in d['particles'] if x['id']==i)
def test_electric_acceleration_and_time():
 """R1：无磁场时，电场的双半步推进应给出正确速度、位置与时间。"""
 p,d,_,_=run(req([particle('p',m=2,q=3)],electric_field=[4,0],dt=.5,steps=2));x=byid(d,'p');assert p.returncode==0 and d['time']==1.0;assert math.isclose(x['velocity'][0],6);assert math.isclose(x['position'][0],4.5)
def test_boris_positive_charge_bends_negative_y():
 """R1：正电荷在正垂直磁场中从 +x 速度应朝 -y 偏转。"""
 p,d,_,_=run(req([particle('p',v=(1,0))],magnetic_field=2,dt=.1));x=byid(d,'p');assert p.returncode==0 and x['velocity'][1]<0 and x['position'][1]<0
def test_reversing_charge_reverses_magnetic_deflection():
 """R1：反转电荷应反转磁偏转方向。"""
 _,a,_,_=run(req([particle('a',q=1,v=(1,0))],magnetic_field=2));_,b,_,_=run(req([particle('b',q=-1,v=(1,0))],magnetic_field=2));assert byid(a,'a')['velocity'][1]*byid(b,'b')['velocity'][1]<0
def test_pure_magnetic_speed_and_kinetic_energy_preserved():
 """R1/R3：纯磁场不会改变单粒子的速度大小和动能。"""
 p,d,_,_=run(req([particle('p',m=2,v=(3,4))],magnetic_field=7,steps=20,dt=.03));x=byid(d,'p');assert p.returncode==0;assert math.isclose(sum(v*v for v in x['velocity']),25,rel_tol=1e-12);assert math.isclose(d['diagnostics']['kinetic_energy'],25,rel_tol=1e-12)
def test_loss_at_aperture_is_removed_and_recorded():
 """R2：位置达到孔径边界的粒子须在该步吸收并记录。"""
 p,d,_,_=run(req([particle('p',p=(.9,0),v=(1,0))],dt=.1,aperture_radius=1));assert p.returncode==0 and d['particles']==[] and d['losses']==[{'id':'p','step':1}]
def test_loss_step_and_same_step_id_order():
 """R2：损失步号正确，且同一步记录按粒子 ID 确定排序。"""
 ps=[particle('z',p=(.95,0),v=(1,0)),particle('a',p=(0,.95),v=(0,1)),particle('keep',p=(0,0))]
 p,d,_,_=run(req(ps,dt=.1,aperture_radius=1));assert p.returncode==0 and d['losses']==[{'id':'a','step':1},{'id':'z','step':1}] and [x['id'] for x in d['particles']]==['keep']
def test_input_permutation_does_not_change_output():
 """R2/R5：同一初态的输入排列不得改变输出字节语义。"""
 ps=[particle('b',p=(.1,0),v=(.2,0)),particle('a',p=(0,.1),v=(0,.2))]
 _,x,_,_=run(req(ps,steps=3));_,y,_,_=run(req(list(reversed(ps)),steps=3));assert x==y and [p['id'] for p in x['particles']]==['a','b']
def test_final_diagnostics_use_only_survivors():
 """R3：最终诊断只统计存活粒子的能量、机械动量、电荷和数量。"""
 ps=[particle('gone',m=3,q=-2,p=(.95,0),v=(1,0)),particle('live',m=2,q=4,v=(3,4))]
 p,d,_,_=run(req(ps,dt=.1,aperture_radius=1));z=d['diagnostics'];assert p.returncode==0 and z['survivor_count']==1 and z['total_charge']==4 and z['mechanical_momentum']==[6.0,8.0] and z['kinetic_energy']==25.0
def test_invalid_shape_missing_and_boolean_values_rejected():
 """R4：结构错误、缺失字段和布尔伪数值必须拒收且不覆盖旧输出。"""
 cases=[{},req([particle('p')],dt=True),req([particle('p')],electric_field=[0]),req([particle('p')],steps=False)]
 for x in cases:
  p,_,raw,tmp=run(x,b'old');assert p.returncode!=0 and p.stderr.startswith('INPUT_ERROR:') and raw==b'old' and not tmp
def test_invalid_ranges_duplicates_and_nonfinite_rejected():
 """R4：非法范围、重复 ID、非有限数与孔径外初态必须拒收。"""
 cases=[req([particle('p')],aperture_radius=0),req([particle('p'),particle('p')]),req([particle('p',p=(10,0))]),req([particle('p',v=(float('nan'),0))])]
 for x in cases:
  p,_,raw,tmp=run(x,b'guard');assert p.returncode!=0 and raw==b'guard' and not tmp
def test_successful_output_is_atomic_and_has_complete_schema():
 """R5：成功输出需是完整稳定 JSON，且同目录不遗留临时文件。"""
 p,d,raw,tmp=run(req([particle('p')],steps=0));assert p.returncode==0 and raw.endswith(b'\n') and not tmp;assert set(d)=={'status','time','particles','losses','diagnostics'};assert set(d['diagnostics'])=={'kinetic_energy','mechanical_momentum','total_charge','survivor_count'}
def test_atomic_replace_preserves_symlink_target():
 """R5：成功写入必须替换输出路径，不能沿符号链接改写既有目标。"""
 with tempfile.TemporaryDirectory() as td:
  base=pathlib.Path(td); inp=base/'input.json'; target=base/'sentinel.bin'; out=base/'result.json'
  inp.write_text(json.dumps(req([particle('p')],steps=0)),encoding='utf-8');target.write_bytes(b'preexisting-target-bytes');out.symlink_to(target)
  env=os.environ.copy();env['PYTHONPATH']=str(PROGRAM_DIR)
  p=subprocess.run([sys.executable,'-m','beamline_sim','--input',str(inp),'--output',str(out)],cwd=PROGRAM_DIR,env=env,text=True,capture_output=True)
  assert p.returncode==0 and not out.is_symlink() and target.read_bytes()==b'preexisting-target-bytes'

def test_zero_steps_keeps_valid_particle_without_loss():
 """R1/R2：零步数合法且不推进、不吸收粒子。"""
 p,d,_,_=run(req([particle('p',p=(.5,0),v=(2,3))],steps=0,aperture_radius=1));assert p.returncode==0 and d['time']==0 and d['losses']==[] and byid(d,'p')['position']==[.5,0]
