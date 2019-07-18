import os
import sys
import glob
import subprocess

all_install_require = ['numpy', 'uncertainties', 'pint', 'netCDF4', 'boto3', 'matplotlib', 'scipy', 'h5py']
install_requires = {}
# https://github.com/pydata/xarray/commit/faacc8da000b7971233142be349ee39c6d088510
install_requires[2] = all_install_require + ['xarray<=0.11.0']
install_requires[3] = all_install_require + ['xarray']

extras_require = {'hdc': ['pyhdc'],
                  'imas': ['imas'],
                  'uda': ['pyuda'],
                  'build_structures': ['xmltodict', 'bs4'],
                  'build_documentation': ['Sphinx', 'sphinx-bootstrap-theme', 'sphinx-gallery', 'Pillow']}

# Add .json IMAS structure files to the package
here = os.path.abspath(os.path.split(__file__)[0]) + os.sep

# Automatically generate requirement.txt file if this is the OMAS repo and requirements.txt is missing
if os.path.exists(here + '.git') and not os.path.exists(here + 'requirements.txt'):
    print('Generating new requirements files')
    for version in [2, 3]:
        with open(here + 'requirements_python%d.txt' % version, 'w') as f:
            f.write('# Do not edit this file by hand, operate on setup.py instead\n#\n')
            f.write('# usage: pip install -r requirements_python%d.txt\n\n' % version)
            for item in install_requires[version]:
                f.write(item.ljust(25) + '# required\n')
            f.write('\n')
            for requirement in extras_require:
                for item in extras_require[requirement]:
                    if requirement in ['imas', 'hdc', 'uda', 'build_structures']:
                        item = '#' + item
                    f.write(item.ljust(25) + '# %s\n' % requirement)

if os.path.exists('.git'):
    print('==GIT DIRECTORY FOUND==')
    p = subprocess.Popen("git ls-files --exclude-standard [^sphinx]*", shell=True, stdout=subprocess.PIPE)
    std_out, std_err = p.communicate()
    files = str(std_out).strip().split('\n')
else:
    files = []
    path = os.path.dirname(os.path.abspath(__file__)) + '/'
    for r, d, f in os.walk(path):
        if [r[len(path):].startswith(exclude) for exclude in ['.git', '.idea']]:
            continue
        for file in f:
            files.append(os.path.join(r[len(path):], file))
dirs = sorted(list(set([os.path.dirname(file) for file in files])))
dirs = [dir for dir in dirs if dir]
packages = [dir.replace('/', '.') for dir in dirs if dir]
package_data = {dir.replace('/', '.'): [os.path.basename(file) for file in files if os.path.dirname(file) == dir] for dir in dirs if dir}

long_description = '''
OMAS is a Python library designed to simplify the interface of third-party codes with the `ITER <http://iter.org>`_ Integrated Modeling and Analysis Suite (`IMAS <https://confluence.iter.org/display/IMP>`_).

* It provides a **convenient Python API**

* capable of storing data with **different file/database formats**

* in a form that is **always compatible with the IMAS data model**

Mapping the physics codes I/O to the IMAS data model is done in third party Python codes such as the `OMFIT framework <http://gafusion.github.io/OMFIT-source>`_.
'''

from setuptools import setup

setup(
    name='omas',
    version=open(here + 'omas/version', 'r').read().strip(),
    description='Ordered Multidimensional Array Structures',
    url='https://gafusion.github.io/omas',
    author='Orso Meneghini',
    license='MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],
    keywords='integrated modeling OMFIT IMAS ITER',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=packages,
    package_data=package_data,
    install_requires=install_requires[sys.version_info[0]],
    extras_require=extras_require)
