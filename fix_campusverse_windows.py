"""One-time fix for Windows file locking and 3D-test text encoding.

Put this file beside app.py in the existing CampusVerse_AI_Castle_Merged
folder, then run: py fix_campusverse_windows.py
Preserves SQLite data, password configuration, 3D graphics and dashboards.
"""
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
if not (root / 'app.py').is_file():
    candidates = [p for p in root.glob('*/app.py') if (p.parent / 'campusverse' / 'data.py').is_file()]
    if len(candidates) == 1:
        root = candidates[0].parent
    else:
        sys.exit('ERROR: Place this file inside the folder containing app.py, campusverse and tests.')

source = root / 'campusverse' / 'data.py'
test = root / 'tests' / 'test_merged_navigation.py'

old_connect = '''def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(DB),timeout=15)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=8000')
    return conn
'''
new_connect = '''@contextmanager
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
'''
old_scene = "(ROOT/'campus_picker'/'index.html').read_text()"
new_scene = "(ROOT/'campus_picker'/'index.html').read_text(encoding='utf-8')"

if not source.is_file() or not test.is_file():
    sys.exit('ERROR: The project is missing campusverse/data.py or tests/test_merged_navigation.py')

src = source.read_text(encoding='utf-8')
tests = test.read_text(encoding='utf-8')
if old_connect not in src and '@contextmanager\ndef connect():' not in src:
    sys.exit('ERROR: data.py is a different version. No changes were made.')
if old_scene not in tests and new_scene not in tests:
    sys.exit('ERROR: test_merged_navigation.py is a different version. No changes were made.')

if old_connect in src:
    src = src.replace('import sqlite3\n', 'import sqlite3\nfrom contextlib import contextmanager\n', 1)
    src = src.replace(old_connect, new_connect, 1)
    shutil.copy2(source, source.with_suffix('.py.before_windows_fix.bak'))
    source.write_text(src, encoding='utf-8')
    print('FIXED: SQLite database connection cleanup.')
else:
    print('ALREADY FIXED: SQLite database connection cleanup.')

if old_scene in tests:
    shutil.copy2(test, test.with_suffix('.py.before_windows_fix.bak'))
    test.write_text(tests.replace(old_scene, new_scene, 1), encoding='utf-8')
    print('FIXED: Windows UTF-8 reading in 3D click test.')
else:
    print('ALREADY FIXED: Windows UTF-8 reading in 3D click test.')

print('\nRunning all existing automated tests...\n')
result = subprocess.run(
    [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
    cwd=root,
    check=False,
)
if result.returncode:
    sys.exit('Some tests still failed. Please share the full error output; your data was not deleted.')
print('\nSUCCESS: Tests passed. You can now run: py -m streamlit run app.py')
