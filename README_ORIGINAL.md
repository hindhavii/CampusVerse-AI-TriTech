# 🏰 CampusVerse AI — DSU Smart Campus Digital Twin

An interactive DSU Harohalli **hackathon prototype**. The opening screen shows a reference-inspired, rotatable 3D campus. Select a building, then choose Campus Connect (public), Campus Control (staff) or Crowd Command (security). Uses the actual university tour screenshots supplied by the team for visual reference. All geometry is illustrative: the 3D model is **not an accurate surveyed replica of DSU**. Realistic façades are suggested through cream walls, columns, windows, entrance pediments, wings, formal courtyard, gardens and paths. Heights and coordinates are placeholders, especially for Hospital, AI Block and sports sites. 

**Critical safety warning:** Crowd values, sectors, entrances, routes and response tasks are a *simulation for demonstration*, not validated fire-safety or operational dispersal instructions. Each building reportedly uses one normal shared entry/exit, and any official emergency exits/egress capacities are unverified. The prototype does not claim to prevent stampedes or provide safe real-life instructions.

## Windows / VS Code — install EVERYTHING before you run

1. STOP the old Streamlit session: click the VS Code terminal and press **Ctrl+C**.
2. Download this ZIP, right-click it in Downloads, choose **Extract All**. Open the extracted **CampusVerse_AI_Final** folder with **VS Code → File → Open Folder** (open the folder containing `app.py`). This is a **new project folder**; don't merge random old files into it.
3. Click **Terminal → New Terminal**.
4. Paste the following commands, **one line at a time** (press Enter after each):

```powershell
py --version
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
py -m pip check
py verify_setup.py
py configure_demo.py
```

Save the printed local Administrator, Maintenance Worker and Security Staff passwords. They are also stored in `.streamlit/secrets.toml` on **your** computer only. That file is excluded from Git by `.gitignore`. Never publish or screenshot your passwords.

5. Once the complete verification passes, launch:

```powershell
py -m streamlit run app.py
```

6. Open `http://localhost:8501` if Chrome doesn't open itself.
7. If `py` is not recognized, replace **every** `py` above with `python` (e.g., `python -m pip install -r requirements.txt`). If the existing Python has dependency conflicts, tell ChatGPT the full terminal error. Do **not** install individual random packages; fix `requirements.txt` and rerun the full install.

## Judges' 4-minute demo

1. Rotate/zoom the 3D reference campus. Select **SOE** using its label (where supported) or the clear SOE button; navigate to **Campus Connect**. Check Classroom occupancy (occupied/unoccupied, number of students and density only). Show Cafeteria, Library, Lecture Hall and **Smart Parking** (free slots in alternative zones).
2. Submit **Report an Issue** such as a broken projector, and save its ticket ID. Open **Campus Control** and sign in using the demo admin password. In **Maintenance**, see the new report, choose priority, assign a team, set a deadline and move its state to In Progress / Resolved / Verified.
3. In **Waste**, create a cleaning task for a full bin. In **Electricity**, select a classroom and show AC, lights, fans and Other loads with the empty-room-waste alert. In **Simulator**, change a sensor, or load the College Fest what-if simulation. Return to Campus Connect and see changed simulated values.
4. Open **Crowd Command** using an admin or security password. For SOE choose the glass entrance and the interior blue-lit turnstile reference, set a hypothetical crowd count, partition into **four conceptual sectors**, create a staff alert with reported gate status, then acknowledge or escalate the incident. Explain how the system proposes **staggered normal dispersal** through the **shared** entrance/exit, NOT imaginary multiple exits.

## Features and decisions implemented

- **One 3D home screen**, building choices then exactly three modes. Building-specific detail screens; GF + Floors 1–5 for academic sample rooms. One example library, one cafeteria, one common room per academic block (their exact physical floors remain unverified); illustrative lecture halls on GF and floor 1.
- **Campus Connect:** classroom status/people/crowd indicator (no vacant classroom seats), cafeteria wait/seating, parking zone available/occupied/alternatives, library available seats, common/waiting area status, lecture halls, **Report an Issue**, public report tracking. No separate Laboratory Occupancy or Gate Display module.
- **Campus Control:** per-block waste bins, fill and cleaning tasks; per-room AC/lights/fans/other simulated kW readings, empty-room-waste inspection tickets; maintenance reports with priority, assigned team, editable deadline, stage and verification; plumbing/water issues merged here.
- **Crowd Command:** single shared everyday entry/exit assumption, glass doors and interior turnstile bottlenecks, conceptual 4-sector partitions, staff alert and response history, obstruction escalation, no invented emergency exits.
- **Campus Brain:** basic transparent *rules*, not actual Gemini API calls. Scenario simulator for fest mode.
- **Local SQLite persistence** for reports, room values, bins, incident status and workers. On free Streamlit Community Cloud, local files can reset on restart; use durable hosted DB for production.
- **Server-side role passwords:** generated locally on first-time setup; administrators can access both restricted modes, workers Campus Control, security Crowd Command. This is a hackathon prototype and not enterprise identity management.

## Publishing through GitHub and Streamlit Cloud

- Create a new **public** GitHub repository; upload the contents of **CampusVerse_AI_Final**, preserving folder paths (especially `campusverse/`, `assets/`, `.streamlit/config.toml`), but **NEVER** upload `.streamlit/secrets.toml` or `.data/`.
- Open https://share.streamlit.io, connect GitHub, select your repository and set **Main file path** to `app.py`.
- In Streamlit Cloud's **Advanced settings / Secrets**, add the three keys `ADMIN_PASSWORD`, `WORKER_PASSWORD`, `SECURITY_PASSWORD` and passwords **from your local config** (or choose new, strong values). Do not write passwords in public GitHub commits.
- Deploy, test public Campus Connect (no login), test admin/worker/security login and tasks, then copy the public `https://...streamlit.app` URL for submission.
- Actual hardware displays, sensors, real-time smartphone alerts, Gemini API and certified evacuation routing are NOT connected.

## Files

`app.py`: UI and navigation | `campusverse/data.py`: seeded local SQLite datasets and business logic | `campusverse/visuals.py`: Plotly 3D campus reference model | `configure_demo.py`: generate ignored demo login credentials | `verify_setup.py`: setup verification | `assets/`: real supplied tour screenshots | `.streamlit/config.toml`: theme.

## Known limitations

The 3D model is **architecturally inspired**, not photogrammetry, a measured 3D mesh or exact campus coordinates. The user's campus aerial reference is an architectural rendering, not a surveyed plan. Hospital and AI Block placement and the exact location of every room, library and cafeteria are unverified. The UI includes a native button for each building because not every combination of browser and Plotly supports selecting 3D points directly. Role passwords, SQLite and local state are demo-level components rather than production security/availability infrastructure.
