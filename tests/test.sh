#!/bin/sh
set -u
TEST_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REWARD_FILE=${REWARD_FILE:-/logs/verifier/reward.txt}; mkdir -p "$(dirname "$REWARD_FILE")"; printf '0.000000\n' > "$REWARD_FILE"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
export PROGRAM_DIR=${PROGRAM_DIR:-/app}
python3 -m venv "$TMP/venv" || exit 1
"$TMP/venv/bin/python" -m pip install --no-index --find-links "$TEST_DIR/wheels" --require-hashes -r "$TEST_DIR/requirements-test.txt" || exit 1
set +e
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "$TMP/venv/bin/python" -m pytest -q "$TEST_DIR/test_beamline.py" --junitxml="$TMP/results.xml" >"$TMP/out" 2>"$TMP/err"; status=$?
set -e
python3 - "$TMP/results.xml" "$REWARD_FILE" <<'PY'
import math,sys,xml.etree.ElementTree as E
groups={'integrator':(.34,{'test_electric_acceleration_and_time','test_boris_positive_charge_bends_negative_y','test_reversing_charge_reverses_magnetic_deflection','test_pure_magnetic_speed_and_kinetic_energy_preserved'}),'aperture':(.28,{'test_loss_at_aperture_is_removed_and_recorded','test_loss_step_and_same_step_id_order','test_input_permutation_does_not_change_output'}),'diagnostics':(.14,{'test_final_diagnostics_use_only_survivors'}),'rejection':(.16,{'test_invalid_shape_missing_and_boolean_values_rejected','test_invalid_ranges_duplicates_and_nonfinite_rejected'}),'output':(.08,{'test_successful_output_is_atomic_and_has_complete_schema','test_atomic_replace_preserves_symlink_target','test_zero_steps_keeps_valid_particle_without_loss'})}
expected=set().union(*(v[1] for v in groups.values())); passed=set(); seen=[]
try:
 for c in E.parse(sys.argv[1]).getroot().findall('.//testcase'):
  n=c.attrib.get('name','');seen.append(n)
  if not any(c.find(x) is not None for x in ('failure','error','skipped')):passed.add(n)
 score=sum(w*len(ts&passed)/len(ts) for w,ts in groups.values()) if set(seen)==expected and len(seen)==len(expected) else 0.0
except Exception:score=0.0
with open(sys.argv[2],'w') as f:f.write(f'{score if math.isfinite(score) else 0.0:.6f}\n')
PY
cat "$TMP/out";cat "$TMP/err" >&2;exit "$status"
