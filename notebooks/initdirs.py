import sys
import os

CODE_DIR = os.environ['CODEROOT']
DATA_DIR = '../data'

for module_dir in ('visionfuncs', 'EPypes', 'visiongraph'):
    m_path = os.path.join(CODE_DIR, module_dir)
    if m_path not in sys.path:
        sys.path.append(m_path)
