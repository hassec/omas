import os
import glob
import subprocess

install_requires = [
    'numpy>=1.16.1',
    'uncertainties',
    'pint',
    'netCDF4',
    'boto3',
    'matplotlib',
    'scipy',
    'h5py',
    'pymongo',
    'dnspython',
    'xmltodict',
    'xarray',
    'setuptools>=41.2',
    'tqdm',
    'Cython',
    # latest xarray version that works with 3.7 doesn't work
    # with importlib_metadata >5 since they deprecated the `get()` method on Entrypoints
    "importlib_metadata <5;python_version=='3.7'"
]

extras_require = {
    'machine': [
        'omfit_classes',
        'pexpect',
        'fortranformat',
        'pygacode',
    ],
    'hdc': ['pyhdc'],
    'imas': ['imas'],
    'uda': ['pyuda'],
    'build_structures': ['bs4'],
    'build_documentation': ['Sphinx', 'sphinx-bootstrap-theme', 'sphinx-gallery', 'Pillow'],
}

# Add .json IMAS structure files to the package
here = os.path.abspath(os.path.split(__file__)[0]) + os.sep

# Automatically generate requirement.txt file if this is the OMAS repo and requirements.txt is missing
if os.path.exists(here + '.git') and not os.path.exists(here + 'requirements.txt'):
    with open(here + 'requirements.txt', 'w') as f:
        f.write('# Do not edit this file by hand, operate on setup.py instead\n#\n')
        f.write('# usage: pip install -r requirements.txt\n\n')
        for item in install_requires:
            f.write(item.ljust(50) + ' # required\n')
        for requirement in extras_require:
            f.write('\n')
            for item in extras_require[requirement]:
                f.write('# ' + item.ljust(25) + '# %s\n' % requirement)

packages = ['omas', 'omas.examples', 'omas.samples', 'omas.tests', 'omas.utilities']
package_data = {
    'omas': ['*.py', '*.pyx', 'version'],
    'omas.examples': ['*.py'],
    'omas.samples': ['*'],
    'omas.tests': ['*.py'],
    'omas.utilities': ['*.py'],
}

machine_mappings_dir = here + os.sep + 'omas' + os.sep + 'machine_mappings'
for item in glob.glob(os.sep.join([here, 'omas', 'imas_structures', '*'])):
    packages.append('omas.imas_structures.' + os.path.split(item)[1])
    package_data['omas.imas_structures.' + os.path.split(item)[1]] = ['*.json']
for retry in [1, 2]:
    if os.path.exists(here + '.git') and retry == 1:
        try:
            tmp = f'pushd {machine_mappings_dir}; git ls-files; popd'
            machine_mappings_files = subprocess.check_output(tmp, shell=True).decode("utf-8").strip().split('\n')[2:-1]
            machine_mappings_files = ['omas' + os.sep + 'machine_mappings' + os.sep + k for k in machine_mappings_files]
        except subprocess.CalledProcessError:
            pass
        else:
            print("setup.py machine_mappings_files based on git")
            break
    else:
        machine_mappings_files = []
        for root, subdirs, files in os.walk(machine_mappings_dir):
            root = root[len(machine_mappings_dir) + 1 :]
            for file in reversed(files):
                machine_mappings_files.append('omas' + os.sep + 'machine_mappings' + os.sep + root + os.sep + file)
dirs = {os.path.dirname(file): [] for file in sorted(machine_mappings_files)}
for file in machine_mappings_files:
    dirs[os.path.dirname(file)].append(os.path.basename(file))
for dir in dirs:
    packages.append(dir.replace('/', '.'))
    package_data[dir.replace('/', '.')] = dirs[dir]

long_description = '''
OMAS is a Python library designed to simplify the interface of third-party codes with the `ITER <http://iter.org>`_ Integrated Modeling and Analysis Suite (`IMAS <https://confluence.iter.org/display/IMP>`_).

* It provides a **convenient Python API**

* capable of storing data with **different file/database formats**

* in a form that is **always compatible with the IMAS data model**

Mapping the physics codes I/O to the IMAS data model is done in third party Python codes such as the `OMFIT framework <https://omfit.io>`_.
'''

print()
print('INFO: optional dependencies:')
from pprint import pprint

pprint(extras_require)
print()
print('INFO: run the `imports_check.py` script to quickly verify that all Python dependencies for OMAS are installed')
print()

from setuptools import setup

setup(
    name='omas',
    version=open(here + 'omas/version', 'r').read().strip(),
    description='Ordered Multidimensional Array Structures',
    url='https://gafusion.github.io/omas',
    author='Orso Meneghini',
    license='MIT',
    classifiers=['License :: OSI Approved :: MIT License', 'Programming Language :: Python :: 3'],
    keywords='integrated modeling OMFIT IMAS ITER',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=packages,
    package_data=package_data,
    install_requires=install_requires,
    extras_require=extras_require,
)
