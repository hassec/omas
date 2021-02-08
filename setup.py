import os
import sys
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
]

extras_require = {
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
            f.write(item.ljust(25) + '# required\n')
        f.write('\n')
        for requirement in sorted(list(extras_require.keys()), key=lambda x: x.lower()):
            for item in sorted(extras_require[requirement], key=lambda x: x.lower()):
                if requirement in ['imas', 'hdc', 'uda', 'build_structures']:
                    item = '#' + item
                    f.write(item.ljust(25) + '# %s\n' % requirement)

packages = ['omas', 'omas.examples', 'omas.samples', 'omas.tests', 'omas.utilities']
package_data = {
    'omas': ['*.py', '*.pyx', 'version'],
    'omas.examples': ['*.py'],
    'omas.samples': ['*'],
    'omas.tests': ['*.py'],
    'omas.utilities': ['*.py'],
}
for item in glob.glob(os.sep.join([here, 'omas', 'imas_structures', '*'])):
    packages.append('omas.imas_structures.' + os.path.split(item)[1])
    package_data['omas.imas_structures.' + os.path.split(item)[1]] = ['*.json']

long_description = '''
OMAS is a Python library designed to simplify the interface of third-party codes with the `ITER <http://iter.org>`_ Integrated Modeling and Analysis Suite (`IMAS <https://confluence.iter.org/display/IMP>`_).

* It provides a **convenient Python API**

* capable of storing data with **different file/database formats**

* in a form that is **always compatible with the IMAS data model**

Mapping the physics codes I/O to the IMAS data model is done in third party Python codes such as the `OMFIT framework <https://omfit.io>`_.
'''

print('INFO: run the `imports_check.py` script to quickly verify that all Python dependencies for OMAS are installed\n')

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
