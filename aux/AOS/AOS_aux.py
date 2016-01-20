import netCDF4
import re

def processVar(name, data):
    print("<<<<<<<<<<<< Entering BESM_aux.py processVar() (diag_scripts/aux/BESM)")

    if name == "pr" or name == "evspsbl":  # converts to mm/day
        data = data * 86400
       
    print(">>>>>>>>>>>> Leaving BESM_aux.py processVar() (diag_scripts/aux/BESM)")
    return data


def processLevel(name, data):
    print("<<<<<<<<<<<< Entering BESM_aux.py processLevel() (diag_scripts/aux/BESM)")
    level = 0

    if name == "wap":  # finds which level is 500hPa
        for x in range(0, len(data)):
            if data[x] == 50000.0:
                level = x + 1
                break
    
    print(">>>>>>>>>>>> Leaving BESM_aux.py processLevel() (diag_scripts/aux/BESM)")
    return level


def processPlev(name, level):
    print("<<<<<<<<<<<< Entering BESM_aux.py processPlev() (diag_scripts/aux/BESM)")

    if name == "Pa":
        level = level / 100
        name = "hPa"

    print(">>>>>>>>>>>> Leaving BESM_aux.py processPlev() (diag_scripts/aux/BESM)")
    return name, level


def processDataset(nc_files, variable):
    print("<<<<<<<<<<<< Entering BESM_aux.py processDataset() (diag_scripts/aux/BESM)")

    if type(nc_files) is list:
        ncs = netCDF4.MFDataset(nc_files)  # creates the dataset from the list
    else:
        ncs = netCDF4.Dataset(nc_files)  # creates the dataset from a single file

    level_data = None
    level_units = None

    lats = ncs.variables["lat"][:]
    lons = ncs.variables["lon"][:]

    if "plev" in ncs.variables:
        print("------------ Found plev in the dataset")
        level_data = ncs.variables["plev"][:]
        level_units = ncs.variables["plev"].units
    elif "lev" in ncs.variables:
        print("------------ Found lev in the dataset")
        level_data = ncs.variables["lev"][:]
        level_units = ncs.variables["lev"].units
    elif "alevel" in ncs.variables:
        print("------------ Found alevel in the dataset")
        level_data = ncs.variables["alevel"][:]
        level_units = ncs.variables["alevel"].units

    units = ncs.variables[variable].units
    long_name = ncs.variables[variable].long_name
    standard_name = ncs.variables[variable].standard_name
    data = ncs.variables[variable][:]
    nyears = len(data)

    level = processLevel(variable, level_data)

    ncs.close()
    print(">>>>>>>>>>>> Leaving BESM_aux.py processDataset() (diag_scripts/aux/BESM)")
    # return [], [], 0, mm/day, preciptation, Precipitation, [], 0, [], hPa
    return lats, lons, level, units, long_name, standard_name, data, nyears, level_data, level_units


def extract_defs(string):
    return re.findall(r'\"(.+?)\"', string)[0]


def extract_ensemble(string):
    return re.findall(r'r[0-9]*i[0-9]*p[0-9]*', string)[0]
