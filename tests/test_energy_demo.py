"""Checks the precise energy and occupancy classification requirements."""
import tempfile
import unittest
from pathlib import Path
from campusverse.energy_demo import classify_interval, load_energy_readings

CSV=Path(__file__).resolve().parents[1]/'data'/'synthetic_classroom_energy.csv'

class EnergyTests(unittest.TestCase):
    def test_file_and_formula(self):
        rows=load_energy_readings(CSV)
        self.assertEqual(len(rows),28)
        for row in rows:
            expected=(round(row['ac_energy_kwh']/(row['occupancy']*row['duration_hours']),4)
                      if row['occupancy'] else None)
            self.assertEqual(row['energy_per_person_hour_kwh'],expected)
    def test_zero_occupancy_blank(self):
        rows=load_energy_readings(CSV)
        self.assertTrue(any(r['occupancy']==0 for r in rows))
        self.assertTrue(all(r['energy_per_person_hour_kwh'] is None for r in rows if r['occupancy']==0))
    def test_red(self):
        for fan,light in [('On','Off'),('Off','On'),('On','On')]:
            self.assertEqual(classify_interval({'occupancy':0,'fan_status':fan,'light_status':light,'electricity_consumption_kwh':2}), 'Possible wastage')
    def test_green(self):
        for rec in [{'occupancy':20,'fan_status':'On','light_status':'On','electricity_consumption_kwh':2},
                    {'occupancy':0,'fan_status':'Off','light_status':'Off','electricity_consumption_kwh':0}]:
            self.assertEqual(classify_interval(rec),'Normal use')
    def test_gray(self):
        for rec in [{'occupancy':None,'fan_status':'On','light_status':'On','electricity_consumption_kwh':2},
                    {'occupancy':12,'fan_status':None,'light_status':'On','electricity_consumption_kwh':2},
                    {'occupancy':12,'fan_status':'On','light_status':None,'electricity_consumption_kwh':2}]:
            self.assertEqual(classify_interval(rec),'Unknown')
if __name__=='__main__':unittest.main()
