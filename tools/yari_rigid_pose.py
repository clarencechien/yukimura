"""Projected two-link IK with constant lengths, explicit elbow branch and limits."""
import math
import numpy as np

def angle(v):return math.atan2(v[1],v[0])
def rotate(v,a):
    c,s=math.cos(a),math.sin(a)
    return np.array([c*v[0]-s*v[1],s*v[0]+c*v[1]])
def ease(t):return t*t*(3-2*t)
def track(frame,keys):
    for (a,x),(b,y) in zip(keys,keys[1:]):
        if a<=frame<=b:return x+(y-x)*ease((frame-a)/(b-a))
    return keys[0][1] if frame<keys[0][0] else keys[-1][1]

def solve_arm(shoulder,target,original):
    s0,e0,w0=(np.array(original[k],dtype=float) for k in ['shoulder','elbow','wrist'])
    l1,l2=np.linalg.norm(e0-s0),np.linalg.norm(w0-e0)
    ray=target-shoulder;distance=np.linalg.norm(ray)
    if not abs(l1-l2)+1e-6<distance<l1+l2-1e-6:
        raise ValueError('Target beyond fixed-length arm reach; change choreography, never stretch limbs.')
    u=ray/distance;v=np.array([-u[1],u[0]])
    projection=(l1*l1-l2*l2+distance*distance)/(2*distance)
    height=math.sqrt(max(0,l1*l1-projection*projection))
    # Preserve the original elbow branch, never choose independently per frame.
    original_ray=w0-s0
    sign=1 if np.cross(original_ray,e0-s0)>0 else -1
    elbow=shoulder+u*projection+v*height*sign
    upper_rotation=angle(elbow-shoulder)-angle(e0-s0)
    fore_rotation=angle(target-elbow)-angle(w0-e0)
    return elbow,upper_rotation,fore_rotation,l1,l2

def pose(frame,config):
    hip=np.array(config['hip'],float)
    if frame<=36:
        amount=track(frame,[(1,0),(11,-1),(15,1),(16,1),(25,.15),(36,0)])
        stroke=config['max_forward_source_px'] if amount>=0 else config['max_retract_source_px']
        translation=np.array([amount*stroke,-amount*stroke*.147])
        lean=math.radians(amount*config['torso_lean_degrees'])
    else:
        t=(frame-37)/35
        breath=math.sin(t*2*math.pi)
        lean=math.radians(.22*breath);translation=np.array([0,-.8*breath])
    transforms={'lower':(np.array([0.,0.]),0.),'torso':(hip,lean),'weapon':(translation,0.)}
    measures=[];joints={}
    for side,original in config['arms'].items():
        s0,e0,w0=(np.array(original[k],float) for k in ['shoulder','elbow','wrist'])
        shoulder=hip+rotate(s0-hip,lean);wrist=w0+translation
        elbow,upper,fore,l1,l2=solve_arm(shoulder,wrist,original)
        if abs(math.degrees(fore))>=config['wrist_change_limit_degrees']:
            raise ValueError(f'{side} wrist would exceed the configured angle limit; reduce the stroke.')
        transforms[side+'_upper']=(shoulder,upper)
        transforms[side+'_forearm']=(elbow,fore)
        transforms[side+'_hand']=(wrist,0.)
        measures.append({'side':side,'upper_length_error':abs(np.linalg.norm(elbow-shoulder)-l1),'forearm_length_error':abs(np.linalg.norm(wrist-elbow)-l2),'wrist_angle_change_degrees':math.degrees(fore),'reach_margin':l1+l2-np.linalg.norm(wrist-shoulder)})
        joints[side]=[shoulder.tolist(),elbow.tolist(),wrist.tolist()]
    return transforms,measures,joints
