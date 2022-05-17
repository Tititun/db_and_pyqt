import sys
import os
PYTHON_PATH = sys.executable
print(sys.path[0])
file_path = sys.path[-1] + 'server.py'
os.system(f'{PYTHON_PATH} {file_path}')
