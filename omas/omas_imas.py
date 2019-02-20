'''save/load from IMAS routines

-------
'''

from __future__ import print_function, division, unicode_literals

from .omas_utils import *
from .omas_core import ODS


# --------------------------------------------
# IMAS convenience functions
# --------------------------------------------
def imas_open(user, machine, pulse, run, new=False,
              imas_version=os.environ.get('IMAS_VERSION', omas_rcparams['default_imas_version'])):
    """
    function to open an IMAS

    :param user: IMAS username

    :param machine: IMAS machine

    :param pulse: IMAS pulse

    :param run: IMAS run id

    :param new: whether the open should create a new IMAS tree

    :param imas_version: IMAS version

    :return: IMAS ids
    """
    import imas
    printd("ids = imas.ids(%d,%d)" % (pulse, run), topic='imas_code')
    ids = imas.ids(pulse, run)

    if user is None and machine is None:
        pass
    elif user is None or machine is None:
        raise (Exception('user={user}, machine={machine}, imas_version={imas_version}\n'
                         'Either specify all or none of `user`, `machine`, `imas_version`\n'
                         'If none of them are specified then use `imasdb` command to set '
                         'MDSPLUS_TREE_BASE_? environmental variables'.format(user=user, machine=machine, pulse=pulse,
                                                                              run=run, imas_version=imas_version)))

    if user is None and machine is None:
        if new:
            printd("ids.create()", topic='imas_code')
            ids.create()
        else:
            printd("ids.open()", topic='imas_code')
            try:
                ids.open()
            except Exception as _excp:
                if 'Error opening imas pulse' in str(_excp):
                    raise (IOError('Error opening imas pulse %d run %d' % (pulse, run)))
        if not ids.isConnected():
            raise (Exception('Failed to establish connection to IMAS database '
                             '(pulse:{pulse} run:{run}, DB:{db})'.format(pulse=pulse, run=run, db=os.environ.get('MDSPLUS_TREE_BASE_0', '???')[:-2])))

    else:
        if new:
            printd("ids.create_env(%s, %s, %s)" % (repr(user), repr(machine), repr(imas_version)), topic='imas_code')
            ids.create_env(user, machine, imas_version)
        else:
            printd("ids.open_env(%s, %s, %s)" % (repr(user), repr(machine), repr(imas_version)), topic='imas_code')
            try:
                ids.open_env(user, machine, imas_version)
            except Exception as _excp:
                if 'Error opening imas pulse' in str(_excp):
                    raise (IOError('Error opening imas pulse (user:%s machine:%s pulse:%s run:%s, imas_version:%s)' % (user, machine, pulse, run, imas_version)))
        if not ids.isConnected():
            raise (Exception('Failed to establish connection to IMAS database (user:%s machine:%s pulse:%s run:%s, imas_version:%s)' % (user, machine, pulse, run, imas_version)))
    return ids


def imas_set(ids, path, value, skip_missing_nodes=False, allocate=False):
    """
    assign a value to a path of an open IMAS ids

    :param ids: open IMAS ids to write to

    :param path: ODS path

    :param value: value to assign

    :param skip_missing_nodes:  if the IMAS path does not exists:
                             `False` raise an error
                             `True` does not raise error
                             `None` prints a warning message

    :param allocate: whether to perform only IMAS memory allocation (ids.resize)

    :return: path if set was done, otherwise None
    """
    if numpy.atleast_1d(is_uncertain(value)).any():
        path = copy.deepcopy(path)
        tmp = imas_set(ids, path, nominal_values(value), skip_missing_nodes=skip_missing_nodes, allocate=allocate)
        path[-1] = path[-1] + '_error_upper'
        imas_set(ids, path, std_devs(value), skip_missing_nodes=skip_missing_nodes, allocate=allocate)
        return tmp

    ds = path[0]
    path = path[1:]

    # `info` IDS is used by OMAS to hold user, machine, pulse, run, imas_version
    # for saving methods that do not carry that information. IMAS does not store
    # this information as part of the data dictionary.
    if ds in add_datastructures.keys():
        return

    # for ITM we have to append Array to the name of the data structure
    DS = ds
    if 'imas' == 'itm':
        ds = ds + 'Array'

    # identify data dictionary to use, from this point on `m` points to the IDS
    debug_path = ''
    if hasattr(ids, ds):
        debug_path += 'ids.%s' % ds
        m = getattr(ids, ds)
        if hasattr(m, 'time') and not isinstance(m.time, float) and not m.time.size:
            m.time.resize(1)
            m.time[0] = -1.0
    elif skip_missing_nodes is not False:
        if skip_missing_nodes is None:
            printe('WARNING: %s is not part of IMAS structure' % l2i([ds] + path))
        return
    else:
        printd(debug_path, topic='imas_code')
        raise (AttributeError('%s is not part of IMAS structure' % l2i([ds] + path)))

    # traverse IMAS structure until reaching the leaf
    out = m
    for kp, p in enumerate(path):
        location = l2i([ds] + path[:kp + 1])
        if isinstance(p, basestring):
            if hasattr(out, p):
                if kp < (len(path) - 1):
                    debug_path += '.' + p
                    out = getattr(out, p)
            elif skip_missing_nodes is not False:
                if skip_missing_nodes is None:
                    printe('WARNING: %s is not part of IMAS structure' % location)
                return
            else:
                printd(debug_path, topic='imas_code')
                raise (AttributeError('%s is not part of IMAS structure' % location))
        else:
            try:
                out = out[p]
                debug_path += '[%d]' % p
            except (AttributeError, IndexError):  # AttributeError is for ITM
                if not allocate:
                    raise (IndexError('%s structure array exceed allocation' % location))
                printd(debug_path + ".resize(%d)" % (p + 1), topic='imas_code')
                out.resize(p + 1)
                debug_path += '[%d]' % p
                out = out[p]

    # if we are allocating data, simply stop here
    if allocate:
        return [DS] + path

    # assign data to leaf node
    printd('setting  : %s' % location, topic='imas')
    if not isinstance(value, (basestring, numpy.ndarray)):
        value = numpy.array(value)
    setattr(out, path[-1], value)
    if 'imas_code' in os.environ.get('OMAS_DEBUG_TOPIC', ''):  # use if statement here to avoid unecessary repr(value) when not debugging
        printd(debug_path + '.%s=%s' % (path[-1], repr(value).replace('\\n', '\n')), topic='imas_code')

    # return path
    return [DS] + path


def imas_get(ids, path, skip_missing_nodes=False):
    """
    read the value of a path in an open IMAS ids

    :param ids: open IMAS ids to read from

    :param path: ODS path

    :param skip_missing_nodes:  if the IMAS path does not exists:
                             `False` raise an error
                             `True` does not raise error
                             `None` prints a warning message

    :return: the value that was read if successful or None otherwise
    """
    printd('fetching: %s' % l2i(path), topic='imas')
    ds = path[0]
    path = path[1:]

    # for ITM we have to append Array to the name of the data structure
    if 'imas' == 'itm':
        ds = ds + 'Array'

    debug_path = ''
    if hasattr(ids, ds):
        debug_path += 'ids.%s' % ds
        m = getattr(ids, ds)
    elif skip_missing_nodes is not False:
        if skip_missing_nodes is None:
            printe('WARNING: %s is not part of IMAS structure' % l2i([ds] + path))
        return None
    else:
        printd(debug_path, topic='imas_code')
        raise (AttributeError('%s is not part of IMAS structure' % l2i([ds] + path)))

    # traverse the IDS to get the data
    out = m
    for kp, p in enumerate(path):
        if isinstance(p, basestring):
            if hasattr(out, p):
                debug_path += '.%s' % p
                out = getattr(out, p)
            elif skip_missing_nodes is not False:
                if skip_missing_nodes is None:
                    printe('WARNING: %s is not part of IMAS structure' % l2i([ds] + path[:kp + 1]))
                    printe(out.__dict__.keys())
                return None
            else:
                printd(debug_path, topic='imas_code')
                raise (AttributeError('%s is not part of IMAS structure' % l2i([ds] + path[:kp + 1])))
        else:
            debug_path += '[%s]' % p
            out = out[p]

    printd(debug_path, topic='imas_code')
    return out


# --------------------------------------------
# save and load OMAS to IMAS
# --------------------------------------------
def save_omas_imas(ods, user=None, machine=None, pulse=None, run=None, new=False,
                   imas_version=os.environ.get('IMAS_VERSION', omas_rcparams['default_imas_version'])):
    """
    Save OMAS data to IMAS

    :param ods: OMAS data set

    :param user: IMAS username (reads ods['dataset_description.data_entry.user'] if user is None and finally fallsback on os.environ['USER'])

    :param machine: IMAS machine (reads ods['dataset_description.data_entry.machine'] if machine is None)

    :param pulse: IMAS pulse (reads ods['dataset_description.data_entry.pulse'] if pulse is None)

    :param run: IMAS run (reads ods['dataset_description.data_entry.run'] if run is None and finally fallsback on 0)

    :param new: whether the open should create a new IMAS tree

    :param imas_version: IMAS version

    :return: paths that have been written to IMAS
    """

    # handle default values for user, machine, pulse, run, imas_version
    # it tries to re-use existing information
    if user is None:
        user = ods.get('dataset_description.data_entry.user', os.environ['USER'])
    if machine is None:
        machine = ods.get('dataset_description.data_entry.machine', None)
    if pulse is None:
        pulse = ods.get('dataset_description.data_entry.pulse', None)
    if run is None:
        run = ods.get('dataset_description.data_entry.run', 0)

    if user is not None and machine is not None:
        printd('Saving to IMAS (user:%s machine:%s pulse:%d run:%d, imas_version:%s)' % (user, machine, pulse, run, imas_version), topic='imas')
    elif user is None and machine is None:
        printd('Saving to IMAS (pulse:%d run:%d, DB:%s)' % (pulse, run, os.environ.get('MDSPLUS_TREE_BASE_0', '???')[:-2]), topic='imas')

    # ensure requirements for writing data to IMAS are satisfied
    if 'imas' != 'itm':
        for ds in ods.keys():
            ods[ds].satisfy_imas_requirements()

    # get the list of paths from ODS
    paths = set_paths = ods.paths()

    try:
        # open IMAS tree
        ids = imas_open(user=user, machine=machine, pulse=pulse, run=run, new=new, imas_version=imas_version)

    except IOError as _excp:
        raise (IOError(str(_excp) + '\nIf this is a new pulse/run then set `new=True`'))

    except ImportError:
        # fallback on saving IMAS as NC file if IMAS is not installed
        if not omas_rcparams['allow_fake_imas_fallback']:
            raise
        filename = os.sep.join([omas_rcparams['fake_imas_dir'], '%s_%s_%d_%d_v%s.pkl' % (user, machine, pulse, run, imas_versions.get(imas_version, imas_version))])
        printe('Overloaded save_omas_imas: %s' % filename)
        from . import save_omas_pkl
        if not os.path.exists(omas_rcparams['fake_imas_dir']):
            os.makedirs(omas_rcparams['fake_imas_dir'])
        ods['dataset_description.data_entry.user'] = unicode(user)
        ods['dataset_description.data_entry.machine'] = unicode(machine)
        ods['dataset_description.data_entry.pulse'] = int(pulse)
        ods['dataset_description.data_entry.run'] = int(run)
        ods['dataset_description.imas_version'] = unicode(imas_version)
        save_omas_pkl(ods, filename)

    else:

        try:
            # allocate memory
            # NOTE: for how memory allocation works it is important to traverse the tree in reverse
            set_paths = []
            for path in reversed(paths):
                set_paths.append(imas_set(ids, path, ods[path], None, allocate=True))
            set_paths = filter(None, set_paths)

            # assign the data
            for path in set_paths:
                printd('writing %s' % l2i(path))
                imas_set(ids, path, ods[path], True)

            # actual write of IDS data to IMAS database
            for ds in ods.keys():
                if ds in add_datastructures.keys():
                    continue
                if 'imas' == 'itm':
                    ds = ds + 'Array'
                printd("ids.%s.put(0)" % ds, topic='imas_code')
                getattr(ids, ds).put(0)

        finally:
            # close connection to IMAS database
            printd("ids.close()", topic='imas_code')
            ids.close()

    return set_paths


def load_omas_imas(user=os.environ['USER'], machine=None, pulse=None, run=0, paths=None,
                   imas_version=os.environ.get('IMAS_VERSION', omas_rcparams['default_imas_version']), verbose=True):
    """
    Load OMAS data from IMAS

    NOTE: Either specify all or none of `user`, `machine`, `imas_version`
    If none of them are specified then use `imasdb` command to set the `MDSPLUS_TREE_BASE_?` environmental variables

    :param user: IMAS username

    :param machine: IMAS machine

    :param pulse: IMAS pulse

    :param run: IMAS run

    :param paths: list of paths to load from IMAS

    :param imas_version: IMAS version

    :param verbose: print loading progress

    :return: OMAS data set
    """

    if pulse is None or run is None:
        raise (Exception('`pulse` and `run` must be specified'))

    printd('Loading from IMAS (user:%s machine:%s pulse:%d run:%d, imas_version:%s)' % (user, machine, pulse, run, imas_version), topic='imas')

    try:
        ids = imas_open(user=user, machine=machine, pulse=pulse, run=run, new=False, imas_version=imas_version)

    except ImportError:
        if not omas_rcparams['allow_fake_imas_fallback']:
            raise
        filename = os.sep.join([omas_rcparams['fake_imas_dir'], '%s_%s_%d_%d_v%s.pkl' % (user, machine, pulse, run, imas_versions.get(imas_version, imas_version))])
        printe('Overloaded load_omas_imas: %s' % filename)
        from . import load_omas_pkl
        ods = load_omas_pkl(filename)

    else:

        try:
            # if paths is None then figure out what IDS are available and get ready to retrieve everything
            if paths is None:
                paths = [[structure] for structure in list_structures(imas_version=imas_version)]
                joined_paths = None # joined_paths==None means take everything, no need to filter out what is available based on what was requested
            else:
                joined_paths = map(l2i, paths)

            # fetch relevant IDSs and find available signals
            fetch_paths = []
            for path in paths:
                ds = path[0]
                path = path[1:]
                if ds in add_datastructures.keys():
                    continue
                if not hasattr(ids, ds):
                    if verbose:
                        print('| ', ds)
                    continue
                # ids fetching
                if not len(getattr(ids, ds).time):
                    printd("ids.%s.get()" % ds, topic='imas_code')
                    getattr(ids, ds).get()
                # ids discovery
                if len(getattr(ids, ds).time):
                    if verbose:
                        print('* ', ds)
                    available_paths = filled_paths_in_ids(ids, load_structure(ds, imas_version=imas_version)[1], [], [])
                    if joined_paths is None:
                        # if joined_paths is None, this means the user requested everything
                        fetch_paths = available_paths
                    else:
                        # intersect between what was requested and what is available
                        joined_available_paths = map(l2i, available_paths)
                        for jpath, path in zip(joined_paths, paths):
                            if path[0] != ds:
                                continue
                            jpath = jpath.replace('.', '\.')
                            jpath = '^' + jpath.replace('.:', '.[0-9]+') + '.*'
                            for japath, apath in zip(joined_available_paths, available_paths):
                                if re.match(jpath, japath):
                                    fetch_paths.append(apath)
                else:
                    if verbose:
                        print('- ', ds)
            joined_fetch_paths = map(l2i, fetch_paths)

            # build omas data structure
            ods = ODS(imas_version=imas_version)
            for k, path in enumerate(fetch_paths):
                if path[-1].endswith('_error_upper') or path[-1].endswith('_error_lower'):
                    continue
                # get data from ids
                data = imas_get(ids, path, None)
                if len(path) == 2 and path[-1] == 'time':
                    if data[0] == -1:
                        continue
                # skip empty arrays
                if isinstance(data, numpy.ndarray) and not data.size:
                    continue
                # skip missing floats and integers
                elif (isinstance(data, float) and data == -9E40) or (isinstance(data, int) and data == -999999999):
                    continue
                # skip empty strings
                elif isinstance(data, unicode) and not len(data):
                    continue
                # add uncertainty
                if l2i(path[:-1] + [path[-1] + '_error_upper']) in joined_fetch_paths:
                    stdata = imas_get(ids, path[:-1] + [path[-1] + '_error_upper'], None)
                    if isinstance(stdata, numpy.ndarray) and not stdata.size:
                        pass
                    elif (isinstance(stdata, float) and stdata == -9E40) or (isinstance(stdata, int) and stdata == -999999999):
                        pass
                    elif isinstance(stdata, unicode) and not len(stdata):
                        continue
                    else:
                        try:
                            data = uarray(data, stdata)
                        except uncertainties.core.NegativeStdDev as _excp:
                            printe('Error loading uncertainty for %s: %s' % (l2i(path), repr(_excp)))
                if verbose:
                    print('Loading data: {0:3.3f}%'.format(100 * float(k) / len(fetch_paths)))
                h = ods
                for step in path[:-1]:
                    h = h[step]
                h[path[-1]] = data

        finally:
            # close connection to IMAS database
            printd("ids.close()", topic='imas_code')
            ids.close()

    ods['dataset_description.data_entry.user'] = unicode(user)
    ods['dataset_description.data_entry.machine'] = unicode(machine)
    ods['dataset_description.data_entry.pulse'] = int(pulse)
    ods['dataset_description.data_entry.run'] = int(run)
    ods['dataset_description.imas_version'] = unicode(imas_version)

    return ods


if 'imas' != 'itm':
    def browse_imas(user=os.environ['USER'], pretty=True, quiet=False,
                    user_imasdbdir=os.sep.join([os.environ['HOME'], 'public', 'imasdb'])):
        '''
        Browse available IMAS data (machine/pulse/run) for given user

        :param user: user (of list of users) to browse. Browses all users if None.

        :param pretty: express size in MB and time in human readeable format

        :param quiet: print database to screen

        :param user_imasdbdir: directory where imasdb is located for current user (typically $HOME/public/imasdb/)

        :return: hierarchical dictionary with database of available IMAS data (machine/pulse/run) for given user
        '''
        # if no users are specified, find all users
        if user is None:
            user = glob.glob(user_imasdbdir.replace('/%s/' % os.environ['USER'], '/*/'))
            user = map(lambda x: x.split(os.sep)[-3], user)
        elif isinstance(user, basestring):
            user = [user]

        # build database for each user
        imasdb = {}
        for username in user:
            imasdb[username] = {}
            imasdbdir = user_imasdbdir.replace('/%s/' % os.environ['USER'], '/%s/' % username).strip()

            # find MDS+ datafiles
            files = list(recursive_glob('*datafile', imasdbdir))

            # extract machine/pulse/run from filename of MDS+ datafiles
            for file in files:
                tmp = file.split(os.sep)
                if not re.match('ids_[0-9]{5,}.datafile', tmp[-1]):
                    continue
                pulse_run = tmp[-1].split('.')[0].split('_')[1]
                pulse = int(pulse_run[:-4])
                run = int(pulse_run[-4:])
                machine = tmp[-4]

                # size and data
                st = os.stat(file)
                size = st.st_size
                date = st.st_mtime
                if pretty:
                    import time
                    size = '%d Mb' % (int(size / 1024 / 1024))
                    date = time.strftime('%d/%m/%y - %H:%M', time.localtime(date))

                # build database
                if machine not in imasdb[username]:
                    imasdb[username][machine] = {}
                imasdb[username][machine][pulse, run] = {'size': size, 'date': date}

        # print if not quiet
        if not quiet:
            pprint(imasdb)

        # return database
        return imasdb


    def load_omas_iter_scenario(pulse, run=0, paths=None,
                                imas_version=os.environ.get('IMAS_VERSION', omas_rcparams['default_imas_version']),
                                verbose=True):
        """
        Load OMAS data set from ITER IMAS scenario database
    
        :param pulse: IMAS pulse
    
        :param run: IMAS run
    
        :param paths: list of paths to load from IMAS
    
        :param imas_version: IMAS version
    
        :return: OMAS data set
    
        :param verbose: print loading progress
        """
        # set MDSPLUS_TREE_BASE_? environment variables as per
        # imasdb /work/imas/shared/iterdb/3 ; env | grep MDSPLUS_TREE_BASE
        try:
            bkp_imas_environment = {}
            for k in range(10):
                if 'MDSPLUS_TREE_BASE_%d' % k in os.environ:
                    bkp_imas_environment['MDSPLUS_TREE_BASE_%d' % k] = os.environ['MDSPLUS_TREE_BASE_%d' % k]
                os.environ['MDSPLUS_TREE_BASE_%d' % k] = '/work/imas/shared/iterdb/3/%d' % k

            # load data from imas
            ods = load_omas_imas(user=None, machine=None, pulse=pulse, run=run, paths=paths, imas_version=imas_version, verbose=verbose)

        finally:
            # restore existing IMAS environment
            for k in range(10):
                del os.environ['MDSPLUS_TREE_BASE_%d' % k]
                os.environ.update(bkp_imas_environment)

        return ods


def filled_paths_in_ids(ids, ds, path=None, paths=None, assume_uniform_array_structures=False):
    """
    List paths in an IDS that have data in its leaves

    :param ids: input ids

    :param ds: hierarchical data schema as returned for example by load_structure('equilibrium')[1]

    :param assume_uniform_array_structures: assume that the first structure in an array of structures has data in the same nodes locations of the later structures in the array

    :return: returns list of paths in an IDS that are filled
    """
    if path is None:
        path = []

    if paths is None:
        paths = []

    # leaf
    if not len(ds):
        paths.append(path)
        # print(paths[-1])
        return paths

    keys = ds.keys()
    if keys[0] == ':':
        keys = range(len(ids))
        if len(keys) and assume_uniform_array_structures:
            keys = [0]

    for kid in keys:
        propagate_path = copy.copy(path)
        propagate_path.append(kid)
        if isinstance(kid, basestring):
            subtree_paths = filled_paths_in_ids(getattr(ids, kid), ds[kid], propagate_path, [], uniform_array_structures)
        else:
            subtree_paths = filled_paths_in_ids(ids[kid], ds[':'], propagate_path, [], uniform_array_structures)
        paths += subtree_paths

        if assume_uniform_array_structures:
            zero_paths = subtree_paths
            for key in range(1, len(ids)):
                subtree_paths = copy.deepcopy(zero_paths)
                for p in subtree_paths:
                    p[len(path)] = key
                paths += subtree_paths

    return paths


def through_omas_imas(ods):
    """
    test save and load OMAS IMAS

    :param ods: ods

    :return: ods
    """
    user = os.environ['USER']
    machine = 'ITER'
    pulse = 1
    run = 0

    paths = save_omas_imas(ods, user=user, machine=machine, pulse=pulse, run=run, new=True)
    ods1 = load_omas_imas(user=user, machine=machine, pulse=pulse, run=run, paths=paths)
    return ods1
