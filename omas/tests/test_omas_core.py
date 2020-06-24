#!/usr/bin/env python
# # -*- coding: utf-8 -*-

"""
Test script for omas/omas_core.py

.. code-block:: none

   python3 -m unittest omas/tests/test_omas_core

-------
"""

import unittest
import os
import numpy
from pprint import pprint

# OMAS imports
from omas import *
from omas.omas_setup import *
from omas.tests import warning_setup


class TestOmasCore(unittest.TestCase):
    """
    Test suite for omas_core.py
    """

    def test_misc(self):
        ods = ODS()
        # check effect of disabling dynamic path creation
        try:
            ods.dynamic_path_creation = False
            ods['dataset_description.data_entry.user']
        except LookupError:
            ods['dataset_description'] = ODS()
            ods['dataset_description.data_entry.user'] = os.environ.get('USER', 'dummy_user')
        else:
            raise Exception('OMAS error handling dynamic_path_creation=False')
        finally:
            ods.dynamic_path_creation = True

        # check that accessing leaf that has not been set raises a ValueError, even with dynamic path creation turned on
        try:
            ods['dataset_description.data_entry.machine']
        except ValueError:
            pass
        else:
            raise Exception('OMAS error querying leaf that has not been set')

        # info ODS is used for keeping track of IMAS metadata
        ods['dataset_description.data_entry.machine'] = 'ITER'
        ods['dataset_description.imas_version'] = omas_rcparams['default_imas_version']
        ods['dataset_description.data_entry.pulse'] = 1
        ods['dataset_description.data_entry.run'] = 0

        # check .get() method
        assert (ods.get('dataset_description.data_entry.pulse') == ods['dataset_description.data_entry.pulse'])
        assert (ods.get('dataset_description.bad', None) is None)

        # check that keys is an iterable
        keys = ods.keys()
        keys[0]

        # check that dynamic path creation during __getitem__ does not leave empty fields behind
        try:
            print(ods['wall.description_2d.0.limiter.unit.0.outline.r'])
        except ValueError:
            assert 'wall.description_2d.0.limiter.unit.0.outline' not in ods

        ods['equilibrium']['time_slice'][0]['time'] = 1000.
        ods['equilibrium']['time_slice'][0]['global_quantities']['ip'] = 1.5

        ods2 = copy.deepcopy(ods)
        ods2['equilibrium']['time_slice'][1] = ods['equilibrium']['time_slice'][0]
        ods2['equilibrium.time_slice.1.time'] = 2000.

        ods2['equilibrium']['time_slice'][2] = copy.deepcopy(ods['equilibrium']['time_slice'][0])
        ods2['equilibrium.time_slice[2].time'] = 3000.

        assert (ods2['equilibrium']['time_slice'][0]['global_quantities'].ulocation == ods2['equilibrium']['time_slice'][2]['global_quantities'].ulocation)

        ods2['equilibrium.time_slice.1.global_quantities.ip'] = 2.

        # check different ways of addressing data
        for item in [ods2['equilibrium.time_slice']['1.global_quantities'],
                     ods2[['equilibrium', 'time_slice', 1, 'global_quantities']],
                     ods2[('equilibrium', 'time_slice', 1, 'global_quantities')],
                     ods2['equilibrium.time_slice.1.global_quantities'],
                     ods2['equilibrium.time_slice[1].global_quantities']]:
            assert item.ulocation == 'equilibrium.time_slice.:.global_quantities'

        ods2['equilibrium.time_slice.0.profiles_1d.psi'] = numpy.linspace(0, 1, 10)

        # check data slicing
        assert numpy.all(ods2['equilibrium.time_slice[:].global_quantities.ip'] == numpy.array([1.5, 2.0, 1.5]))

        # uncertain scalar
        ods2['equilibrium.time_slice[2].global_quantities.ip'] = ufloat(3, 0.1)

        # uncertain array
        ods2['equilibrium.time_slice[2].profiles_1d.q'] = uarray([0., 1., 2., 3.], [0, .1, .2, .3])

        ckbkp = ods.consistency_check
        tmp = pickle.dumps(ods2)
        ods2 = pickle.loads(tmp)
        if ods2.consistency_check != ckbkp:
            raise Exception('consistency_check attribute changed')

        # check flattening
        tmp = ods2.flat()
        # pprint(tmp)

        # check deepcopy
        ods3 = ods2.copy()

        # check writing setting an xarray.DataArray
        ods2['equilibrium.time_slice[2].profiles_1d.q'] = xarray.DataArray(
            uarray([0., 1., 2., 3.], [0, .1, .2, .3]), coords={'x': [1, 2, 3, 4]}, dims=['x']
        )
        return

    def test_dynamic_set_nonzero_array_index(self):
        ods = ODS()
        ods.consistency_check = False
        ods.dynamic_path_creation = True
        self.assertRaises(IndexError, ods.__setitem__, 'something[10]', 5)
        return

    def test_coordinates(self):
        ods = ods_sample()
        assert (len(ods.list_coordinates()) > 0)
        assert (len(ods['equilibrium'].list_coordinates()) > 0)
        return

    def test_dataset(self):
        ods = ODS()

        ods.sample_equilibrium(time_index=0)
        ods.sample_equilibrium(time_index=1)

        ods.sample_core_profiles(time_index=0)
        ods.sample_core_profiles(time_index=1)

        n = 1E10
        sizes = {}
        for homogeneous in [False, 'time', None, 'full']:
            DS = ods.dataset(homogeneous=homogeneous)
            print(homogeneous, len(DS.variables))
            sizes[homogeneous] = len(DS.variables)
            if homogeneous is not None:
                assert n >= sizes[homogeneous], 'homogeneity setting does not match structure reduction expectation'
                n = sizes[homogeneous]
        assert sizes[None] == sizes['time'], 'sample equilibrium and core_profiles should be homogeneous'

        ods.sample_pf_active()
        try:
            DS = ods.dataset(homogeneous='full')
            raise AssertionError('sample pf_active data should not be able to collect across channels because their time arrays are not homogeneous')
        except ValueError:
            pass
        return

    def test_time(self):
        # test generation of a sample ods
        ods = ODS()
        ods['equilibrium.time_slice'][0]['time'] = 100
        ods['equilibrium.time_slice.0.global_quantities.ip'] = 0.0
        ods['equilibrium.time_slice'][1]['time'] = 200
        ods['equilibrium.time_slice.1.global_quantities.ip'] = 1.0
        ods['equilibrium.time_slice'][2]['time'] = 300
        ods['equilibrium.time_slice.2.global_quantities.ip'] = 2.0

        # get time information from children
        extra_info = {}
        assert numpy.allclose(ods.time('equilibrium'), [100, 200, 300])
        assert ods['equilibrium'].homogeneous_time() is True

        # time arrays can be set using `set_time_array` function
        # this simplifies the logic in the code since one does not
        # have to check if the array was already there or not
        ods.set_time_array('equilibrium.time', 0, 101)
        ods.set_time_array('equilibrium.time', 1, 201)
        ods.set_time_array('equilibrium.time', 2, 302)

        # the make the timeslices consistent
        ods['equilibrium.time_slice'][0]['time'] = 101
        ods['equilibrium.time_slice'][1]['time'] = 201
        ods['equilibrium.time_slice'][2]['time'] = 302

        # get time information from explicitly set time array
        extra_info = {}
        assert numpy.allclose(ods.time('equilibrium'), [101, 201, 302])
        assert numpy.allclose(ods.time('equilibrium.time_slice'), [101, 201, 302])
        assert numpy.allclose(ods['equilibrium'].time('time_slice'), [101, 201, 302])
        assert ods['equilibrium'].homogeneous_time() is True

        # get time value from a single item in array of structures
        extra_info = {}
        assert ods['equilibrium.time_slice'][0].time() == 101
        assert ods['equilibrium'].time('time_slice.0') == 101
        assert ods['equilibrium.time_slice'][0].homogeneous_time() is True

        # sample pf_active data has non-homogeneous times
        ods.sample_pf_active()
        assert ods['pf_active'].homogeneous_time() is False, 'sample pf_active data should have non-homogeneous time'
        assert ods['pf_active.coil'][0]['current'].homogeneous_time() is True

        ods.sample_dataset_description()
        ods['dataset_description'].satisfy_imas_requirements()
        assert ods['dataset_description.ids_properties.homogeneous_time'] is not None
        return

    def test_dynamic_set_existing_list_nonzero_array_index(self):
        ods = ODS()
        ods.consistency_check = False
        ods.dynamic_path_creation = 'dynamic_array_structures'
        ods['something[0]'] = 5
        ods['something[7]'] = 10
        assert ods['something[0]'] == 5
        assert ods['something[7]'] == 10
        return

    def test_set_nonexisting_array_index(self):
        ods = ODS()
        ods.consistency_check = False
        ods.dynamic_path_creation = False
        self.assertRaises(IndexError, ods.__setitem__, 'something.[10]', 5)
        return

    def test_force_type(self):
        ods = ODS()
        ods['core_profiles.profiles_1d'][0]['ion'][0]['z_ion'] = 1
        assert isinstance(ods['core_profiles.profiles_1d'][0]['ion'][0]['z_ion'], float)
        return

    def test_address_structures(self):
        ods = ODS()

        # make sure data structure is of the right type
        assert isinstance(ods['core_transport'].omas_data, dict)
        assert isinstance(ods['core_transport.model'].omas_data, list)

        # append elements by using `+`
        for k in range(10):
            ods['equilibrium.time_slice.+.global_quantities.ip'] = k
        assert len(ods['equilibrium.time_slice']) == 10
        assert (ods['equilibrium.time_slice'][9]['global_quantities.ip'] == 9)

        # access element by using negative indices
        assert (ods['equilibrium.time_slice'][-1]['global_quantities.ip'] == 9)
        assert (ods['equilibrium.time_slice.-10.global_quantities.ip'] == 0)

        # set element by using negative indices
        ods['equilibrium.time_slice.-1.global_quantities.ip'] = -99
        ods['equilibrium.time_slice'][-10]['global_quantities.ip'] = -100
        assert (ods['equilibrium.time_slice'][-1]['global_quantities.ip'] == -99)
        assert (ods['equilibrium.time_slice'][-10]['global_quantities.ip'] == -100)

        # access by pattern
        assert (ods['@eq.*1.*.ip'] == 1)
        return

    def test_version(self):
        ods = ODS(imas_version='3.20.0')
        ods['ec_antennas.antenna.0.power.data'] = [1.0]

        try:
            ods = ODS(imas_version='3.21.0')
            ods['ec_antennas.antenna.0.power.data'] = [1.0]
            raise AssertionError('3.21.0 should not have `ec_antennas.antenna.0.power`')
        except LookupError:
            pass

        # check support for development version is there
        ODS(imas_version='develop.3')

        try:
            tmp = ODS(imas_version='does_not_exist')
        except ValueError:
            pass
        return

    def test_satisfy_imas_requirements(self):
        ods = ODS()
        ods['equilibrium.time_slice.0.global_quantities.ip'] = 0.0
        # check if data structures satisfy IMAS requirements (this should Fail)
        try:
            ods.satisfy_imas_requirements()
            raise ValueError('It is expected that not all the sample structures have the .time array set')
        except ValueError as _excp:
            pass

        ods = ods_sample()

        # re-check if data structures satisfy IMAS requirements (this should pass)
        ods.satisfy_imas_requirements()
        return

    def test_deepcopy(self):
        ods = ods_sample()

        # inject non-consistent data
        ods.consistency_check = False
        ods['bla'] = ODS(consistency_check=False)
        ods['bla.tra'] = 1
        try:
            # this should fail
            ods.consistency_check = True
        except LookupError:
            assert not ods.consistency_check

        # deepcopy should not raise a consistency_check error
        # since we are directly manipulating the __dict__ attributes
        import copy
        ods1 = copy.deepcopy(ods)

        # make sure non-consistent data got also copied over
        assert ods1['bla'] == ods['bla']

        # make sure the deepcopy is not shallow
        ods1['equilibrium.vacuum_toroidal_field.r0'] += 1
        assert ods['equilibrium.vacuum_toroidal_field.r0'] + 1 == ods1['equilibrium.vacuum_toroidal_field.r0']

        # deepcopy using .copy() method
        ods2 = ods.copy()

        # make sure the deepcopy is not shallow
        ods2['equilibrium.vacuum_toroidal_field.r0'] += 1
        assert ods['equilibrium.vacuum_toroidal_field.r0'] + 1 == ods2['equilibrium.vacuum_toroidal_field.r0']
        return

    def test_saveload(self):
        ods = ODS()
        ods.sample_equilibrium()
        ods.save('test.pkl')

    def test_input_data_process_functions(self):
        def robust_eval(string):
            import ast
            try:
                return ast.literal_eval(string)
            except:
                return string

        ods = ODS(consistency_check=False)
        with omas_environment(ods, input_data_process_functions=[robust_eval]):
            ods['int'] = '1'
            ods['float'] = '1.0'
            ods['str'] = 'bla'
            ods['complex'] = '2+1j'
        for item in ods:
            assert isinstance(ods[item], eval(item))
        return

    def test_conversion_after_assignement(self):
        ods = ODS(consistency_check=False)
        ods['bla'] = 5
        try:
            ods[0] = 4
            raise AssertionError('Convertion of dict to list should not be allowed')
        except TypeError:
            pass

        del ods['bla']
        ods[0] = 4
        try:
            ods['bla'] = 5
            raise AssertionError('Convertion of list to dict should not be allowed')
        except TypeError:
            pass
        return

    def test_codeparameters(self):
        ods = ODS()
        ods['equilibrium.code.parameters'] = CodeParameters(imas_json_dir + '/../samples/input_gray.xml')

        tmp = {}
        tmp.update(ods['equilibrium.code.parameters'])
        ods['equilibrium.code.parameters'] = tmp
        assert isinstance(ods['equilibrium.code.parameters'], CodeParameters)

        with omas_environment(ods, xmlcodeparams=True):
            assert isinstance(ods['equilibrium.code.parameters'], str)
        assert isinstance(ods['equilibrium.code.parameters'], CodeParameters)

        # test that dynamic creation of .code.parameters makes it a CodeParameters object
        ods = ODS()
        ods['equilibrium.code.parameters']['param1'] = 1
        assert isinstance(ods['equilibrium.code.parameters'], CodeParameters)

        # test saving of code_parameters in json format
        ods.save(tempfile.gettempdir() + '/ods_w_codeparams.json')

        # test that loading of data with code.parameters results in a CodeParameters object
        ods = ODS()
        ods.load(tempfile.gettempdir() + '/ods_w_codeparams.json')
        assert isinstance(ods['equilibrium.code.parameters'], CodeParameters)

        # test loading CodeParameters from a json
        ods = ODS().load(imas_json_dir + '/../samples/ods_w_code_parameters.json')
        # test traversing ODS and code parameters with OMAS syntax
        assert ods['ec_launchers.code.parameters.launcher.0.mharm'] == 2
        # test that sub-tree elements of code parameters are also of CodeParameters class
        assert isinstance(ods['ec_launchers.code.parameters.launcher'], CodeParameters)
        # test to_string and from_string methods
        with omas_environment(ods, xmlcodeparams=True):
            code_parameters_string = ods['ec_launchers.code.parameters']
            tmp = CodeParameters().from_string(code_parameters_string)
            assert isinstance(tmp['launcher'], CodeParameters)
            assert tmp['launcher.0.mharm'] == 2
        # test that CodeParameters are restored after xmlcodeparams=True environment
        assert isinstance(ods['ec_launchers.code.parameters'], CodeParameters)
        assert isinstance(ods['ec_launchers.code.parameters.launcher'], CodeParameters)
        assert isinstance(ods['ec_launchers.code.parameters.launcher.0'], CodeParameters)
        assert len(ods['ec_launchers.code.parameters.launcher.0']) == 2
        return

    # End of TestOmasCore class


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestOmasCore)
    unittest.TextTestRunner(verbosity=2).run(suite)
