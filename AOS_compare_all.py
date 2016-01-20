"""
*********************************************************************
 AOS_compare_all.py
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
import numpy as np
import sys
import re
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/aux/AOS")
import AOS_aux
import random

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
charts_flag = True  # plot charts
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

    if charts_flag is False:
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

        plt.figure(figsize=(20,7))
        """ Loops through each Model from the namelist
        """
        for nc_model, nc_file in model_filenames.items():
            print("Current model: %s" % (nc_model))
            print("Current filename is: %s" % (nc_file))
            nc_var = netCDF4.Dataset(nc_file, mode="r")
            
            if nc_file[-7:-3] == nc_file[-12:-8]:
                proc_years = nc_file[-12:-8]
            else:
                proc_years = nc_file[-12:-3]
            
            model = nc_model
            ensemble = AOS_aux.extract_ensemble(nc_file)

            """ Loops through each netcdf file from the model,
            appends the file path to a list
            """
            nc_files_path_list = []
            for x in range(0, 9999):
                try:
                    nc_files_path_list.append(nc_var.getncattr("infile_%s" % (str(x).zfill(4)))) 
                except:
                    break
            nc_var.close()
            if charts_flag:
                generate_chart(nc_files_path_list, variable)
        plt.legend(loc='best', shadow=False, fontsize='large', frameon=False)

        # saves the image in the namelist's 'PLOT_DIR' directory
        E.ensure_directory(PLOT_DIR)
        image_path = "".join([PLOT_DIR, "/", variable, "_comparison_chart.png"])
        plt.savefig(image_path, orientation="landscape", dpi=100)
        print("Chart stored in: %s" % (image_path))
        print("Finished variable: %s" % (variable))
    print("End of diag_scripts/" + os.path.basename(__file__))


def generate_chart(nc_files, variable):
    print("Plotting %s in chart (%s)" % (model, variable))
    lats, lons, level, units, long_name, standard_name, data, nyears, level_data, level_units = AOS_aux.processDataset(nc_files, variable)
    var_array = np.zeros([nyears,len(lats),len(lons)], dtype='f4')
    val_by_month = []
    tick_locs = []
    tick_lbls = []

    r = lambda: random.randint(0,255)
    color = '#%02X%02X%02X' % (r(),r(),r())

    for idx, filename in enumerate(nc_files):
        ncfile = netCDF4.Dataset(filename, 'r')
        year = float(filename[-9:-5])
        month = float(filename[-5:-3])
        if level_units is None:
            var_data = ncfile.variables[variable][:,:,:]
        else:
            var_data = ncfile.variables[variable][:,level,:,:]
        var_array[idx,:,:] = np.mean(var_data, axis=0)
        val_by_month.append(AOS_aux.processVar(variable, np.mean(np.mean(var_data, axis=0))))
        if month == 1.0:
            tick_lbls.append(filename[-9:-5])
        else:
            tick_lbls.append(" ")
        tick_locs.append(year + (month * 0.05))
        ncfile.close()
    
    plt.margins(0.05)
    plt.plot(tick_locs, val_by_month, color, label=("/".join([model, ensemble])), linewidth=2)
    plt.xticks(tick_locs, tick_lbls)

    plt.ylabel(var_units)
    
    plt.title(proc_years + " - " + var_title)
