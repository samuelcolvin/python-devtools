from setuptools.config import pyprojecttoml

if __name__ == '__main__':
    version = pyprojecttoml.load_file('pyproject.toml')['project']['version']
    path = 'devtools/version.py'
    with open(path, 'w') as f:
        f.write(f"VERSION = '{version}'\n")
    print(f'Set "{version}" in {path}')
