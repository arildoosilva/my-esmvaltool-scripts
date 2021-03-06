"""
*********************************************************************
 AOS_mean_seasons.py
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

            first_year = nc_file[-12:-8]
            last_year = nc_file[-7:-3]

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

            for each_year in range(int(first_year), int(last_year)+1):
                seasons_dict = seasons(nc_files_path_list, each_year)

                if maps_flag:
                    for key in seasons_dict:
                        generate_map(seasons_dict[key], variable, key, each_year)
                    
                yearly_files = []
                for each_file in nc_files_path_list:
                    if str(each_year) in each_file:
                        yearly_files.append(each_file)
                if charts_flag:
                    generate_chart(yearly_files, variable, each_year)
        print("Finished variable: %s" % (variable))
    print("End of diag_scripts/" + os.path.basename(__file__))


def seasons(nc_files, year):
    summer = set()
    winter = set()
    spring = set()
    fall = set()
    summer_months = ["01", "02"]
    winter_months = ["06", "07", "08"]
    spring_months = ["09", "10", "11"]
    fall_months = ["03", "04", "05"]

    for each_file in nc_files:
        if str(year) in each_file:
            if str(each_file[-5:-3]) in summer_months:
                summer.add(each_file)
                if str(each_file[-5:-3]) == "01":
                    dec = each_file.replace(str(year) + "01", str(year-1) + "12")
                    if os.path.isfile(dec):
                        summer.add(dec)
            elif str(each_file[-5:-3]) in fall_months:
                fall.add(each_file)
            elif str(each_file[-5:-3]) in winter_months:
                winter.add(each_file)
            elif str(each_file[-5:-3]) in spring_months:
                spring.add(each_file)

    seasons_dict = {
        "Summer" : summer,
        "Spring" : spring,
        "Fall" : fall,
        "Winter" : winter
    }
    return seasons_dict


def generate_map(nc_files, variable, season, year):
    plt.clf()
    plt.cla()
    plt.close()
    plt.figure()
    nc_files = list(nc_files)
    print("Plotting map for model %s, var is %s (%s %d)" % (model, variable, season, year))
    lats, lons, level, units, long_name, standard_name, data, nyears, level_data, level_units = AOS_aux.processDataset(nc_files, variable)

    if level_units is None:
        avg = np.mean(data[:,:,:], axis=0)
    else:
        avg = np.mean(data[:,level,:,:], axis=0)
    avg = AOS_aux.processVar(variable, avg)

    avg, lons = shiftgrid(30.,avg,lons,start=True, cyclic=360.0)

    lon_0 = lons.mean()
    lat_0 = lats.mean()

    m = Basemap(resolution="l",projection="mill",lat_ts=40,lat_0=lat_0,lon_0=lon_0)
    lon, lat = np.meshgrid(lons, lats)
    xi, yi = m(lon, lat)

    cs = m.pcolor(xi, yi, np.squeeze(avg))

    m.drawparallels(np.arange(-180., 181., 30.), labels=[1,0,0,0], fontsize=10)  # -
    m.drawmeridians(np.arange(-180., 181., 45.), labels=[0,0,0,1], fontsize=10)  # |
    
    m.drawcoastlines()
    # m.drawstates()
    m.drawcountries()
    # m.fillcontinents(color='white')

    cbar = m.colorbar(cs, location='bottom', pad="5%")
    cbar.ax.tick_params(labelsize=10)

    plt.title(model + " - " + season + " " + str(year) + "\n" + ensemble + " - " + var_title)
    cbar.set_label(var_units)

    # saves the image in the namelist's 'PLOT_DIR' directory
    E.ensure_directory("/".join([PLOT_DIR, model, str(year), variable]))
    image_path = "".join([PLOT_DIR, "/", model, "/", str(year), "/", variable, "/", variable, "_", model, "_", season, str(year), "_map.png"])
    plt.savefig(image_path, orientation="landscape", dpi=100)
    print("Plot stored in: %s" % (image_path))


def generate_chart(nc_files, variable, year):
    plt.clf()
    print("Plotting chart %s for model %s year %d" % (variable, model, year))
    lats, lons, level, units, long_name, standard_name, data, nyears, level_data, level_units = AOS_aux.processDataset(nc_files, variable)
    var_array = np.zeros([nyears,len(lats),len(lons)], dtype='f4')
    val_by_month = []
    tick_locs = []
    tick_lbls = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    for idx, filename in enumerate(nc_files):
        ncfile = netCDF4.Dataset(filename, 'r')
        year = float(filename[-9:-5])
        month = float(filename[-5:-3])
        if level_units is None:
            var_data = ncfile.variables[variable][:,:,:]
        else:
            var_data = ncfile.variables[variable][:,level,:,:]
        var_array[idx,:,:] = np.mean(var_data, axis=1)
        val_by_month.append(AOS_aux.processVar(variable, np.mean(np.mean(var_data, axis=0))))
        tick_locs.append(year + (month * 0.05))
        ncfile.close()
    
    plt.margins(0.1)
    plt.plot(tick_locs, val_by_month, "b-", linewidth=2)
    plt.xticks(tick_locs, tick_lbls)

    plt.ylabel(var_units)
    
    plt.title(model + " - " + str(year).rstrip(".0") + "\n" + ensemble + " - " + var_title)
    
    # saves the image in the namelist's 'PLOT_DIR' directory
    E.ensure_directory("/".join([PLOT_DIR, model, str(year).rstrip(".0"), variable]))
    image_path = "".join([PLOT_DIR, "/", model, "/", str(year).rstrip(".0"), "/", variable, "/", variable, "_", model, "_", str(year).rstrip(".0"), "_chart.png"])
    plt.savefig(image_path, orientation="landscape", dpi=100)
    print("Chart stored in: %s" % (image_path))
