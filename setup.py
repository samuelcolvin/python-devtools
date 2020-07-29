import re
from importlib.machinery import SourceFileLoader
from pathlib import Path
from setuptools import setup

description = "Python's missing debug print command and other development tools."
THIS_DIR = Path(__file__).resolve().parent
try:
    history = (THIS_DIR / 'HISTORY.md').read_text()
    history = re.sub(r'#(\d+)', r'[#\1](https://github.com/samuelcolvin/pydantic/issues/\1)', history)
    history = re.sub(r'( +)@([\w\-]+)', r'\1[@\2](https://github.com/\2)', history, flags=re.I)
    history = re.sub('@@', '@', history)

    long_description = (THIS_DIR / 'README.md').read_text() + '\n\n' + history
except FileNotFoundError:
    long_description = description + '.\n\nSee https://python-devtools.helpmanual.io/ for documentation.'

# avoid loading the package before requirements are installed:
version = SourceFileLoader('version', 'devtools/version.py').load_module()

setup(
    name='devtools',
    version=str(version.VERSION),
    description=description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Environment :: MacOS X',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    author='Samuel Colvin',
    author_email='s@muelcolvin.com',
    url='https://github.com/samuelcolvin/python-devtools',
    license='MIT',
    packages=['devtools'],
    python_requires='>=3.6',
    extras_require={
        'pygments': ['Pygments>=2.2.0'],
    },
    zip_safe=True,
)
