"""Check all packages and project files before the first launch."""
from pathlib import Path
import importlib.util
import os
from campusverse import data
from campusverse.energy_demo import load_energy_readings

root=Path(__file__).resolve().parent
problems=[]
for pkg in ['streamlit','plotly','pandas','PIL']:
    ok=importlib.util.find_spec(pkg) is not None
    print(('PASS' if ok else 'FAIL')+' package: '+pkg)
    if not ok:problems.append('Missing package '+pkg)
for fname in ['app.py','requirements.txt','campusverse/data.py','campusverse/visuals.py','assets/soe_front.jpg','assets/courtyard.jpg','campus_picker/index.html','data/synthetic_classroom_energy.csv']:
    present=(root/fname).is_file()
    print(('PASS' if present else 'FAIL')+' file: '+fname)
    if not present:problems.append('Missing '+fname)
if not problems:
    energy_rows=load_energy_readings(root/'data'/'synthetic_classroom_energy.csv')
    print('PASS synthetic energy rows:',len(energy_rows))
    data.initialize()
    print('PASS database: '+str(data.DB))
    print('PASS seeded sample rooms:',len(data.spaces()))
    print('PASS clickable 3D scene:',(root/'campus_picker'/'index.html').stat().st_size,'bytes')
    if not (root/'.streamlit'/'secrets.toml').exists():
        print('WARNING admin/security login not configured; run: py configure_demo.py')
else:
    print('SETUP INCOMPLETE: '+'; '.join(problems))
    raise SystemExit(1)
print('All mandatory checks passed.')
