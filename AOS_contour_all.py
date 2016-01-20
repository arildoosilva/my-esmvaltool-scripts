"""
*********************************************************************
 AOS_contour_all.py
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
contour_flag = True  # plot contours
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

    if contour_flag is False:
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
            if contour_flag:
                generate_contour(nc_files_path_list, variable)
        print("Finished variable: %s" % (variable))
    print("End of diag_scripts/" + os.path.basename(__file__))


def generate_contour(nc_files, variable):
    plt.clf()
    plt.cla()
    plt.close()
    print("Plotting contour %s for model %s" % (variable, model))
    lats, lons, level, units, long_name, standard_name, data, nyears, level_data, level_units = AOS_aux.processDataset(nc_files, variable)

    if level_units is None:
        print("Cannot plot contour for a variable that doesn't have levels")
    else:
        level_units, level_data = AOS_aux.processPlev(level_units, level_data)

        data = np.mean(data, axis=0)
        data = np.mean(data, axis=2)
        data = AOS_aux.processVar(variable, data)

        CS = plt.contour(lats, level_data[::1], np.squeeze(data))
        plt.clabel(CS, inline=1, fontsize=10)

        plt.title(model + " - " + proc_years + " mean\n" + ensemble + " - " + var_title)
        plt.xlabel("lat")
        plt.ylabel("level (" + level_units + ")")
        locs, labels = plt.xticks()

        plt.xticks(locs, ('South Pole', '', 'EQ', '', 'North Pole'))

        plt.gca().invert_yaxis()

        # saves the image in the namelist's 'PLOT_DIR' directory
        E.ensure_directory(PLOT_DIR + "/" + model)
        image_path = "".join([PLOT_DIR, "/", model, "/", variable, "_", model, "_contour.png"])
        plt.savefig(image_path, orientation="landscape", dpi=100)
        print("Contour stored in: %s" % (image_path))
