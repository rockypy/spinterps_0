'''
Created on May 27, 2019

@author: Faizan-Uni
'''

from pathlib import Path

import h5py
import numpy as np
import netCDF4 as nc

from ..misc import print_sl, print_el


class ExtractNetCDFCoords:

    _raster_type_lab = 'nc'

    def __init__(self, verbose=True):

        self._vb = verbose

        self._in_path = None
        self._x_crds_lab = None
        self._y_crds_lab = None
        self._x_crds = None
        self._y_crds = None

        self._set_in_flag = False
        self._set_crds_extrt_flag = False
        return

    def set_input(self, path_to_nc, x_crds_lab, y_crds_lab):

        assert isinstance(path_to_nc, (str, Path))

        assert isinstance(x_crds_lab, str)
        assert x_crds_lab

        assert isinstance(y_crds_lab, str)
        assert y_crds_lab

        path_to_nc = Path(path_to_nc).absolute()

        assert path_to_nc.exists()

        self._in_path = path_to_nc
        self._x_crds_lab = x_crds_lab
        self._y_crds_lab = y_crds_lab

        if self._vb:
            print_sl()

            print(f'INFO: Set the following parameters for the netCDF:')
            print(f'Path: {self._in_path}')
            print(f'X coordinates\' label: {self._x_crds_lab}')
            print(f'Y coordinates\' label: {self._y_crds_lab}')

            print_el()

        self._set_in_flag = True
        return

    def extract_coordinates(self):

        assert self._set_in_flag

        in_hdl = nc.Dataset(str(self._in_path))

        assert self._x_crds_lab in in_hdl.variables
        assert self._y_crds_lab in in_hdl.variables

        self._x_crds = in_hdl[self._x_crds_lab][...]
        self._y_crds = in_hdl[self._y_crds_lab][...]

        assert np.all(self._x_crds.shape)
        assert np.all(self._y_crds.shape)

        if isinstance(self._x_crds, np.ma.MaskedArray):
            self._x_crds = self._x_crds.data
            self._y_crds = self._y_crds.data

            if self._vb:
                print_sl()

                print(
                    f'INFO: X and coordinates array were masked. '
                    f'Took the "data" attribute!')

                print_el()

        elif (isinstance(self._x_crds, np.ndarray) and
              isinstance(self._y_crds, np.ndarray)):
            pass

        else:
            raise NotImplementedError

        assert np.all(np.isfinite(self._x_crds))
        assert np.all(np.isfinite(self._y_crds))

        assert self._x_crds.ndim == 1
        assert self._x_crds.ndim == self._y_crds.ndim

        if self._vb:
            print_sl()

            print(f'INFO: netCDF coordinates\' properties:')
            print(f'Dimensions of coordinates: {self._x_crds.ndim}')
            print(f'Shape of X coordinates: {self._x_crds.shape}')
            print(f'Shape of Y coordinates: {self._y_crds.shape}')

            print_el()

        in_hdl.close()
        in_hdl = None

        self._set_crds_extrt_flag = True
        return

    def get_x_coordinates(self):

        assert self._set_crds_extrt_flag

        return self._x_crds

    def get_y_coordinates(self):

        assert self._set_crds_extrt_flag

        return self._y_crds


class ExtractNetCDFValues:

    def __init__(self, verbose=True):

        self._vb = verbose

        self._in_path = None
        self._in_var_lab = None
        self._in_time_lab = None

        self._out_path = None
        self._out_fmt = None

        self._set_in_flag = False
        self._set_out_flag = False
        self._set_data_extrt_flag = False
        return

    def set_input(self, path_to_nc, variable_label, time_label):

        assert isinstance(path_to_nc, (str, Path))

        assert isinstance(variable_label, str)
        assert variable_label

        assert isinstance(time_label, str)
        assert time_label

        path_to_nc = Path(path_to_nc).absolute()

        assert path_to_nc.exists()

        self._in_path = path_to_nc
        self._in_var_lab = variable_label
        self._in_time_lab = time_label

        if self._vb:
            print_sl()

            print(f'INFO: Set the following parameters for the netCDF:')
            print(f'Path: {self._in_path}')
            print(f'Variable label: {self._in_var_lab}')
            print(f'Time label: {self._in_time_lab}')

            print_el()

        self._set_in_flag = True
        return

    def set_output(self, path_to_output):

        if path_to_output is None:
            self._out_fmt = 'raw'

        else:
            assert isinstance(path_to_output, (str, Path))

            path_to_output = Path(path_to_output).absolute()

            assert path_to_output.parents[0].exists()

            fmt = path_to_output.suffix

            if fmt in ('.h5', '.hdf5'):
                self._out_fmt = 'h5'

            else:
                raise NotImplementedError

        self._out_path = path_to_output

        if self._vb:
            print_sl()

            print(f'INFO: Set the following parameters for the output:')
            print(f'Path: {self._out_path}')
            print(f'Format: {self._out_fmt}')

            print_el()

        self._set_out_flag = True
        return

    def extract_data_for_indicies(self, indicies):

        assert self._set_in_flag
        assert self._set_out_flag

        assert isinstance(indicies, dict)
        assert indicies

        in_hdl = nc.Dataset(str(self._in_path))

        assert self._in_var_lab in in_hdl.variables
        assert self._in_time_lab in in_hdl.variables

        # memory manage?
        in_var = in_hdl[self._in_var_lab]
        in_var.set_always_mask(False)

        assert in_var.ndim == 3
        assert in_var.size > 0
        assert all(in_var.shape)

        in_time = in_hdl[self._in_time_lab]
        in_time.set_always_mask(False)

        assert in_time.ndim == 1
        assert in_time.size > 0

        assert in_time.shape[0] == in_var.shape[0]

        if self._out_fmt == 'h5':
            out_hdl = h5py.File(str(self._out_path), mode='w', driver=None)

            out_time_grp = out_hdl.create_group(self._in_time_lab)
            out_time_grp[self._in_time_lab] = in_time[...]

            if hasattr(in_time, 'units'):
                out_time_grp.attrs['units'] = in_time.units

            if hasattr(in_time, 'calendar'):
                out_time_grp.attrs['calendar'] = in_time.calendar

            out_var_grp = out_hdl.create_group(self._in_var_lab)

            if hasattr(in_var, 'units'):
                out_var_grp.attrs['units'] = in_var.units

        elif self._out_fmt == 'raw':
            extrt_data = {}

        else:
            raise NotImplementedError

        if self._vb:
            print_sl()

            print(f'INFO: Input netCDF variable\'s properties:')
            print(f'Dimensions of variable: {in_var.ndim}')
            print(f'Shape of variable: {in_var.shape}')
            print(f'Shape of time: {in_time.shape}')

            print_el()

        in_var_data = in_var[...]

        for label, crds_idxs in indicies.items():
            x_crds_idxs = crds_idxs['x']
            assert x_crds_idxs.ndim == 1
            assert x_crds_idxs.size > 0

            x_crds_idxs_min = x_crds_idxs.min()
            x_crds_idxs_max = x_crds_idxs.max()
            assert (x_crds_idxs_max > 0) & (x_crds_idxs_min > 0)

            y_crds_idxs = crds_idxs['y']
            assert y_crds_idxs.ndim == 1
            assert y_crds_idxs.size > 0

            y_crds_idxs_min = y_crds_idxs.min()
            y_crds_idxs_max = y_crds_idxs.max()
            assert (y_crds_idxs_max > 0) & (y_crds_idxs_min > 0)

            assert x_crds_idxs.shape == y_crds_idxs.shape

            assert y_crds_idxs_max < in_var_data.shape[1]
            assert x_crds_idxs_max < in_var_data.shape[2]

            if self._out_fmt == 'raw':
                steps_data = {}

                for i in range(in_time.shape[0]):
                    step = in_time[i].item()
                    step_data = in_var_data[i, y_crds_idxs, x_crds_idxs]

                    steps_data[step] = step_data

                assert steps_data

                extrt_data[label] = steps_data

            elif self._out_fmt == 'h5':
                label_var = out_var_grp.create_group(str(label))
                label_var['columns'] = x_crds_idxs
                label_var['rows'] = y_crds_idxs
                label_var['data'] = in_var_data[:, y_crds_idxs, x_crds_idxs]

                out_hdl.flush()

            else:
                raise NotImplementedError

        if self._out_fmt == 'raw':
            assert extrt_data
            self._extrt_data = extrt_data

        in_hdl.close()
        in_hdl = None

        if self._out_fmt == 'h5':
            out_hdl.flush()
            out_hdl.close()
            out_hdl = None

        self._set_data_extrt_flag = True
        return

    def get_extracted_data(self):

        assert self._out_fmt == 'raw'

        assert self._set_data_extrt_flag

        assert self._extrt_data is not None

        return self._extrt_data
