"""Local persistent *simulated* data for the CampusVerse AI hackathon prototype.

No DSU sensor, room, parking-slot, flow-capacity or safety information is asserted here.
The dataset uses invented example values and room numbers for demonstration only.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
DB = PROJECT / '.data' / 'campusverse.sqlite3'
BUILDINGS = ['SOE', 'CDSIMER', 'Hospital', 'AI Block', 'Sports Facilities', 'Open Auditorium', 'Cricket Ground', 'DSU Arena', 'Parking']
ACADEMIC = ['SOE', 'CDSIMER', 'AI Block']
FLOORS = list(range(6))  # Ground floor + 1 through 5. Exact DSU assignments are unverified.
CATEGORY_NAMES = {'classroom':'Classrooms','cafeteria':'Cafeteria','parking':'Parking','library':'Library','common':'Common room','waiting':'Waiting area','lecture':'Lecture halls','lab':'Laboratories'}


def now():
    return datetime.now().isoformat(timespec='seconds')


@contextmanager
def connect():
    """Close SQLite connections even after errors (important on Windows)."""
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB), timeout=15)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=8000')
        with conn:
            yield conn
    finally:
        conn.close()


def initialize():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS spaces (
          id TEXT PRIMARY KEY, building TEXT NOT NULL, floor INTEGER,
          category TEXT NOT NULL, label TEXT NOT NULL,
          capacity INTEGER NOT NULL, occupied INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS bins (
          id TEXT PRIMARY KEY, building TEXT NOT NULL, location TEXT NOT NULL,
          fill INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS parking (
          id TEXT PRIMARY KEY, label TEXT NOT NULL, capacity INTEGER NOT NULL,
          occupied INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS energy (
          space_id TEXT PRIMARY KEY, ac REAL NOT NULL, lights REAL NOT NULL,
          fans REAL NOT NULL, other REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS tickets (
          id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL,
          building TEXT NOT NULL, location TEXT NOT NULL, category TEXT NOT NULL,
          description TEXT NOT NULL, priority TEXT NOT NULL DEFAULT 'Medium',
          assigned_to TEXT NOT NULL DEFAULT 'Unassigned',
          deadline TEXT, status TEXT NOT NULL DEFAULT 'Submitted',
          created_at TEXT NOT NULL, resolved_at TEXT);
        CREATE TABLE IF NOT EXISTS crowd_events (
          id INTEGER PRIMARY KEY AUTOINCREMENT, building TEXT NOT NULL,
          location TEXT NOT NULL, count INTEGER NOT NULL,
          shared_gate_status TEXT NOT NULL, action TEXT NOT NULL,
          staff TEXT NOT NULL DEFAULT 'Unassigned',
          status TEXT NOT NULL DEFAULT 'New', created_at TEXT NOT NULL);
        ''')
        # Add new outdoor venue demo records even when upgrading an existing DB.
        c.executemany('INSERT OR IGNORE INTO spaces VALUES (?,?,?,?,?,?,?)',[
            ('ARENA_EVENT','DSU Arena',-1,'event','Arena event gathering area',650,210),
            ('CRICKET_EVENT','Cricket Ground',-1,'event','Cricket spectator area',900,320),
            ('SPORT_EVENT','Sports Facilities',-1,'event','Sports facility gathering',180,65),
            ('OPEN_EVENT','Open Auditorium',-1,'event','Open auditorium gathering',500,180),
        ])
        c.executemany('INSERT OR IGNORE INTO bins VALUES (?,?,?,?)',[
            ('ARENA_B1','DSU Arena','Event entrance vicinity',78),
            ('CRICKET_B1','Cricket Ground','Spectator access area',87),
            ('PARKING_B1','Parking','Outdoor parking area',63),
        ])
        if c.execute('SELECT COUNT(*) FROM spaces').fetchone()[0] > 4:
            return
        spaces=[]
        for block in ACADEMIC:
            code={'SOE':'S','CDSIMER':'M','AI Block':'AI'}[block]
            # Sample IDs, not mapped to confirmed real classrooms/floors.
            for floor in FLOORS:
                for n in [1,2]:
                    number=f'{floor}{n:02d}'
                    spaces.append((f'{code}_C_{number}',block,floor,'classroom',f'Classroom {number}',60,(0 if floor%2==0 and n==1 else 29+3*n+floor)))
                if floor in (0,1):
                    spaces.append((f'{code}_LH_{floor}',block,floor,'lecture',f'Lecture Hall {floor+1}',190,135 if floor==0 else 0))
            # -1: facility floor not verified, so do not invent location.
            spaces.extend([(f'{code}_LIB',block,-1,'library','Block Library',160,91),
                           (f'{code}_CAFE',block,-1,'cafeteria','Block Cafeteria',125,78),
                           (f'{code}_COMMON',block,-1,'common','Block Common Room',76,40),
                           (f'{code}_WAIT',block,-1,'waiting','Waiting Area',58,18)])
        spaces.extend([
            ('H_WAIT','Hospital',-1,'waiting','Hospital Waiting Area',150,105),
            ('SPORT_COURT','Sports Facilities',-1,'common','Sports Gathering Area',160,56),
            ('OPEN_AUD','Open Auditorium',-1,'lecture','Open Auditorium',500,180),
        ])
        c.executemany('INSERT INTO spaces VALUES (?,?,?,?,?,?,?)',spaces)
        bins=[]
        for block in ACADEMIC+['Hospital','Sports Facilities','Open Auditorium']:
            code=block.replace(' ','_').upper()
            for i,(name,fill) in enumerate([('Entrance',36),('Common Area',82),('Cafeteria vicinity',93)],1):
                # Simulated positions. Not an assertion of physical bin placements.
                bins.append((f'{code}_B{i}',block,name,fill))
        c.executemany('INSERT INTO bins VALUES (?,?,?,?)',bins)
        c.executemany('INSERT INTO parking VALUES (?,?,?,?)',[
            ('P1','Parking Zone A (illustrative)',60,53),
            ('P2','Parking Zone B (illustrative)',48,28),
            ('P3','Parking Zone C (illustrative)',52,51)])
        energy=[]
        for rid,block,fl,cat,label,cap,occ in spaces:
            if cat in ('classroom','lecture'):
                ac=3.2 if cat=='classroom' else 5.0
                energy.append((rid,ac,0.48,0.36,0.22))
        c.executemany('INSERT INTO energy VALUES (?,?,?,?,?)',energy)


def query(sql,params=()):
    with connect() as c:
        return [dict(r) for r in c.execute(sql,params).fetchall()]


def execute(sql,params=()):
    with connect() as c:
        cur=c.execute(sql,params)
        return cur.lastrowid


def spaces(building=None,category=None,floor=None):
    clauses=[];params=[]
    for col,val in [('building',building),('category',category),('floor',floor)]:
        if val is not None:
            clauses.append(f'{col}=?');params.append(val)
    where=(' WHERE '+' AND '.join(clauses)) if clauses else ''
    return query('SELECT * FROM spaces'+where+' ORDER BY floor, category, label',params)


def update_occupancy(space_id,occupied):
    execute('UPDATE spaces SET occupied=MIN(capacity,MAX(0,?)) WHERE id=?',(int(occupied),space_id))


def bins(building):
    return query('SELECT * FROM bins WHERE building=? ORDER BY id',(building,))


def update_bin(bin_id,fill):
    execute('UPDATE bins SET fill=MIN(100,MAX(0,?)) WHERE id=?',(int(fill),bin_id))


def parking():
    return query('SELECT * FROM parking ORDER BY id')


def update_parking(zone,occupied):
    execute('UPDATE parking SET occupied=MIN(capacity,MAX(0,?)) WHERE id=?',(int(occupied),zone))


def energy_for(space_id):
    rows=query('SELECT * FROM energy WHERE space_id=?',(space_id,))
    return rows[0] if rows else None


def set_energy(space_id,values):
    execute('UPDATE energy SET ac=?, lights=?, fans=?, other=? WHERE space_id=?',(*[float(values[k]) for k in ('ac','lights','fans','other')],space_id))


def due_for(priority):
    hours={'Critical':2,'High':24,'Medium':72,'Low':168}[priority]
    return (datetime.now()+timedelta(hours=hours)).isoformat(timespec='minutes')


def add_ticket(source,building,location,category,description,priority='Medium',staff='Unassigned'):
    if priority not in ('Critical','High','Medium','Low'):
        raise ValueError('Invalid priority')
    if not description.strip():
        raise ValueError('Issue description cannot be empty')
    return execute('''INSERT INTO tickets (source,building,location,category,description,
       priority,assigned_to,deadline,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)''',
       (source,building,location,category,description.strip(),priority,staff,due_for(priority),'Submitted',now()))


def tickets(building=None):
    if building:
        return query('SELECT * FROM tickets WHERE building=? ORDER BY id DESC',(building,))
    return query('SELECT * FROM tickets ORDER BY id DESC')


def update_ticket(ticket_id,priority,staff,deadline,status):
    valid={'Submitted','Assigned','In Progress','Resolved','Verified'}
    if status not in valid: raise ValueError('Invalid ticket state')
    execute('''UPDATE tickets SET priority=?,assigned_to=?,deadline=?,status=?,
      resolved_at=? WHERE id=?''',(priority,staff,deadline,status,now() if status in ('Resolved','Verified') else None,ticket_id))


def add_crowd_event(building,location,count,gate_status,action,staff='Unassigned'):
    return execute('''INSERT INTO crowd_events (building,location,count,shared_gate_status,
       action,staff,status,created_at) VALUES (?,?,?,?,?,?,?,?)''',
       (building,location,int(count),gate_status,action,staff,'New',now()))


def crowd_events(building):
    return query('SELECT * FROM crowd_events WHERE building=? ORDER BY id DESC',(building,))


def update_crowd_event(event_id,status,staff):
    if status not in ('New','Acknowledged','Investigating','Escalated','Closed'):
        raise ValueError('Invalid crowd-event state')
    execute('UPDATE crowd_events SET status=?,staff=? WHERE id=?',(status,staff,event_id))


def festival_scenario():
    with connect() as c:
        c.execute("UPDATE spaces SET occupied=MIN(capacity,CAST(capacity*0.92 AS INTEGER)) WHERE category IN ('cafeteria','library','waiting','common','lecture')")
        c.execute('UPDATE bins SET fill=95 WHERE fill>=70')
        c.execute('UPDATE parking SET occupied=MAX(0,capacity-2)')


def reset_scenario():
    """Reset seed occupancy and bins without destroying any user reports or tasks."""
    with connect() as c:
        c.execute("UPDATE spaces SET occupied=CASE WHEN category='classroom' THEN 30 WHEN category='cafeteria' THEN 70 WHEN category='library' THEN 90 WHEN category='lecture' THEN 120 WHEN category='waiting' THEN 25 ELSE 35 END")
        c.execute("UPDATE bins SET fill=CASE WHEN location='Cafeteria vicinity' THEN 92 WHEN location='Common Area' THEN 78 ELSE 35 END")
        c.execute("UPDATE parking SET occupied=CASE WHEN id='P1' THEN 53 WHEN id='P2' THEN 28 ELSE 51 END")
