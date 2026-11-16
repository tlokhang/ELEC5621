"""Free-base contact standing and head-response evaluation; no external support."""
import csv,json,math
from pathlib import Path
import mujoco
import numpy as np
from head_stabilization import ROOT,camera_gaze_yaw,wrap_angle
import matplotlib.pyplot as plt
OUT=ROOT/'results/full_body_balance'

def run(case,seed):
 m=mujoco.MjModel.from_xml_path(str(ROOT/'assets/microduck/scene_head_stabilization.xml'))
 d=mujoco.MjData(m);mujoco.mj_resetDataKeyframe(m,d,1);mujoco.mj_forward(m,d)
 joints=m.actuator_trnid[:,0];ids=m.jnt_dofadr[joints];qp=m.jnt_qposadr[joints];q=d.qpos[qp].copy();kp=m.actuator_gainprm[:,0]
 names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,int(j)) for j in joints]
 yaw=names.index('head_yaw');cam=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_CAMERA,'head_camera')
 initial=camera_gaze_yaw(d,cam);rng=np.random.default_rng(seed);target=math.radians(float(rng.choice([-1,1])*rng.uniform(10,20)));push=float(rng.uniform(-.2,.2))
 rows=[];failed=False;nonfoot=0;violations=0;peakforce=0
 for i in range(round(10/m.opt.timestep)):
  t=i*m.opt.timestep;R=d.xmat[1].reshape(3,3);pitch=np.arctan2(-R[2,0],R[2,2]);roll=np.arctan2(R[2,1],R[2,2])
  ref=q.copy();desired=initial+(target if t>=2 else 0)
  ref[yaw]+=target if t>=2 else 0
  if case=='balanced':
   ref[yaw]-=math.atan2(R[1,0],R[0,0])+2*wrap_angle(camera_gaze_yaw(d,cam)-desired)
   tau=d.qfrc_bias[ids]-.1*d.qvel[ids]
   for a,j in enumerate(joints):
    if 'ankle' in names[a]:tau[a]+=d.xaxis[j,1]*(pitch+.1*d.qvel[4])
    if 'hip_roll' in names[a]:tau[a]+=d.xaxis[j,0]*(-roll-.1*d.qvel[3])
   ref+=tau/kp
  # Position targets may exceed joint angles to request bounded torque; retain upstream ctrl/force limits.
  d.ctrl[:]=np.clip(ref,m.actuator_ctrlrange[:,0],m.actuator_ctrlrange[:,1])
  d.xfrc_applied[:]=0
  if 5<=t<5.1:d.xfrc_applied[1,0]=push
  mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
  for c in d.contact:
   if 0 in (int(m.geom_bodyid[c.geom1]),int(m.geom_bodyid[c.geom2])):
    other=int(m.geom_bodyid[c.geom2]) if int(m.geom_bodyid[c.geom1])==0 else int(m.geom_bodyid[c.geom1])
    if other not in (6,15):nonfoot+=1
  violations+=int(np.any(d.qpos[qp]<m.jnt_range[joints,0]-.01) or np.any(d.qpos[qp]>m.jnt_range[joints,1]+.01))
  peakforce=max(peakforce,float(np.max(np.abs(d.actuator_force))))
  rows.append(dict(time_s=(i+1)*m.opt.timestep,height_m=float(d.qpos[2]),pitch_deg=math.degrees(pitch),roll_deg=math.degrees(roll),gaze_error_deg=math.degrees(wrap_angle(camera_gaze_yaw(d,cam)-desired)),contacts=int(d.ncon),max_force_nm=float(np.max(np.abs(d.actuator_force)))))
  if not np.all(np.isfinite(d.qpos)) or d.qpos[2]<.075 or max(abs(pitch),abs(roll))>math.radians(20):failed=True;break
 errors=[r['gaze_error_deg'] for r in rows if r['time_s']>3]
 return rows,dict(seed=seed,target_deg=math.degrees(target),push_n=push,success=not failed and nonfoot==0 and violations==0,nonfoot_contact_samples=nonfoot,joint_violation_steps=violations,peak_actuator_force_nm=peakforce,elapsed_s=rows[-1]['time_s'],peak_tilt_deg=max(max(abs(r['pitch_deg']),abs(r['roll_deg'])) for r in rows),min_height_m=min(r['height_m'] for r in rows),gaze_rms_after_3s_deg=float(np.sqrt(np.mean(np.square(errors)))) if errors else None)

def main():
 OUT.mkdir(parents=True,exist_ok=True);results={}
 for case in ('baseline','balanced'):
  results[case]=[]
  for seed in range(12):
   rows,metrics=run(case,seed);results[case].append(metrics)
   if seed==0:
    with (OUT/f'{case}.csv').open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
   print(case,seed,metrics['success'],metrics['peak_tilt_deg'],flush=True)
 (OUT/'summary.json').write_text(json.dumps(dict(criteria='10 s, base height >=75 mm, abs roll/pitch <=20 deg; head cue 2 s, 0.1 s push at 5 s',model='Official free-base model; original force limits; no mocap or weld',mujoco_version=mujoco.__version__,trials=results),indent=2))
 fig,ax=plt.subplots(2,1,figsize=(8,5),sharex=True,constrained_layout=True)
 for case in results:
  a=np.genfromtxt(OUT/f'{case}.csv',delimiter=',',names=True)
  ax[0].plot(a['time_s'],a['pitch_deg'],label=case);ax[1].plot(a['time_s'],a['height_m'],label=case)
 ax[0].set_ylabel('Pitch (deg)');ax[1].set_ylabel('Base height (m)');ax[1].set_xlabel('Time (s)')
 for axis in ax:axis.legend();axis.grid(alpha=.2)
 fig.savefig(OUT/'comparison.png',dpi=150)
if __name__=='__main__':main()
