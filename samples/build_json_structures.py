from __future__ import print_function, division, unicode_literals
import os, re, glob

os.environ['OMAS_DEBUG_TOPIC'] = '*'
from omas import *

force_build = True

generate_xml_schemas()

for imas_version in sorted(map(lambda x: os.path.split(x)[-1], glob.glob(imas_json_dir + os.sep + '*'))):

    print('Processing IMAS data structures v%s' % re.sub('_', '.', imas_version))
    filename = os.path.abspath(os.sep.join([imas_json_dir, imas_version, 'omas_doc.html']))

    if force_build or not os.path.exists(filename):
        create_json_structure(imas_version=imas_version)
        create_html_documentation(imas_version=imas_version)
