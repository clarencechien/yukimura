"""Transfer a head fit between two exports of the same TRELLIS generation.

Each export is normalized by its own bounding box (height 2, centred in x/y, feet at z=0).
p_target = (p_source / s_source + c_source - c_target) * s_target, applied to scale + translation.
"""
import argparse, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--fit', required=True, help='head-fit.json measured on the source export')
p.add_argument('--source-report', required=True, help='refinement-report.json (normalization) of the source export')
p.add_argument('--target-report', required=True, help='refinement-report.json (normalization) of the target export')
p.add_argument('--output', required=True)
a = p.parse_args()
fit = json.loads(Path(a.fit).read_text())
def frame(report):
    n = json.loads(Path(report).read_text())['normalization']; lo, hi = n['original_low'], n['original_high']
    return n['scale'], [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]]
ss, cs = frame(a.source_report); st, ct = frame(a.target_report)
ratio = st / ss
fit['transferred_from'] = {'fit': a.fit, 'scale': fit['scale'], 'translation': fit['translation'], 'source_report': a.source_report, 'target_report': a.target_report}
fit['scale'] = fit['scale'] * ratio
fit['translation'] = [(fit['translation'][i] / ss + cs[i] - ct[i]) * st for i in range(3)]
Path(a.output).write_text(json.dumps(fit, indent=2) + '\n'); print(json.dumps({'scale': fit['scale'], 'translation': fit['translation']}))
