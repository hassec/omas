'''save/load from MongoDB routines

-------
'''

# to start a mongodb server on the local workstation
# mongod --dbpath $DIRECTORY_WHERE_TO_STORE_DATA

from __future__ import print_function, division, unicode_literals

from .omas_utils import *
from .omas_core import ODS


# -----------------------------
# save and load OMAS to MongoDB
# -----------------------------
def save_omas_mongo(ods, collection, database='OMAS', server=omas_rcparams['default_mongo_server']):
    """
    Save an OMAS data set to MongoDB

    :param ods: OMAS data set

    :param collection: collection name in the database

    :param database: database name on the server

    :param server: server name

    :return: unique `_id` identifier of the record
    """

    printd('Saving OMAS data to MongoDB: collection=%s database=%s  server=%s' % (collection, database, server), topic=['MongoDB'])

    # importing module
    from pymongo import MongoClient

    # Connect with the portnumber and host
    client = MongoClient(server)

    # Access database
    mydatabase = client[database]

    # Access collection of the database
    mycollection = mydatabase[collection]

    # cheap way to encode data
    kw = {'indent': 0, 'separators': (',', ': '), 'sort_keys': True}
    json_string = json.dumps(ods, default=lambda x: json_dumper(x, None), **kw)
    jj = json.loads(json_string)

    _id = mydatabase.myTable.insert(jj)
    return str(_id)


def load_omas_mongo(find, collection, database='OMAS', server=omas_rcparams['default_mongo_server'], consistency_check=True, imas_version=omas_rcparams['default_imas_version']):
    """
    Load an OMAS data set from MongoDB

    :param find: dictionary to find data in the database

    :param collection: collection name in the database

    :param database: database name on the server

    :param server: server name

    :param consistency_check: verify that data is consistent with IMAS schema

    :param imas_version: imas version to use for consistency check

    :return: list of OMAS data set that match find criterion
    """

    # importing module
    from pymongo import MongoClient
    from bson.objectid import ObjectId

    # allow search by _id
    if not isinstance(find, dict):
        raise TypeError('load_omas_mongo find attribute must be a dictionary')
    if '_id' in find:
        find = copy.deepcopy(find)
        find['_id'] = ObjectId(find['_id'])

    printd('Loading OMAS data from MongoDB: collection=%s database=%s  server=%s' % (collection, database, server), topic=['MongoDB'])

    # Connect with the portnumber and host
    client = MongoClient(server)

    # Access database
    mydatabase = client[database]

    # Access collection of the database
    mycollection = mydatabase[collection]

    results = {}
    for record in mydatabase.myTable.find(find):
        ods = ODS(consistency_check=consistency_check, imas_version=imas_version)
        _id = record['_id']
        del record['_id']
        ods.from_structure(record)
        results[_id] = ods

    return results


def through_omas_mongo(ods, method=['function', 'class_method'][1]):
    """
    Test save and load OMAS MongoDB

    :param ods: ods

    :return: ods
    """
    if method == 'function':
        _id = save_omas_mongo(ods, 'test')
        results = load_omas_mongo({'_id': _id}, 'test')
        if len(results) != 1:
            raise Exception('through_omas_mongo failed')
        ods1 = list(results.values())[0]
        return ods1
    else:
        _id = ods.save('mongo', 'test')
        ods1 = ODS().load('mongo', {'_id': _id}, 'test')
        return ods1
