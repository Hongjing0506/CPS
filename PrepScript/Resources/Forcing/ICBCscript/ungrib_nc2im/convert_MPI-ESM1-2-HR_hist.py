#******************************************************************************
# Python script to convert CMIP6-MPI data to Intermediate file format
#
# This script does not look for specific dates in a file - simply convert
# all dates in the input file to IM format, so it is the users responsibility
# to ensure the input data is consistent
# 
# translated from NCL script by Oscar
#******************************************************************************

import os
import time
import argparse
import NCL_Utils as nclu
import numpy as np
import xarray as xr
import pandas as pd
from glob import glob
# import pywinter.winter as pyw
import pywinter as pyw
from datetime import datetime, timedelta
np.set_printoptions(precision=7, suppress=True, linewidth=200)



#------------------------------------------------------------------------------#
argparser = argparse.ArgumentParser()
argparser.add_argument('-Y', '--year', help='year', type=int, required=False, default=2000)
argparser.add_argument('-M', '--month', help='month', type=int, required=False, default=1)
argparser.add_argument('-D', '--day', help='day', type=int, required=False, default=27)
argparser.add_argument('-indir', '--inputdir', help='input directory containing netCDF files', type=str, required=False, default="./ncs/")
argparser.add_argument('-outdir', '--outputdir', help='output directory for intermediate files', type=str, required=False, default="./")
args = argparser.parse_args()
year = args.year
month = args.month
day = args.day
inputdir=args.inputdir
outputdir=args.outputdir
#------------------------------------------------------------------------------#


#******************************************************************************
# Don't change anything below this line
#******************************************************************************
# 单位设置
calendar = "proleptic_gregorian"
units = "days since 1850-01-01 00:00:00"
# 基准日期
base_date_str = "1850-01-01 00:00:00"
date_format = "%Y-%m-%d %H:%M:%S"
base_date = datetime.strptime(base_date_str, date_format)
# 计算日期
date_str = f"{year:04d}-{month:02d}-{day:02d} 00:00:00"
date_in = datetime.strptime(date_str, date_format)
date_sel1 = date_in
date_sel2 = date_in + timedelta(hours=18)
start_year, start_month = date_sel1.year, date_sel1.month
end_year, end_month = date_sel2.year, date_sel2.month



#******************************************************************************
# READ IN DATA
#******************************************************************************

day_date = date_in.strftime("%Y-%m-%d")
print("\n\n=============================")
print(f"    date: {day_date}        ")
print("=============================")
print("[1] read files")

# MPI  1 --> 95 layers are bottom --> top
#************** 3D(6hr) ******************************
fl_T = sorted(glob(f"{inputdir}/ta_*01010000*.nc"))
in_T = xr.open_mfdataset(fl_T, combine='by_coords')  # ta(3D)
fl_U = sorted(glob(f"{inputdir}/ua_*01010000*.nc"))
in_U = xr.open_mfdataset(fl_U, combine='by_coords')  # ua(3D)
fl_V = sorted(glob(f"{inputdir}/va_*01010000*.nc"))
in_V = xr.open_mfdataset(fl_V, combine='by_coords')  # va(3D)
fl_Q = sorted(glob(f"{inputdir}/hus_*01010000*.nc"))
in_Q = xr.open_mfdataset(fl_Q, combine='by_coords')  # sh(3D)
#************** 2D(3hr-HIS 6hr-SSP585) ******************************
fl_T2 = sorted(glob(f"{inputdir}/tas_*01010600*.nc"))
in_T2 = xr.open_mfdataset(fl_T2, combine='by_coords')  # ta-2m(2D)
fl_U2 = sorted(glob(f"{inputdir}/uas_*01010600*.nc"))
in_U2 = xr.open_mfdataset(fl_U2, combine='by_coords')  # ua-10m(2D)
fl_V2 = sorted(glob(f"{inputdir}/vas_*01010600*.nc"))
in_V2 = xr.open_mfdataset(fl_V2, combine='by_coords')  # va-10m(2D)
fl_Q2 = sorted(glob(f"{inputdir}/huss_*01010600*.nc"))
in_Q2 = xr.open_mfdataset(fl_Q2, combine='by_coords')  # sh-2m(2D)
#************** 2D(6hr) ******************************
fl_PS = sorted(glob(f"{inputdir}/ps_*01010600*.nc"))
in_PS = xr.open_mfdataset(fl_PS, combine='by_coords')  # ps(2D)
f1_SLP = sorted(glob(f"{inputdir}/psl_*01010600*.nc"))
in_SLP = xr.open_mfdataset(f1_SLP, combine='by_coords')  # psl(2D)
#************** 2D(day-HIS 6hr-SSP585) ******************************
fl_TSK = sorted(glob(f"{inputdir}/ts_*0101*.nc"))
in_TSK = xr.open_mfdataset(fl_TSK, combine='by_coords')  # SST(daily)
#************** 3D SOIl(mon) ****************************************
fl_TSOIL = sorted(glob(f"{inputdir}/tsl_*01-*.nc"))
in_TSOIL = xr.open_mfdataset(fl_TSOIL, combine='by_coords')  # soil temperature (daily)
fl_MSOIL = sorted(glob(f"{inputdir}/mrsol_*01-*.nc"))
in_MSOIL = xr.open_mfdataset(fl_MSOIL, combine='by_coords')  # soil moisture (daily)
#************** 2D **************************************************************
in_ZSFC = xr.open_dataset(f"{inputdir}/orog_fx_MPI-ESM1-2-HR_historical_r1i1p1f1_gn.nc")  # PHIS:static surface geopotential
in_LAND = xr.open_dataset(f"{inputdir}/sftlf_fx_MPI-ESM1-2-HR_historical_r1i1p1f1_gn.nc")  # land-sea mask



#******************************************************************************
# SELECT DATA FOR GIVEN DATE
#******************************************************************************
print("[2] select data for given date")
# atm 3D
T = in_T.ta.sel(time=slice(date_sel1, date_sel2))
U = in_U.ua.sel(time=slice(date_sel1, date_sel2))
V = in_V.va.sel(time=slice(date_sel1, date_sel2))
Q = in_Q.hus.sel(time=slice(date_sel1, date_sel2))
# atm 2D
T2 = in_T2.tas.sel(time=slice(date_sel1, date_sel2))
U10 = in_U2.uas.sel(time=slice(date_sel1, date_sel2))
V10 = in_V2.vas.sel(time=slice(date_sel1, date_sel2))
Q2 = in_Q2.huss.sel(time=slice(date_sel1, date_sel2))
PS = in_PS.ps.sel(time=slice(date_sel1, date_sel2))
SLP = in_SLP.psl.sel(time=slice(date_sel1, date_sel2))
# land 
TSKIN = in_TSK.ts.sel(time=slice(date_sel1, date_sel2))
TSOIL = in_TSOIL.tsl.sel(time=in_TSOIL.tsl.time.dt.year.isin(range(start_year, end_year + 1)) & 
                         in_TSOIL.tsl.time.dt.month.isin(range(start_month, end_month + 1)))
MSOIL = in_MSOIL.mrsol.sel(time=in_MSOIL.mrsol.time.dt.year.isin(range(start_year, end_year + 1)) & 
                           in_MSOIL.mrsol.time.dt.month.isin(range(start_month, end_month + 1)))


#******************************************************************************
# DATA CHECK
#******************************************************************************
print("[3] data check")
varlist = ["T","U","V","Q","T2","U10","V10","Q2","PS","SLP"]
for var in varlist:
    size = eval(var).sizes['time']
    if size !=  4:
        print("\n\n===============================================")
        print("ERROR!!!")
        print(f"for year={year}, month={month}, day={day}")
        print(f"Error: {var} time is not 4, it is {size}")
        exit()

# dims
ntime, nlev, nlat, nlon = T.shape
times  = T.time  # time dimension
levs  = T.lev  # vertical levels
lon   = T.lon    # atm grid
lat   = T.lat
day_hours = pd.date_range(start=date_in.replace(hour=0, minute=0, second=0, microsecond=0), 
                        end=date_in.replace(hour=23, minute=59, second=59, microsecond=999999), 
                        freq='6h')
# get dimensions from dummy variable
print("    ntim, nlev, nlat, nlon: "+str(ntime)+" "+str(nlev)+" "+str(nlat)+" "+str(nlon))
print("    day_hours:", day_hours.to_list())
#----------- ti[0]me --------------------




#******************************************************************************
# CHECK FOR MISSING DATA 
#******************************************************************************
print("[4] check for missing data ")

def check_missing(varname, arr, date_str):
    if "time" not in arr.dims:
        raise ValueError("Input data must have a 'time' dimension.")
    has_nan = arr.isnull().any()  
    if has_nan:
        print("\n\n===============================================")
        print("ERROR!!!")
        outfile = f"check_{varname}_{date_str}.nc"
        arr.to_dataset(name=varname).to_netcdf(outfile)
        missing_idx = np.argwhere(nan_da.values)
        print(f"{varname} missing values at indices:", missing_idx)
        print(f"save to {outfile}")
        print("Data contains some missing value, exit")
        raise ValueError("Data contains missing values.")

check_missing("T", T, date_str)
check_missing("U", U, date_str)
check_missing("V", V, date_str)
check_missing("Q", Q, date_str)
check_missing("PS", PS, date_str)
check_missing("SLP", SLP, date_str)
check_missing("T2", T2, date_str)
check_missing("U10", U10, date_str)
check_missing("V10", V10, date_str)
check_missing("Q2", Q2, date_str)
check_missing("TSKIN", TSKIN, date_str)
if (PS <= 0).any():
    print("\n\n===============================================")
    print("ERROR!!!")
    print("Data PS contains some non-positive value, exit")
    print("PS non-positive values at indices:", np.argwhere(PS.values <= 0))
    print(f"save to check_PS_{date_str}.nc")
    PS.to_netcdf(f"check_PS_{date_str}.nc")
    exit()
    



#******************************************************************************
# INTERPOLATE/CONVERT DATA TO REQUIRED TIME FREQUENCY
#******************************************************************************
print("[5] interpolate/convert data to required time frequency")
# 判断年份
if year <= 2014:
    # 将每日数据转换为 6 小时数据 (假设通过维度扩展进行)
    time_index = pd.to_datetime(TSKIN.time.values)[0]
    day_hours = pd.date_range(start=time_index.replace(hour=0, minute=0, second=0, microsecond=0), 
                            end=time_index.replace(hour=23, minute=59, second=59, microsecond=999999), 
                            freq='6h')
    TSKIN6 = TSKIN.isel(time=0).expand_dims(time=day_hours)  # 直接广播复制到4个时刻
    TAVGSFC6 = TSKIN6
    TSKIN = TSKIN6
    SST6 = TSKIN6
    # 设置缺失值为 np.nan
    SST6 = SST6.where(np.isnan(SST6), np.nan)
else:
    # 保持 6 小时数据不变
    TSKIN6 = TSKIN
    TAVGSFC6 = TSKIN6
    SST6 = TSKIN6
    TSKIN = TSKIN6
    # 设置缺失值为 np.nan
    SST6 = SST6.where(np.isnan(SST6), np.nan)
# TSKIN.to_netcdf("test_sst.nc")




#******************************************************************************
# MAKE LAND MASK AND CALCULATE SURFACE HEIGHT
#******************************************************************************
print("[6] make land mask and calculate surface height")
LMASK = in_LAND.sftlf  
LMASK = np.where(LMASK == 0, 0, 1)  # 0-ocean, 1-land
LMASK = xr.DataArray(LMASK.astype(np.float64), coords=[lat, lon], dims=["lat", "lon"])
ZSFC = in_ZSFC.orog  
PHIS = ZSFC * 9.8    # geopotential to surface height


#******************************************************************************
# CALCULATE VERTICAL LEVELS, PRESSURE, GEOPOTENTIAL HEIGHT, RELATIVE HUMIDITY
#******************************************************************************
print("[7] calculate vertical levels, pressure, geopotential height, relative humidity")
# Calculate the pressures on each hybrid level (bottom up)
print("    Calculate P")
p0 = 1
hyam = in_T.ap.values[0,:]
# hyam = hyam / p0     # 进行无量纲化，将hyam转换为无量纲形式
hybm = in_T.b.values[0,:]
hyai = in_T.ap_bnds.values[0,:,0]
hybi = in_T.b_bnds.values[0,:,0]
hyai = np.array(hyai.tolist() + [0.0])  # 在列表末尾添加 0.0
hybi = np.array(hybi.tolist() + [0.0])  # 在列表末尾添加 0.0
# 计算压力
P = nclu.pres_hybrid_ccm(PS.values, p0, hyam, hybm)
P = xr.DataArray(P, coords=[T.time, levs, lat, lon], dims=["time", "lev", "lat", "lon"])

# 需要添加多维处理能力
# 需要添加 bottom up 计算能力
#===========================
print("    calculate Z")
P0 = 1
tv = T * (1 + 0.61 * Q)  # 虽然公式中是 q，但这里的 Q 已经是比湿
Z = np.zeros_like(T.values)
for t in range(T.sizes['time']):
    Z[t, :, :, :] = nclu.cz2ccm(PS.isel(time=t).values, PHIS.values, tv.isel(time=t).values[::-1,:,:], P0, hyam, hybm, hyai, hybi)
Z = Z[:,::-1,:,:]
Z = xr.DataArray(Z, coords=[T.time, levs, lat, lon], dims=["time", "lev", "lat", "lon"])

#==============================
print("    calculate RH")
W = Q / (1 + Q)  # 比湿转化为混合比
R = nclu.relhum(W.values, T.values, P.values, clip=True)
R = xr.DataArray(R, coords=[T.time, levs, lat, lon], dims=["time", "lev", "lat", "lon"])
W2 = Q2 / (1 + Q2)  # 比湿转化为混合比
R2 = nclu.relhum(W2.values, T2.values, PS.values, clip=True)
R2 = xr.DataArray(R2, coords=[T2.time, lat, lon], dims=["time", "lat", "lon"])




#******************************************************************************
# CALCULATE SURFACE SNOW, SOIL TEMP, SOIL MOISTURE
#******************************************************************************
# 雪深 SNOWW6
SNOWW6 = xr.zeros_like(PS)  # NCL 里先赋值为 0
SNOWW6 = SNOWW6.where(SNOWW6 >= 0, np.nan)                               # 小于0的设为无效
SNOWW6 = SNOWW6 * 1000                                                   # 转换单位（假设 mm）
SNOWW6 = SNOWW6.fillna(np.nan)                                           # 缺测设为 np.nan
# print("SNOWW6:", np.min(SNOWW6.values), np.max(SNOWW6.values))

# 土壤温度 TSOIL1_6 ~ TSOIL4_6
TSOIL_6 = TSOIL.isel(time=0).expand_dims(time=day_hours)                  # 直接广播复制到4个时刻
MSOIL_6 = MSOIL.isel(time=0).expand_dims(time=day_hours)                  # 直接广播复制到4个时刻
TSOIL1_6 = TSOIL_6.isel(depth=0).fillna(np.nan)                          # 第1层土壤温度
TSOIL2_6 = TSOIL_6.isel(depth=1).fillna(np.nan)                          # 第2层土壤温度
TSOIL3_6 = TSOIL_6.isel(depth=2).fillna(np.nan)                          # 第3层土壤温度
TSOIL4_6 = TSOIL_6.isel(depth=3).fillna(np.nan)                          # 第4层土壤温度

# 土壤湿度 MSOIL1_6 ~ MSOIL4_6
thickness = [0.065, 0.254, 0.913, 2.902]  # m
MSOIL1_6 = (MSOIL_6.isel(depth=0)/ (1000 * thickness[0])).fillna(np.nan) # 第1层土壤温度
MSOIL2_6 = (MSOIL_6.isel(depth=1)/ (1000 * thickness[1])).fillna(np.nan) # 第2层土壤温度
MSOIL3_6 = (MSOIL_6.isel(depth=2)/ (1000 * thickness[2])).fillna(np.nan) # 第3层土壤温度
MSOIL4_6 = (MSOIL_6.isel(depth=3)/ (1000 * thickness[3])).fillna(np.nan) # 第4层土壤温度




#******************************************************************************
# WRITE OUT DATA TO WRF INTERMEDIATE FORMAT (CALL pywinter)
#******************************************************************************
print("[8] write out data to WRF intermediate files")
'''
Use pywinter to write intermediate files
Pywinter is a Python3 library designed for handling files in MPAS/WRF-WPS intermediate file format.
Contact: dniloash@gmail.com
Github: https://github.com/dniloash/Pywinter
This is a fantastic library, if you have any questions please read the documentation
'''

#=========================
# (1) Geo-Information (select one of the projections below)
# 0: Cylindrical Equidistant (Lat/lon)
# 1: Mercator projection
# 3: Lambert conformal conic
# 4: Gaussian [global only] (Transverse mercator)
# 5: Polar-stereographic projection
'''
The latitude and longitude must be ordered from the lower to the higher in degrees north and degrees east,
therefore the 2D, 3D or soil data array must be according to the respective coordinates.
'''
stlon = float(lon[0].values)                # SOUTH-WEST corner longitude of data (degrees north)
stlat = float(lat[0].values)                # SOUTH-WEST corner latitude of data (degrees east)
dlon = float(lon[1].values - lon[0].values) # longitude increment (degrees)
dlat = float(lat[1].values - lat[0].values) # latitude increment (degrees)
winter_geo = pyw.Geo0(stlat, stlon, dlat, dlon)


#=========================
# (2) variables Field 
FIELD_2D = {
#   varname      : [ long name,                              units,        level],
    "PSFC"       : ["Surface pressure",                      "Pa",       '200100'],   # Surface pressure
    "PMSL"       : ["Sea level pressure",                    "Pa",       '201300'],   # Mean sea level pressure
    "SKINTEMP"   : ["Skin Temperature",                      "K",        '200100'],   # Skin temperature
    "SOILHGT"    : ["Terrain Elevation",                     "m",        '200100'],   # Surface geopotential height
    "TT"         : ["2m temperature",                        "K",        '200100'],   # 2m temperature
    "RH"         : ["2m relative humidity",                  "%",        '200100'],   # 2m relative humidity
    "SPECHUMD"   : ["2m specific humidity",                  "kg kg-1",  '200100'],   # 2m specific humidity
    "UU"         : ["10m wind u component",                  "m s-1",    '200100'],   # 10m wind u component
    "VV"         : ["10m wind v component",                  "m s-1",    '200100'],   # 10m wind v component
    "LANDSEA"    : ["Land/Sea Flag; 0=Ocean; 1=Land",        "proprtn",  '200100'],   # Land/Sea Flag; 0=Ocean; 1=Land
    "SEAICE"     : ["Sea-ice fraction",                      "fraction", '200100'],   # Sea-ice fraction
    "SNOW"       : ["Water equivalent snow depth",           "kg m-2",   '200100'],   # Water equivalent snow depth
    "TAVGSFC"    : ["Daily mean of surface air temperature", "K",        '200100'],   # Daily mean of surface air temperature
    "ST000007"   : ["Soil Temperature 0-7 cm layer",         "K",        '200100'],   # Soil Temperature 0-7 cm layer
    "ST007028"   : ["Soil Temperature 7-28 cm layer",        "K",        '200100'],   # Soil Temperature 7-28 cm layer
    "ST028100"   : ["Soil Temperature 28-100 cm layer",      "K",        '200100'],   # Soil Temperature 28-100 cm layer
    "ST100255"   : ["Soil Temperature 100-255 cm layer",     "K",        '200100'],   # Soil Temperature 100-255 cm layer
    "SM000007"   : ["Soil Moisture 0-7 cm layer",            "fraction", '200100'],   # Soil Moisture 0-7 cm layer
    "SM007028"   : ["Soil Moisture 7-28 cm layer",           "fraction", '200100'],   # Soil Moisture 7-28 cm layer
    "SM028100"   : ["Soil Moisture 28-100 cm layer",         "fraction", '200100'],   # Soil Moisture 28-100 cm layer
    "SM100255"   : ["Soil Moisture 100-255 cm layer",        "fraction", '200100'],   # Soil Moisture 100-255 cm layer
}

FIELD_3D = {
#   varname     : [long name,                                units,       level],
    "UU"        : ["Zonal Wind Speed",                       "m s-1",      None],   # Eastward wind
    "VV"        : ["Meridional Wind Speed",                  "m s-1",      None],   # Northward wind
    "TT"        : ["Temperature",                            "K",          None],   # Air temperature
    "RH"        : ["Relative humidity",                      "%",          None],   # Relative humidity
    "SPECHUMD"  : ["Specific humidity",                      "kg kg-1",    None],   # Specific humidity
    "PRESSURE"  : ["Pressure",                               "Pa",         None],   # Pressure
}

FIELD_SST = {
#   varname     : [long name,                                units,       level],
    "SST"       : ["Sea surface temperature",                "K",        '200100'],   # Sea surface temperature
}



#=========================
# (3) write out data
for i, tim in enumerate(times):
    # print("    time:", pd.to_datetime(tim.values))
    time_index = pd.to_datetime(tim.values)
    date_st1 = time_index.strftime("%Y-%m-%d_%H")
    yyyy_format = time_index.strftime("%Y")
    
    # ============= 2D fields =============
    # var              = pyw.V2d(varname,     data,                                              long_name,                units,                    level                   )
    winter_landsea     = pyw.V2d("LANDSEA",   LMASK.values.astype(np.float32),                   FIELD_2D["LANDSEA"][0],   FIELD_2D["LANDSEA"][1],   FIELD_2D["LANDSEA"][2]  )
    winter_psfc        = pyw.V2d("PSFC",      PS.sel(time=tim).values.astype(np.float32),        FIELD_2D["PSFC"][0],      FIELD_2D["PSFC"][1],      FIELD_2D["PSFC"][2]     )
    winter_pmsl        = pyw.V2d("PMSL",      SLP.sel(time=tim).values.astype(np.float32),       FIELD_2D["PMSL"][0],      FIELD_2D["PMSL"][1],      FIELD_2D["PMSL"][2]     )
    winter_skintemp    = pyw.V2d("SKINTEMP",  TSKIN.sel(time=tim).values.astype(np.float32),     FIELD_2D["SKINTEMP"][0],  FIELD_2D["SKINTEMP"][1],  FIELD_2D["SKINTEMP"][2] )
    winter_tt_2m       = pyw.V2d("TT",        T2.sel(time=tim).values.astype(np.float32),        FIELD_2D["TT"][0],        FIELD_2D["TT"][1],        FIELD_2D["TT"][2]       )
    winter_rh_2m       = pyw.V2d("RH",        R2.sel(time=tim).values.astype(np.float32),        FIELD_2D["RH"][0],        FIELD_2D["RH"][1],        FIELD_2D["RH"][2]       )
    winter_spechumd_2m = pyw.V2d("SPECHUMD",  Q2.sel(time=tim).values.astype(np.float32),        FIELD_2D["SPECHUMD"][0],  FIELD_2D["SPECHUMD"][1],  FIELD_2D["SPECHUMD"][2] )
    winter_uu_10m      = pyw.V2d("UU",        U10.sel(time=tim).values.astype(np.float32),       FIELD_2D["UU"][0],        FIELD_2D["UU"][1],        FIELD_2D["UU"][2]       )
    winter_vv_10m      = pyw.V2d("VV",        V10.sel(time=tim).values.astype(np.float32),       FIELD_2D["VV"][0],        FIELD_2D["VV"][1],        FIELD_2D["VV"][2]       )
    # winter_seaice     = pyw.V2d("SEAICE",    SEAICE6.sel(time=tim).values.astype(np.float32),  FIELD_2D["SEAICE"][0],    FIELD_2D["SEAICE"][1],    FIELD_2D["SEAICE"][2]   )
    winter_snow        = pyw.V2d("SNOW",      SNOWW6.sel(time=tim).values.astype(np.float32),    FIELD_2D["SNOW"][0],      FIELD_2D["SNOW"][1],      FIELD_2D["SNOW"][2]     )
    winter_tavgsfc     = pyw.V2d("TAVGSFC",   TAVGSFC6.sel(time=tim).values.astype(np.float32),  FIELD_2D["TAVGSFC"][0],   FIELD_2D["TAVGSFC"][1],   FIELD_2D["TAVGSFC"][2]  )
    winter_st000007    = pyw.V2d("ST000007",  TSOIL1_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["ST000007"][0],  FIELD_2D["ST000007"][1],  FIELD_2D["ST000007"][2] )    
    winter_st007028    = pyw.V2d("ST007028",  TSOIL2_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["ST007028"][0],  FIELD_2D["ST007028"][1],  FIELD_2D["ST007028"][2] )
    winter_st028100    = pyw.V2d("ST028100",  TSOIL3_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["ST028100"][0],  FIELD_2D["ST028100"][1],  FIELD_2D["ST028100"][2] )
    winter_st100255    = pyw.V2d("ST100255",  TSOIL4_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["ST100255"][0],  FIELD_2D["ST100255"][1],  FIELD_2D["ST100255"][2] )
    winter_sm000007    = pyw.V2d("SM000007",  MSOIL1_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["SM000007"][0],  FIELD_2D["SM000007"][1],  FIELD_2D["SM000007"][2] )    
    winter_sm007028    = pyw.V2d("SM007028",  MSOIL2_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["SM007028"][0],  FIELD_2D["SM007028"][1],  FIELD_2D["SM007028"][2] )
    winter_sm028100    = pyw.V2d("SM028100",  MSOIL3_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["SM028100"][0],  FIELD_2D["SM028100"][1],  FIELD_2D["SM028100"][2] )
    winter_sm100255    = pyw.V2d("SM100255",  MSOIL4_6.sel(time=tim).values.astype(np.float32),  FIELD_2D["SM100255"][0],  FIELD_2D["SM100255"][1],  FIELD_2D["SM100255"][2] )
    fields_2D          = [  winter_landsea,  winter_psfc,     winter_pmsl,
                          winter_skintemp, winter_tt_2m,    winter_rh_2m,    winter_spechumd_2m,
                          winter_uu_10m,   winter_vv_10m,   winter_snow,     winter_tavgsfc,
                          winter_st000007, winter_st007028, winter_st028100, winter_st100255,
                          winter_sm000007, winter_sm007028, winter_sm028100, winter_sm100255]
    # Write intermediate file
    pyw.cinter('2D', date_st1, winter_geo, fields_2D, outputdir)


    # ============= 3D fields =============
    # var              = pyw.V3d(varname,     data                                    )       
    winter_uu          = pyw.V3d("UU",        U.isel(time=i).values[0:61, :, :].astype(np.float32))
    winter_vv          = pyw.V3d("VV",        V.isel(time=i).values[0:61, :, :].astype(np.float32))
    winter_tt          = pyw.V3d("TT",        T.isel(time=i).values[0:61, :, :].astype(np.float32))
    winter_rh          = pyw.V3d("RH",        R.isel(time=i).values[0:61, :, :].astype(np.float32))
    winter_sh          = pyw.V3d("SPECHUMD",  Q.isel(time=i).values[0:61, :, :].astype(np.float32))
    winter_pr          = pyw.V3d("PRESSURE",  P.isel(time=i).values[0:61, :, :].astype(np.float32))
    winter_ght         = pyw.V3d("GHT",       Z.isel(time=i).values[0:61, :, :].astype(np.float32))
    fields_3D          = [winter_uu, winter_vv, winter_tt, winter_rh, winter_sh, winter_pr, winter_ght]
    # Write intermediate file
    pyw.cinter('3D', date_st1, winter_geo, fields_3D, outputdir)



    # ============= SST fields =============
    # var              = pyw.V2d(varname,     data,                                              long_name,                units,                    level                   )
    winter_sst         = pyw.V2d("SST",       SST6.sel(time=tim).values.astype(np.float32),      FIELD_SST["SST"][0],      FIELD_SST["SST"][1],      FIELD_SST["SST"][2]     )
    fields_SST         = [winter_sst]
    # Write intermediate file
    pyw.cinter('SST', date_st1, winter_geo, fields_SST, outputdir)



# ============= Soil HGT fields =============
winter_soilhgt     = pyw.V2d("SOILHGT",   ZSFC.values.astype(np.float32),                    FIELD_2D["SOILHGT"][0],   FIELD_2D["SOILHGT"][1],   FIELD_2D["SOILHGT"][2]  )
fields_soilhgt     = [winter_soilhgt]
# Write intermediate file
pyw.cinter('SOILHGT', date_st1, winter_geo, fields_soilhgt, outputdir)


#******************************************************************************
# DONE
#******************************************************************************
print(f"\n!!! PROCESS COMPLETE: {day_date} !!!")

