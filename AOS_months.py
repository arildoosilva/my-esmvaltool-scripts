"""
*********************************************************************
 AOS_months.py
 arildo.o.s@outlook.com, November 2015

 Required diag_script_info attributes
 plot_dir: where the plots will be stored

 Required variable_info attributes
 title: variable title
 units: variable units

 Modification history
 20151128: written
*********************************************************************
"""

from esmval_lib import ESMValProject
import netCDF4
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from mpl_toolkits.basemap import shiftgrid
import numpy as np
import sys
import re
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/aux/AOS")
import AOS_aux

# Initializing global variables
PLOT_DIR = None
model = None
E = None
var_def_file = None
var_title = None
var_units = None
proc_years = None
ensemble = None

""" Change these to True or False to set what to do
"""
maps_flag = True  # plot maps
help_flag = False  # shows ESMValTool help and exit

def main(project_info):
    if help_flag:
        help(ESMValProject)
        sys.exit()
    global PLOT_DIR
    global model
    global E
    global var_def_file
    global var_title
    global var_units
    global proc_years
    global ensemble
    print("Starting diag_scripts/" + os.path.basename(__file__))

    # create instance of a wrapper that allows easy access to data
    E = ESMValProject(project_info)

    if maps_flag is False and charts_flag is False:
        print("Nothing to do")
        sys.exit()

    DATAKEYS = E.get_currVars()  # lat, lon, time, ...
    PLOT_DIR = E.get_plot_dir()
    # VERBOSITY = E.get_verbosity()

    for variable in DATAKEYS:
        print("Current variable: %s" % (variable))

        try:
            with open("".join(["variable_defs/", variable, ".ncl"]), "r") as var_def_file:
                for line in var_def_file.readlines():
                    if "variable_info@title" in line and ";" not in line:
                        var_title = AOS_aux.extract_defs(line)
                    elif "variable_info@units" in line and ";" not in line:
                        var_units = AOS_aux.extract_defs(line)
        except IOError:
            print("".join(["variable_defs/", variable, ".ncl not found."]))
            sys.exit()

        # get filenames of preprocessed climatological mean files
        model_filenames = E.get_clim_model_filenames(variable=variable, monthly=True)

        """ Loops through each year
        """
        for nc_model, nc_file in model_filenames.items():
            first_year = nc_file[-12:-8]
            last_year = nc_file[-7:-3]
            break

        for each_year in range(int(first_year), int(last_year)+1):
            print("Current year: %s" % (each_year))

            for nc_model, nc_file in model_filenames.items():
                print("Current model: %s" % (nc_model))
                print("Current filename is: %s" % (nc_file))
                nc_var = netCDF4.Dataset(nc_file, mode="r")
                model = nc_model
                ensemble = AOS_aux.extract_ensemble(nc_file)

                """ Loops through each netcdf file from the model,
                appends the file path to a list of files by year
                """
                yearly_files = []
                for x in range(0, 9999):
                    try:
                        if str(each_year) in str(nc_var.getncattr("infile_%s" % (str(x).zfill(4))))[-9:-5]:
                            yearly_files.append(nc_var.getncattr("infile_%s" % (str(x).zfill(4))))
                    except:
                        break
                nc_var.close()

                if maps_flag:
                    generate_map(yearly_files, variable, each_year)
        print("Finished variable: %s" % (variable))
    print("End of diag_scripts/" + os.path.basename(__file__))


def generate_map(nc_files, variable, year):
    plt.clf()
    plt.cla()
    plt.close()
    plt.figure(figsize=(50, 160))

    print("Plotting map %s for model %s" % (variable, model))
    lats, lons, level, units, long_name, standard_name, data, nyears, level_data, level_units = AOS_aux.processDataset(nc_files, variable)
    var_array = np.zeros([nyears,len(lats),len(lons)], dtype='f4')

    number_of_subplots = len(nc_files)

    months = dict({1: "Jan",
                   2: "Feb",
                   3: "Mar",
                   4: "Apr",
                   5: "May",
                   6: "Jun",
                   7: "Jul",
                   8: "Aug",
                   9: "Sep",
                   10: "Oct",
                   11: "Nov",
                   12: "Dec"})

    array_min = None
    array_max = None

    for idx, filename in enumerate(nc_files):
        ncfile = netCDF4.Dataset(filename, 'r')
        if level_units is None:
            var_data = ncfile.variables[variable][:,:,:]
        else:
            var_data = ncfile.variables[variable][:,level,:,:]

        var_data = AOS_aux.processVar(variable, var_data)

        var_array[:,:,:] = np.mean(var_data, axis=0)

        if array_min == None:
            array_min = np.min(var_array)

        if array_max == None:
            array_max = np.max(var_array)

        if np.min(var_array) < array_min:
            array_min = np.min(var_array)

        if np.max(var_array) > array_max:
            array_max = np.max(var_array)

    for idx, filename in enumerate(nc_files):
        ncfile = netCDF4.Dataset(filename, 'r')
        month = months[int(filename[-5:-3])]
        if level_units is None:
            var_data = ncfile.variables[variable][:,:,:]
        else:
            var_data = ncfile.variables[variable][:,level,:,:]

        var_data = AOS_aux.processVar(variable, var_data)

        var_array = np.zeros([1,len(lats),len(lons)], dtype='f4')
        var_array[:,:,:] = np.mean(var_data, axis=0)

        ncfile.close()

        ax1 = plt.subplot(number_of_subplots,3,idx+1)
        ax1.set(adjustable='box', aspect='equal')
        ax1.set_title(" ".join([long_name, model, month, str(year)]))

        avg = np.mean(var_array, axis=0)

        avg, lons = shiftgrid(30.,avg,lons,start=True, cyclic=360.0)

        lon_0 = lons.mean()
        lat_0 = lats.mean()

        m = Basemap(resolution="l",projection="mill",lat_ts=40,lat_0=lat_0,lon_0=lon_0)
        lon, lat = np.meshgrid(lons, lats)
        xi, yi = m(lon, lat)

        cs = m.pcolor(xi, yi, np.squeeze(avg), vmin=array_min, vmax=array_max)

        m.drawparallels(np.arange(-180., 181., 30.), labels=[1,0,0,0], fontsize=10)  # -
        m.drawmeridians(np.arange(-180., 181., 45.), labels=[0,0,0,1], fontsize=10)  # |
        m.drawcoastlines()
        m.drawcountries()

        cbar = m.colorbar(cs, location='bottom', pad="5%")
        cbar.ax.tick_params(labelsize=10)
        cbar.set_label(var_units)

        ax1.plot()

    # saves the image in the namelist's 'PLOT_DIR' directory
    E.ensure_directory(PLOT_DIR + "/" + model + "/" + str(year) + "/" + variable)
    image_path = "".join([PLOT_DIR, "/", model, "/", str(year), "/", variable, "/", variable, "_", model, "_", str(year), "_months.png"])
    plt.savefig(image_path, orientation="landscape", dpi=200, bbox_inches="tight")
    print("Plot stored in: %s" % (image_path))
