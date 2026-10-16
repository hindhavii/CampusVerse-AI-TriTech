"""Verifies linkages without requiring a browser or a Streamlit server."""
import tempfile
import unittest
from pathlib import Path
from campusverse import data

ROOT=Path(__file__).resolve().parents[1]

class MergeNavigationTests(unittest.TestCase):
    def test_scene_uses_click_bridge_not_generic_interior(self):
        scene=(ROOT/'campus_picker'/'index.html').read_text(encoding='utf-8')
        for term in ['streamlit:setComponentValue','window.cvSelect(key)',"campusBuildings['Sports Facilities']", "campusBuildings['Open Auditorium']", "campusBuildings['Parking']", "const ARENA=makeArena(),CRICKET=makeCricket()",'soeEntranceDetail(SOE)']:
            self.assertIn(term,scene)
    def test_locations_and_academic_floors(self):
        self.assertIn('DSU Arena',data.BUILDINGS)
        self.assertIn('Cricket Ground',data.BUILDINGS)
        self.assertIn('Parking',data.BUILDINGS)
        self.assertNotIn('Y Block',data.BUILDINGS)
        self.assertEqual(data.FLOORS,[0,1,2,3,4,5])
    def test_persistent_ticket_and_nonacademic_options(self):
        with tempfile.TemporaryDirectory() as temp:
            former=data.DB
            try:
                data.DB=Path(temp)/'example.sqlite'
                data.initialize()
                tid=data.add_ticket('Student / Faculty','SOE','101','Faulty projector','Test projector problem')
                self.assertEqual(data.query('SELECT status FROM tickets WHERE id=?',(tid,))[0]['status'],'Submitted')
                data.update_ticket(tid,'High','Electrical Team',data.due_for('High'),'Assigned')
                self.assertEqual(data.query('SELECT status FROM tickets WHERE id=?',(tid,))[0]['status'],'Assigned')
                for b in ['DSU Arena','Cricket Ground','Sports Facilities','Open Auditorium']:
                    self.assertTrue(data.spaces(b,'event'))
                    self.assertFalse(data.spaces(b,'classroom'))
            finally:
                data.DB=former
if __name__=='__main__':unittest.main()
