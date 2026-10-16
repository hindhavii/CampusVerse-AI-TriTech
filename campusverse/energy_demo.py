"""Tiny synthetic energy reader; standard library only, no new dependencies."""
from __future__ import annotations

import csv
from pathlib import Path


def classify_interval(row: dict) -> str:
    """Classify occupancy and fan/light statuses using the approved color rules."""
    occupancy = row.get('occupancy')
    fan = row.get('fan_status')
    light = row.get('light_status')
    electricity = row.get('electricity_consumption_kwh')
    if occupancy is None or fan not in ('On', 'Off') or light not in ('On', 'Off'):
        return 'Unknown'
    if occupancy == 0 and (fan == 'On' or light == 'On'):
        return 'Possible wastage'
    if occupancy == 0 and fan == 'Off' and light == 'Off':
        return 'Normal use'
    if occupancy > 0 and electricity is not None and electricity > 0:
        return 'Normal use'
    return 'Unknown'


def load_energy_readings(path: str | Path) -> list[dict]:
    """Load and recalculate AC kWh per person-hour; blank for zero occupancy."""
    output = []
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        expected = {'timestamp', 'building', 'room', 'duration_hours', 'occupancy',
                    'fan_status', 'light_status', 'ac_energy_kwh',
                    'electricity_consumption_kwh'}
        if not expected.issubset(set(reader.fieldnames or [])):
            raise ValueError('Synthetic energy CSV lacks a required column')
        for r in reader:
            duration = float(r['duration_hours'])
            occupancy = int(r['occupancy']) if r['occupancy'].strip() else None
            ac = float(r['ac_energy_kwh'])
            total = float(r['electricity_consumption_kwh'])
            if duration <= 0 or ac < 0 or total < ac or (occupancy is not None and occupancy < 0):
                raise ValueError('Invalid energy dataset reading')
            pp = round(ac/(occupancy*duration), 4) if occupancy else None
            output.append({'timestamp': r['timestamp'], 'building': r['building'],
                           'room': r['room'], 'room_type': r.get('room_type',''),
                           'duration_hours':duration, 'occupancy':occupancy,
                           'fan_status':r['fan_status'].strip() or None,
                           'light_status':r['light_status'].strip() or None,
                           'ac_energy_kwh':ac,'electricity_consumption_kwh':total,
                           'energy_per_person_hour_kwh':pp})
    return output
