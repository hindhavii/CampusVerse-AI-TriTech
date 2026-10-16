# 🏰 CampusVerse AI — Castle 3D + Original Dashboards

This is the MERGE of two **previously separate** project versions:

1. Original Streamlit dashboard from `CampusVerse_AI_Final.zip`, preserving Campus Connect, Campus Control, Crowd Command, the original database, report/task workflows and role-gated demo sign-in.
2. The newer Three.js DSU-inspired circular castle-at-dusk campus from the user-approved working 3D prototype. Clicking an actual model building selects the place and opens the ORIGINAL Streamlit three-choice menu. No invented floor cutaway.

The existing `requirements.txt` was **not changed** and no new third-party packages were added. `campusverse/visuals.py` is retained for backward compatibility but the homepage no longer uses the old Plotly 3D model.

## Windows / VS Code: run from the beginning

1. Right-click the ZIP -> **Extract All**.
2. In VS Code choose **File -> Open Folder** and pick `CampusVerse_AI_Castle_Merged` (folder containing `app.py`).
3. **Terminal -> New Terminal**.
4. Paste each command separately:

```powershell
py -m pip install -r requirements.txt
py verify_setup.py
py -m unittest discover -s tests -v
py configure_demo.py
py -m streamlit run app.py
```

`configure_demo.py` makes local demo passwords and prints them only on initial creation. Store them safely; they are excluded from Git. When reopening the app, the same passwords are retained. Three.js is loaded via CDN, so the 3D scene needs internet access. If no 3D renders, use the collapsed accessible fallback control underneath the scene.

## Demo walkthrough

1. Move the cursor across SOE and click the **actual 3D geometry** or its floating label. Camera focuses and sends the name to Streamlit.
2. The original **SOE -> Campus Connect | Campus Control | Crowd Command** hub appears.
3. **Campus Connect -> Classrooms** supports Ground Floor and Floors 1–5; Cafeteria, Library and Common Room occur only once per block. Submit a report and track its ticket ID.
4. **Campus Control** requires configured staff credentials. Its electricity section retains the original room-level equipment graph and now also displays the synthetic classroom/lecture-hall interval graph + AC energy per person-hour.
5. **Cricket Ground / DSU Arena / Parking** have facility-specific public choices rather than academic floors/classrooms.
6. Use **Back to building options**, then **3D Campus** to revisit the model.

## Dataset and classification

`data/synthetic_classroom_energy.csv` has 28 sample readings. It includes timestamp, building, room, duration hours, occupancy, fan status, light status, AC energy kWh, total interval energy kWh. AC energy/person-hour is recomputed at load as `AC kWh / (occupancy * hours)`, displayed as blank for zero/missing occupancy.

- Red: unoccupied **and** at least one fan/light ON.
- Green: occupied with electricity use **or** unoccupied with both fan/light OFF.
- Gray: missing occupancy/fan/light reading, or ambiguous state not qualifying for the others.

All values are demo readings, **not real-time DSU sensor measurements**. This is not verified campus geometry and does not provide evacuation guidance. The illustration in `assets/approved_visual_target_CONCEPT_ONLY.png` is a look reference, not a rendered 3D asset.

## Technical details and limitations

- `app.py`: original 3 systems, with only homepage integration, location-choice filtering, and energy view addition.
- `campus_picker/index.html`: newer Three.js canvas and Mesh raycasting; a lightweight Streamlit custom-component message sends the selected building to Python without extra Python dependencies.
- `campusverse/data.py`: original persistent SQLite; adds small outdoor-event demo rows using `INSERT OR IGNORE` for existing databases.
- `campusverse/energy_demo.py`: energy data loader/classification; Python standard library only.
- `assets/`: original DSU reference images and a separate approved visual concept.

**Limitations:** Demo passwords use the original Streamlit secrets and role logic, not production-grade individual accounts. Existing worker ticket authorizations and crowd operations are hackathon prototype mechanisms. Persistent SQLite works locally; a deployed app needs a persistent hosted datastore if the hosting platform has ephemeral storage. WebGL/Streamlit interaction should be tested on the user's actual laptop/browser; CI-style syntax and unit checks do not replace a real browser test.
