# # -*- coding: utf-8 -*-

"""
Miscellaneous utility and helper functions to support various tests in this folder.
"""

from __future__ import print_function, division, unicode_literals
import numpy

__all__ = []


def make_available(f):
    __all__.append(f.__name__)
    return f


@make_available
def add_eq_sample_data(ods):
    """
    Expands an ODS by adding a (heavily down-sampled) psi map to it with low precision. This function can overwrite
    existing data if you're not careful. The original is modified, so deepcopy first if you want different ODSs.

    :param ods: ODS instance

    :return: ODS instance with equilibrium data added
    """

    # These arrays were decimated to make them smaller; we don't need something nice looking for these tests and we
    # don't want to take up space storing huge arrays when little ones will do. Data originally from shot 173225.
    psi_small = numpy.array([
        [0.37, 0.22, 0.07, 0.07, 0.17, 0.15, 0.32, 0.63, 0.81, 1.01, 1.13],
        [0.29, 0.22, 0.24, 0.22, 0.25, 0.33, 0.49, 0.77, 1.08, 1.59, 1.83],
        [0.53, 0.43, 0.35, 0.26, 0.25, 0.3, 0.44, 0.74, 1.08, 1.72, 2.02],
        [0.75, 0.56, 0.35, 0.16, 0.03, -0.02, 0.09, 0.36, 0.74, 1.22, 1.69],
        [0.7, 0.51, 0.24, -0.06, -0.34, -0.53, -0.53, -0.26, 0.21, 0.84, 1.55],
        [0.72, 0.48, 0.14, -0.26, -0.67, -0.99, -1.08, -0.82, -0.31, 0.42, 1.02],
        [0.71, 0.47, 0.13, -0.27, -0.68, -1., -1.1, -0.85, -0.35, 0.35, 0.97],
        [0.62, 0.45, 0.21, -0.07, -0.33, -0.51, -0.52, -0.29, 0.14, 0.7, 1.31],
        [0.59, 0.48, 0.34, 0.2, 0.09, 0.05, 0.13, 0.38, 0.71, 1.17, 1.5],
        [0.48, 0.44, 0.43, 0.4, 0.42, 0.46, 0.58, 0.82, 1.11, 1.67, 1.9],
        [0.46, 0.44, 0.5, 0.55, 0.57, 0.61, 0.72, 0.9, 1.11, 1.46, 1.6],
    ])
    grid1_small = numpy.array([0.83, 0.99, 1.15, 1.3, 1.46, 1.62, 1.77, 1.94, 2.09, 2.25, 2.4])
    grid2_small = numpy.array([-1.58, -1.29, -0.99, -0.69, -0.39, -0.1, 0.2, 0.5, 0.79, 1.1, 1.38])
    bdry_r_small = numpy.array([1.08, 1.12, 1.27, 1.54, 1.82, 2.03, 2.2, 2.22, 2.07, 1.9, 1.68, 1.45, 1.29, 1.16, 1.1])
    bdry_z_small = numpy.array([1.00e-03, 5.24e-01, 8.36e-01, 9.42e-01, 8.37e-01, 6.49e-01, 3.46e-01, -9.38e-02,
                                -4.57e-01, -6.89e-01, -8.93e-01, -1.07e+00, -9.24e-01, -5.16e-01, -1.00e-01])
    wall_r_small = numpy.array([1.01, 1., 1.01, 1.09, 1.17, 1.2, 1.23, 1.31, 1.37, 1.36, 1.42, 1.5, 1.46, 1.54, 2.05,
                                2.41, 2.2, 1.64, 1.1, 1.03])
    wall_z_small = numpy.array([-0., 1.21, 1.12, 1.17, 1.19, 1.17, 1.29, 1.31, 1.32, 1.16, 1.18, 1.23, 1.1, 1.14, 0.81,
                                0.09, -0.59, -1.27, -1.3, -0.38])

    ods['equilibrium.time_slice.0.profiles_2d.0.psi'] = psi_small
    ods['equilibrium.time_slice.0.profiles_2d.0.grid.dim1'] = grid1_small
    ods['equilibrium.time_slice.0.profiles_2d.0.grid.dim2'] = grid2_small
    ods['equilibrium.time_slice.0.boundary.outline.r'] = bdry_r_small
    ods['equilibrium.time_slice.0.boundary.outline.z'] = bdry_z_small

    ods['equilibrium.time_slice.0.global_quantities.magnetic_axis.r'] = 1.77
    ods['equilibrium.time_slice.0.global_quantities.magnetic_axis.z'] = 0.05

    ods['wall.description_2d.0.limiter.unit.0.outline.r'] = wall_r_small
    ods['wall.description_2d.0.limiter.unit.0.outline.z'] = wall_z_small
    return ods


@make_available
def add_ts_sample_data(ods, nc=10):
    """
    Adds some FAKE Thomson scattering channel locations so that the overlay plot will work in tests. It's fine to test
    with dummy data as long as you know it's not real.

    :param ods: ODS instance

    :param nc: Number of channels to add.

    :return: ODS instance with FAKE THOMSON HARDWARE INFORMATION added.
    """

    r = numpy.linspace(1.935, 1.945, nc)
    z = numpy.linspace(-0.7, 0.2, nc)
    for i in range(nc):
        ch = ods['thomson_scattering.channel'][i]
        ch['identifier'] = 'F{:02d}'.format(i)  # F for fake
        ch['name'] = 'Fake Thomson channel for testing {}'.format(i)
        ch['position.phi'] = 6.5  # This angle in rad should look bad to someone who doesn't notice the Fake labels
        ch['position.r'] = r[i]
        ch['position.z'] = z[i]

    return ods


@make_available
def add_bolo_sample_data(ods, nc=10):
    """
    Adds some FAKE bolometer chord locations so that the overlay plot will work in tests. It's fine to test
    with dummy data as long as you know it's not real.

    :param ods: ODS instance

    :param nc: 10  # Number of fake channels to make up for testing

    :return: ODS instance with FAKE BOLOMETER HARDWARE INFORMATION added.
    """

    angles = numpy.pi + numpy.linspace(-numpy.pi/4.0, numpy.pi/4.0, nc)

    # FAKE origin for the FAKE bolometer fan
    r0 = 2.5
    z0 = 0.05

    for i in range(nc):
        ch = ods['bolometer.channel'][i]['line_of_sight']
        ch['first_point.r'] = r0
        ch['first_point.z'] = z0 + 0.001 * i
        ch['second_point.r'] = ch['first_point.r'] + numpy.cos(angles[i])
        ch['second_point.z'] = ch['first_point.z'] + numpy.sin(angles[i])
        ods['bolometer.channel'][i]['identifier'] = 'fake bolo {}'.format(i)

    return ods
