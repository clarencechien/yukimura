"""Regression checks for projected reach, contact and choreography constraints."""
import copy
import json
import unittest
from pathlib import Path
import numpy as np
from yari_rigid_pose import pose, rotate, solve_arm

CONFIG=json.loads((Path(__file__).resolve().parents[1]/'assets/source/jigoku-2d/yari-rigid/rig.json').read_text())

class PoseChecks(unittest.TestCase):
    def test_constant_lengths_and_foot_contacts(self):
        for frame in range(1,73):
            transforms,_,joints=pose(frame,CONFIG)
            for side,leg in CONFIG['legs'].items():
                points=np.array(joints[side+'_leg'])
                source=np.array([leg[k] for k in ['hip','knee','ankle']],float)
                np.testing.assert_allclose(np.linalg.norm(np.diff(points,axis=0),axis=1),np.linalg.norm(np.diff(source,axis=0),axis=1),atol=1e-8)
                toe,angle=transforms[side+'_foot']
                np.testing.assert_allclose(toe,leg['toe'],atol=1e-8)
                ankle=toe+rotate(np.array(leg['ankle'])-np.array(leg['toe']),angle)
                np.testing.assert_allclose(ankle,points[-1],atol=1e-8)
                if side=='front':self.assertEqual(angle,0.)
                else:self.assertLessEqual(ankle[1],leg['ankle'][1]+1e-8)

    def test_closed_loops_and_real_lower_body_motion(self):
        for first,last in [(1,36),(37,72)]:
            a,_,_=pose(first,CONFIG);b,_,_=pose(last,CONFIG)
            for name in a:
                np.testing.assert_allclose(a[name][0],b[name][0],atol=1e-8)
                self.assertAlmostEqual(a[name][1],b[name][1])
        a,_,_=pose(1,CONFIG);b,_,_=pose(15,CONFIG)
        self.assertGreater(np.linalg.norm(a['pelvis'][0]-b['pelvis'][0]),20)
        for side in CONFIG['legs']:
            self.assertGreater(abs(b[side+'_shin'][1]-a[side+'_shin'][1]),.1)

    def test_pelvis_drive_precedes_weapon_extension(self):
        first,_,_=pose(1,CONFIG);drive,_,_=pose(13,CONFIG);contact,_,_=pose(15,CONFIG)
        np.testing.assert_allclose(drive['pelvis'][0],contact['pelvis'][0])
        self.assertLess(drive['weapon'][0][0],contact['weapon'][0][0])
        self.assertGreater(contact['pelvis'][0][0],first['pelvis'][0][0])

    def test_unreachable_target_rejected_instead_of_stretching(self):
        for side,leg in CONFIG['legs'].items():
            original=dict(zip(['shoulder','elbow','wrist'],[leg['hip'],leg['knee'],leg['ankle']]))
            with self.assertRaises(ValueError):solve_arm(np.array(leg['hip']),np.array(leg['ankle'])+[1000,0],original)
        bad=copy.deepcopy(CONFIG);bad['max_forward_source_px']=1000
        with self.assertRaises(ValueError):pose(15,bad)

    def test_configured_knee_limit_is_enforced(self):
        bad=copy.deepcopy(CONFIG);bad['knee_change_limit_degrees']=1
        with self.assertRaises(ValueError):pose(15,bad)

if __name__=='__main__':unittest.main()
