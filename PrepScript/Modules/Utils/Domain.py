#! /stu01/wumej22/Anaconda3/bin/python
# -*- coding: utf-8 -*-

"""
===============================================================================
Module Name   : Study Domain Definition and Diagnostic Analysis Module
Description   : Define a study area from a bounding box or shapefile,
                and perform ERA5-based diagnostic analysis.
                
                Key Functions:
                - Domain_Definition                         : Run the complete domain workflow.
                - Compute_Anomalies_ERA5 : Compute monthly anomalies.
                - Compute_Correlations   : Compute study-area correlations.
                - Plot_Correlation_Coefficient_Maps      : Plot correlation maps.
                - Plot_Significance_Intersection_Study_Area : Plot the final study area.

Author        : Omarjan @ SYSU
===============================================================================
"""

import os
import logging
import pandas as pd
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import shapely
from matplotlib.colors import BoundaryNorm
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from matplotlib.ticker import MultipleLocator
from pathlib import Path
from . import Tools, Consts
from shapely.geometry import box
from cnmaps import get_adm_maps, draw_maps
from scipy.stats import t
import cmaps

if hasattr(shapely, "contains_xy"):
    from shapely import contains_xy
else:
    from shapely.vectorized import contains as contains_xy

logger = logging.getLogger("CRESMPrep." + __name__)


def Domain_Definition(casecfg, envcfg, gridname, bbox=None, shp=None):
    logger.info(f"{Consts.S4}Starting study-domain definition workflow...")

    logger.info(f"{Consts.S4}Computing anomalies...")
    Compute_Anomalies_ERA5(casecfg, envcfg, gridname)

    logger.info(f"{Consts.S4}Computing correlations...")
    Compute_Correlations(casecfg, envcfg, gridname, bbox=bbox, shp=shp)

    logger.info(f"{Consts.S4}Plotting correlation coefficient maps...")
    Plot_Correlation_Coefficient_Maps(casecfg, envcfg, gridname, bbox=bbox, shp=shp)

    logger.info(f"{Consts.S4}Plotting significance-intersection study area...")
    Plot_Significance_Intersection_Study_Area(casecfg, envcfg, gridname, bbox=bbox, shp=shp)

    logger.info(f"{Consts.S4}Study-domain definition workflow complete.")



def Compute_Anomalies_ERA5(casecfg, envcfg, gridname):
    CaseOutputPath = casecfg.get(gridname, 'CaseOutputPath').strip()
    DefaultDataName = envcfg.get('Domain', 'DefaultDataName').strip()
    DomainDataPath = envcfg.get('Domain', 'DomainDataPath').strip()
    LevelDimName = envcfg.get('Domain', 'LevelDimName').strip()
    TimeDimName = envcfg.get('Domain', 'TimeDimName').strip()
    LatDimName = envcfg.get('Domain', 'LatDimName').strip()
    LonDimName = envcfg.get('Domain', 'LonDimName').strip()
    AnalyzeExtent = get_analyze_extent(envcfg)
    VarList = [item.strip() for item in envcfg.get('Domain', 'VarList').split(',') if item.strip()]

    Tools.File_Exist(DomainDataPath, level="error")
    #read in the variable list from the configuration
    data_in = xr.open_dataset(DomainDataPath)

    if LatDimName not in data_in.coords or LonDimName not in data_in.coords:
        raise KeyError(f"Domain data must contain '{LatDimName}' and '{LonDimName}' coordinates")

    # Limit the anomaly calculation to the configured analysis range
    data_in = select_analyze_range(data_in, AnalyzeExtent, LatDimName, LonDimName)

    # Extract pressure levels from the dataset
    if LevelDimName not in data_in.coords:
        raise KeyError(f"Pressure level coordinate not found: {LevelDimName}")
    pressures = data_in[LevelDimName].values

    # Extract time variable
    if TimeDimName not in data_in.coords:
        raise KeyError(f"Time coordinate not found: {TimeDimName}")

    # 如果数据中的时间变量不是 date，则统一重命名为 date
    if TimeDimName != 'date':
        data_in = data_in.rename({TimeDimName: 'date'})
        TimeDimName = 'date'

    date = data_in['date'].values

    # 兼容 datetime64 和 YYYYMMDD 两种时间格式
    if np.issubdtype(np.asarray(date).dtype, np.datetime64):
        date = pd.to_datetime(date)
    else:
        date = pd.to_datetime(np.asarray(date).astype(str), format='%Y%m%d')

    # Placeholder for anomaly
    anom_dataset = xr.Dataset()  

    for var in VarList:
        logger.debug(f"{Consts.S8}Processing variable: {var}")
        anoms = []
        for p in pressures:
            logger.debug(f"{Consts.S8}Processing pressure level: {p}")

            # get the data for the current pressure level
            data_field = data_in[var].sel(**{LevelDimName: p}).load()

            # 获取实际的时间维度
            time_dim = data_field['date'].dims[0]

            # 重新定义时间轴并命名为 time
            data_field = data_field.assign_coords(time=(time_dim, date))

            # 计算每月的平均值
            data_monavg = data_field.groupby('time.month').mean(dim=time_dim)
            
            # 计算异常值（原始值减去每月平均值）
            anom = data_field.groupby('time.month') - data_monavg
            
            # 为避免冲突，添加 pressure_level 维度时使用新维度名称 'level'
            anom = anom.expand_dims(dim={'level': [p]})  # 添加新维度表示气压层
            
            # 添加结果到异常列表
            anoms.append(anom)

        # 将异常值合并到数据集，按气压层（level）维度组织
        anom_dataset[var] = xr.concat(anoms, dim='level')

    # 保存异常值数据集到文件
    output_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Anomalies_{gridname}.nc"
    anom_dataset.to_netcdf(output_file)



def get_study_area(shp=None, bbox=None, return_detail=False):
    # shp has the highest priority. If shp is not provided, use bbox.
    StudyAreaMode = None
    StudyAreaGeometry = None
    StudyAreaLon = None
    StudyAreaLat = None
    StudyAreaPlotGeometry = None

    if shp is not None and str(shp).strip():
        # If a shapefile is provided, use it to define the study area
        StudyAreaMode = 'shapefile'
        StudyAreaPath = str(shp).strip()
        Tools.File_Exist(StudyAreaPath, level="error")
        StudyAreaMap = gpd.read_file(StudyAreaPath)

        if StudyAreaMap.empty:
            raise ValueError(f"Study area shapefile is empty: {StudyAreaPath}")

        if StudyAreaMap.crs is None:
            raise ValueError(f"Study area shapefile has no CRS: {StudyAreaPath}")

        StudyAreaMap = StudyAreaMap.to_crs('EPSG:4326')
        StudyAreaPlotGeometry = [geometry for geometry in StudyAreaMap.geometry if geometry is not None and not geometry.is_empty]
        if hasattr(StudyAreaMap.geometry, 'union_all'):
            StudyAreaGeometry = StudyAreaMap.geometry.union_all()
        else:
            StudyAreaGeometry = StudyAreaMap.geometry.unary_union

    elif bbox is not None:
        # If a bounding box is provided, use it to define the study area
        StudyAreaMode = 'bbox'

        if not isinstance(bbox, dict):
            raise TypeError("bbox must be a dictionary")

        BBoxKeys = ['lon_max', 'lon_min', 'lat_max', 'lat_min']
        MissingKeys = [key for key in BBoxKeys if key not in bbox]
        if MissingKeys:
            raise KeyError(f"bbox is missing keys: {MissingKeys}")

        StudyAreaLon = {"min": float(bbox['lon_min']), "max": float(bbox['lon_max'])}
        StudyAreaLat = {"min": float(bbox['lat_min']), "max": float(bbox['lat_max'])}
        StudyAreaPlotGeometry = [box(StudyAreaLon['min'], StudyAreaLat['min'], StudyAreaLon['max'], StudyAreaLat['max'])]

        if StudyAreaLon['min'] >= StudyAreaLon['max']:
            raise ValueError("bbox lon_min must be smaller than lon_max")

        if StudyAreaLat['min'] >= StudyAreaLat['max']:
            raise ValueError("bbox lat_min must be smaller than lat_max")

    else:
        raise ValueError("Either shp or bbox must be provided")

    if return_detail:
        return StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat, StudyAreaPlotGeometry

    return StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat



def create_mask(data_field, StudyAreaGeometry, LatDimName, LonDimName):
    lons, lats = np.meshgrid(data_field[LonDimName].values, data_field[LatDimName].values)
    study_mask = contains_xy(StudyAreaGeometry, lons, lats)
    study_mask = xr.DataArray(
        study_mask,
        dims=(LatDimName, LonDimName),
        coords={LatDimName: data_field[LatDimName], LonDimName: data_field[LonDimName]}
    )
    return study_mask



def compute_grid_correlation(data_values, study_values):
    # Compute correlations and p-values using vectorized Pearson correlation
    ValidMask = np.isfinite(data_values) & np.isfinite(study_values[:, None])
    SampleSize = np.sum(ValidMask, axis=0)
    SampleSize = np.maximum(SampleSize, 2)

    # Compute means while ignoring NaNs
    data_mean = np.nanmean(np.where(ValidMask, data_values, np.nan), axis=0)
    study_mean = np.nanmean(np.where(np.isfinite(study_values), study_values, np.nan))

    # Compute anomalies
    data_anomaly = data_values - data_mean
    study_anomaly = study_values - study_mean

    # Mask invalid data points
    data_anomaly[~ValidMask] = np.nan
    numerator = np.nansum(data_anomaly * study_anomaly[:, None], axis=0)
    denominator = np.sqrt(np.nansum(data_anomaly ** 2, axis=0) * np.nansum(study_anomaly ** 2))

    # Compute correlations and handle division by zero
    correlations = numerator / denominator
    correlations[denominator == 0] = np.nan

    # Compute p-values using the t-distribution
    TValues = correlations * np.sqrt((SampleSize - 2) / (1 - correlations ** 2))
    pvalues = 2 * t.sf(np.abs(TValues), SampleSize - 2)
    pvalues[np.isnan(correlations)] = np.nan
    
    return correlations, pvalues



def Compute_Correlations(casecfg, envcfg, gridname, bbox=None, shp=None):

    CaseOutputPath = casecfg.get(gridname, 'CaseOutputPath').strip()
    DefaultDataName = envcfg.get('Domain', 'DefaultDataName').strip()
    VarList = [item.strip() for item in envcfg.get('Domain', 'VarList').split(',') if item.strip()]
    LatDimName = envcfg.get('Domain', 'LatDimName').strip()
    LonDimName = envcfg.get('Domain', 'LonDimName').strip()
    AnalyzeExtent = get_analyze_extent(envcfg)

    anomalies_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Anomalies_{gridname}.nc"
    correlation_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Correlation_{gridname}.nc"
    corpvalues_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Correlation_PValues_{gridname}.nc"

    # Check if the input data file exists
    Tools.File_Exist(anomalies_file, level="error")

    # read in the variable list from the configuration
    data_anom = xr.open_dataset(anomalies_file)

    if 'level' not in data_anom.coords:
        raise KeyError("Pressure level coordinate not found: level")

    pressures = data_anom['level'].values
    StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat = get_study_area(shp, bbox)

    # Initialize dataset for storing correlations
    cors_dataset = xr.Dataset()
    pvals_dataset = xr.Dataset()

    for var in VarList:
        logger.debug(f"Processing variable: {var}")

        # Preload data
        data_field = data_anom[var]

        if LatDimName not in data_field.dims or LonDimName not in data_field.dims:
            raise KeyError(f"Variable '{var}' must contain '{LatDimName}' and '{LonDimName}' dimensions")

        # Limit the correlation calculation to the configured analysis range
        data_field = select_analyze_range(data_field, AnalyzeExtent, LatDimName, LonDimName).load()

        if 'time' not in data_field.coords:
            raise KeyError(f"Variable '{var}' does not contain the normalized time coordinate: time")

        if StudyAreaMode == 'bbox':
            lat_values = data_field[LatDimName].values
            lon_values = data_field[LonDimName].values

            if lat_values[0] <= lat_values[-1]:
                lat_slice = slice(StudyAreaLat['min'], StudyAreaLat['max'])
            else:
                lat_slice = slice(StudyAreaLat['max'], StudyAreaLat['min'])

            if lon_values[0] <= lon_values[-1]:
                lon_slice = slice(StudyAreaLon['min'], StudyAreaLon['max'])
            else:
                lon_slice = slice(StudyAreaLon['max'], StudyAreaLon['min'])

            study_data = data_field.sel({LatDimName: lat_slice, LonDimName: lon_slice})

        else:
            study_mask = create_mask(data_field, StudyAreaGeometry, LatDimName, LonDimName)
            study_data = data_field.where(study_mask)

        if study_data.sizes.get(LatDimName, 0) == 0 or study_data.sizes.get(LonDimName, 0) == 0:
            raise ValueError(f"Study area does not overlap the data grid for variable: {var}")

        time_dim = data_field['time'].dims[0]
        study_mean = study_data.mean(dim=[LatDimName, LonDimName], skipna=True)

        # Initialize empty DataArray for correlations
        corrs_da = xr.DataArray(
            np.full((len(pressures), 4, len(data_field[LatDimName]), len(data_field[LonDimName])), np.nan),
            coords={
                "level": pressures,
                "season": [0, 1, 2, 3],
                LatDimName: data_field[LatDimName],
                LonDimName: data_field[LonDimName],
            },
            dims=["level", "season", LatDimName, LonDimName]
        )

        corrs_da.attrs = {
            "long_name": "Pearson correlation coefficient",
            "description": "Correlation between grid point anomaly and study area mean anomaly",
            "range": "-1 to 1"
        }

        # Initialize empty DataArray for p-values
        pvals_da = xr.DataArray(
            np.full((len(pressures), 4, len(data_field[LatDimName]), len(data_field[LonDimName])), np.nan),
            coords={
                "level": pressures,
                "season": [0, 1, 2, 3],
                LatDimName: data_field[LatDimName],
                LonDimName: data_field[LonDimName],
            },
            dims=["level", "season", LatDimName, LonDimName]
        )

        pvals_da.attrs = {
            "long_name": "Pearson correlation p-value",
            "description": "Statistical significance of Pearson correlation"
        }

        for i, p in enumerate(pressures):
            logger.debug(f"{Consts.S8}Processing pressure level: {p}")

            # Select specific pressure level
            data_level = data_field.sel(level=p)
            study_level = study_mean.sel(level=p)

            for j, season in enumerate(["DJF", "MAM", "JJA", "SON"]):
                logger.debug(f"{Consts.S8}Processing season: {season}")
                # Select seasonal data
                data_season = data_level.where(data_level.time.dt.season == season, drop=True)
                study_season = study_level.where(study_level.time.dt.season == season, drop=True)
                data_season, study_season = xr.align(data_season, study_season, join='inner')

                if data_season.sizes.get(time_dim, 0) < 2:
                    continue
                # Flatten spatial data
                data_flat = data_season.stack(points=(LatDimName, LonDimName)).transpose(time_dim, 'points')
                data_values = data_flat.values
                study_values = study_season.values

                correlations, pvalues = compute_grid_correlation(data_values, study_values)

                # Reshape correlations and p-values to 2D
                correlations = correlations.reshape(data_season[LatDimName].size, data_season[LonDimName].size)
                pvalues = pvalues.reshape(data_season[LatDimName].size, data_season[LonDimName].size)

                # Store correlations and p-values
                corrs_da[i, j] = correlations
                pvals_da[i, j] = pvalues

        # Add correlations and p-values to dataset
        cors_dataset[var] = corrs_da
        pvals_dataset[var] = pvals_da

    cors_dataset.attrs = {
        "description": "Spatial Pearson correlation between grid anomalies and study area mean anomalies",
        "method": "Pearson correlation coefficient",
        "season": "DJF, MAM, JJA, SON",
        "Created by": "CRESM Preprocessing System",
        "Author": Consts.author
    }

    pvals_dataset.attrs = {
        "description": "P-values of spatial Pearson correlation",
        "method": "Two-sided t-test based on Pearson correlation",
        "Created by": "CRESM Preprocessing System",
        "Author": Consts.author
    }

    # Save to output file
    cors_dataset.to_netcdf(correlation_file)
    logger.info(f"{Consts.S4}Correlations saved to {correlation_file}")
    pvals_dataset.to_netcdf(corpvalues_file)
    logger.info(f"{Consts.S4}P-values saved to {corpvalues_file}")

    return correlation_file, corpvalues_file



def get_analyze_extent(envcfg):
    AnalyzeLonMin = envcfg.getfloat('Domain', 'AnalyzeLonMin')
    AnalyzeLonMax = envcfg.getfloat('Domain', 'AnalyzeLonMax')
    AnalyzeLatMin = envcfg.getfloat('Domain', 'AnalyzeLatMin')
    AnalyzeLatMax = envcfg.getfloat('Domain', 'AnalyzeLatMax')

    return [AnalyzeLonMin, AnalyzeLonMax, AnalyzeLatMin, AnalyzeLatMax]



def select_analyze_range(data_field, AnalyzeExtent, LatDimName, LonDimName):
    if LatDimName not in data_field.coords or LonDimName not in data_field.coords:
        raise KeyError(f"Data must contain '{LatDimName}' and '{LonDimName}' coordinates")

    lat_values = data_field[LatDimName].values
    lon_values = data_field[LonDimName].values

    if len(lat_values) == 0 or len(lon_values) == 0:
        raise ValueError("Data grid is empty")

    if lat_values[0] <= lat_values[-1]:
        lat_slice = slice(AnalyzeExtent[2], AnalyzeExtent[3])
    else:
        lat_slice = slice(AnalyzeExtent[3], AnalyzeExtent[2])

    if lon_values[0] <= lon_values[-1]:
        lon_slice = slice(AnalyzeExtent[0], AnalyzeExtent[1])
    else:
        lon_slice = slice(AnalyzeExtent[1], AnalyzeExtent[0])

    data_field = data_field.sel({LatDimName: lat_slice, LonDimName: lon_slice})

    if data_field.sizes.get(LatDimName, 0) == 0 or data_field.sizes.get(LonDimName, 0) == 0:
        raise ValueError(f"Analysis range does not overlap the data grid: {AnalyzeExtent}")

    return data_field



def get_study_area_geometry(StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat):
    if StudyAreaMode == 'shapefile':
        return StudyAreaGeometry

    return box(StudyAreaLon['min'], StudyAreaLat['min'], StudyAreaLon['max'], StudyAreaLat['max'])



def draw_map_base(ax, AnalyzeExtent, AdminMaps, ProvinceMaps=None, DrawOcean=False, DrawLake=False):
    ax.set_extent(AnalyzeExtent, crs=ccrs.PlateCarree())

    if DrawOcean:
        ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="#49E0E1", zorder=1)

    if DrawLake:
        ax.add_feature(cfeature.LAKES.with_scale("10m"), facecolor="blue", alpha=0.3, zorder=2)

    draw_maps(AdminMaps, ax=ax, linewidth=1.0, color='black')

    if ProvinceMaps is not None:
        draw_maps(ProvinceMaps, ax=ax, linewidth=0.6, color='black')

    LonTickMin = np.floor(AnalyzeExtent[0] / 5.0) * 5.0
    LonTickMax = np.ceil(AnalyzeExtent[1] / 5.0) * 5.0
    LatTickMin = np.floor(AnalyzeExtent[2] / 5.0) * 5.0
    LatTickMax = np.ceil(AnalyzeExtent[3] / 5.0) * 5.0

    ax.set_xticks(np.arange(LonTickMin, LonTickMax + 5, 5), crs=ccrs.PlateCarree())
    ax.set_yticks(np.arange(LatTickMin, LatTickMax + 5, 5), crs=ccrs.PlateCarree())
    lon_formatter = LongitudeFormatter(degree_symbol='°')
    lat_formatter = LatitudeFormatter(degree_symbol='°')
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)
    ax.tick_params(axis='both', which='major', labelsize=10, direction='out')
    gl = ax.gridlines(draw_labels=False, linewidth=0.5, linestyle='--', color='black')
    gl.xlocator = MultipleLocator(5)
    gl.ylocator = MultipleLocator(5)
    ax.add_feature(cfeature.COASTLINE, linewidth=1)



def draw_study_area(ax, StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat, StudyAreaPlotGeometry=None):
    if StudyAreaPlotGeometry is None:
        StudyAreaPlotGeometry = [get_study_area_geometry(StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat)]

    ax.add_geometries(StudyAreaPlotGeometry, ccrs.PlateCarree(), edgecolor='black', facecolor='gray', alpha=0.25, linewidth=1.2)



def get_study_area_criteria(envcfg):
    StudyAreaCriteriaList = [item.strip() for item in envcfg.get('Domain', 'StudyAreaCriteria').split(',') if item.strip()]
    return {
        item.split(':', 1)[0].strip(): float(item.split(':', 1)[1].strip())
        for item in StudyAreaCriteriaList
    }



def read_elevation(TopographyDir, AnalyzeExtent, DemCoarsen):
    AnalyzeLonMin, AnalyzeLonMax, AnalyzeLatMin, AnalyzeLatMax = AnalyzeExtent
    known_lat, known_lon, ddeg = -89.99583, -179.99583, 0.00833333
    tile_x = 1200
    tx_min, tx_max = (AnalyzeLonMin - known_lon) / ddeg, (AnalyzeLonMax - known_lon) / ddeg
    ty_min, ty_max = (AnalyzeLatMin - known_lat) / ddeg, (AnalyzeLatMax - known_lat) / ddeg
    xstarts = list(range(1, 43200, tile_x))
    ystarts = list(range(1, 21600, tile_x))
    xid = [i for i, xs in enumerate(xstarts) if xs <= tx_max and (xs + tile_x - 1) >= tx_min]
    yid = [j for j, ys in enumerate(ystarts) if ys <= ty_max and (ys + tile_x - 1) >= ty_min]

    if not xid or not yid:
        return xr.DataArray(
            np.zeros((10, 10)),
            dims=("lat", "lon"),
            coords={
                "lat": np.linspace(AnalyzeLatMin, AnalyzeLatMax, 10),
                "lon": np.linspace(AnalyzeLonMin, AnalyzeLonMax, 10),
            }
        )

    big = np.zeros((len(yid) * tile_x, len(xid) * tile_x), np.int16)
    for ix, i in enumerate(xid):
        for iy, j in enumerate(yid):
            path = Path(TopographyDir) / f"{xstarts[i]:05d}-{xstarts[i] + tile_x - 1:05d}.{ystarts[j]:05d}-{ystarts[j] + tile_x - 1:05d}"
            if path.exists():
                tile = np.fromfile(path, dtype=">i2").reshape(tile_x + 6, tile_x + 6)[3:-3, 3:-3]
                big[iy * tile_x:(iy + 1) * tile_x, ix * tile_x:(ix + 1) * tile_x] = tile

    lons = known_lon + (xstarts[xid[0]] - 1 + np.arange(big.shape[1])) * ddeg
    lats = known_lat + (ystarts[yid[0]] - 1 + np.arange(big.shape[0])) * ddeg
    elevation = xr.DataArray(big, coords=[("lat", lats), ("lon", lons)], name="topo")

    if DemCoarsen > 1:
        elevation = elevation.coarsen(lat=DemCoarsen, lon=DemCoarsen, boundary="trim").mean().astype("float32")

    return elevation



def get_elevation_peak(elevation):
    ElevationValues = np.asarray(elevation.values, dtype=float)
    ElevationValues = ElevationValues[np.isfinite(ElevationValues) & (ElevationValues > 0)]

    if ElevationValues.size == 0:
        return 500

    ElevationPercentile = np.nanpercentile(ElevationValues, 80)
    ElevationPeak = int(np.round(ElevationPercentile / 500.0) * 500)
    ElevationPeak = max(ElevationPeak, 500)

    return ElevationPeak



def Plot_Correlation_Coefficient_Maps(casecfg, envcfg, gridname, bbox=None, shp=None):
    CaseOutputPath = casecfg.get(gridname, 'CaseOutputPath').strip()
    DefaultDataName = envcfg.get('Domain', 'DefaultDataName').strip()
    VarList = [item.strip() for item in envcfg.get('Domain', 'VarList').split(',') if item.strip()]
    LatDimName = envcfg.get('Domain', 'LatDimName').strip()
    LonDimName = envcfg.get('Domain', 'LonDimName').strip()
    AnalyzeExtent = get_analyze_extent(envcfg)

    correlation_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Correlation_{gridname}.nc"
    corpvalues_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Correlation_PValues_{gridname}.nc"
    output_dir = f"{CaseOutputPath}/{gridname}/Domain/Correlation_Plots"

    # Check if the input data files exist
    Tools.File_Exist(correlation_file, level="error")
    Tools.File_Exist(corpvalues_file, level="error")
    os.makedirs(output_dir, exist_ok=True)

    StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat, StudyAreaPlotGeometry = get_study_area(shp, bbox, return_detail=True)
    AdminMaps = get_adm_maps(level='国')
    CorrelationCMap = plt.get_cmap('RdBu_r')
    CorrelationMin = -1.0
    CorrelationMax = 1.0
    ContourLevels = np.arange(CorrelationMin, CorrelationMax + 0.1, 0.1)
    Norm = BoundaryNorm(ContourLevels, ncolors=CorrelationCMap.N)

    corr_ds = xr.open_dataset(correlation_file)
    pval_ds = xr.open_dataset(corpvalues_file)

    if 'level' not in corr_ds.coords:
        raise KeyError("Pressure level coordinate not found: level")

    pressures = corr_ds['level'].values

    for var in VarList:
        if var not in corr_ds or var not in pval_ds:
            raise KeyError(f"Variable not found in correlation files: {var}")

        logger.info(f"{Consts.S8}->Plotting variable: {var}")
        for p in pressures:
            logger.debug(f"{Consts.S8}Plotting pressure level: {p}")
            corr = corr_ds[var].sel(level=p).squeeze()
            pvals = pval_ds[var].sel(level=p).squeeze()

            if LatDimName not in corr.coords or LonDimName not in corr.coords:
                raise KeyError(f"Correlation data must contain '{LatDimName}' and '{LonDimName}' coordinates")

            for j, season in enumerate(["DJF", "MAM", "JJA", "SON"]):
                logger.debug(f"{Consts.S8}Plotting season: {season}")
                corr_season = corr.sel(season=j).squeeze()
                pvals_season = pvals.sel(season=j).squeeze()

                # Plot correlations
                fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()}, constrained_layout=True)
                draw_map_base(ax, AnalyzeExtent, AdminMaps)

                # 提取绘图数据
                mesh = ax.contourf(
                    corr_season[LonDimName], corr_season[LatDimName], corr_season,
                    transform=ccrs.PlateCarree(), cmap=CorrelationCMap,
                    levels=ContourLevels, norm=Norm
                )

                # 添加 colorbar
                cbar = plt.colorbar(mesh, ax=ax, orientation='horizontal', pad=0.01, aspect=40, shrink=0.9)
                cbar.set_ticks(np.linspace(CorrelationMin, CorrelationMax, 11))
                cbar.set_label('Correlation Coefficient', fontsize=12)
                cbar.ax.tick_params(labelsize=10)

                # 绘制研究区
                draw_study_area(ax, StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat, StudyAreaPlotGeometry)

                # 显著性阴影
                mask = pvals_season > 0.05
                ax.contourf(
                    pvals_season[LonDimName], pvals_season[LatDimName], mask,
                    levels=[0.5, 1.5], colors='none', hatches=['///'],
                    transform=ccrs.PlateCarree()
                )

                # 保存图像
                plt.title(f'{var.upper()} at {p} hPa {season}', fontsize=24, pad=10, loc='center', fontweight='bold')
                save_path = os.path.join(output_dir, f'{var}_{p}hPa_{season}.png')
                plt.savefig(save_path, dpi=600)
                plt.close(fig)

    corr_ds.close()
    pval_ds.close()
    logger.info(f"{Consts.S8}-> Correlation maps saved to: {output_dir}")
    return output_dir



def Plot_Significance_Intersection_Study_Area(casecfg, envcfg, gridname, bbox=None, shp=None):
    CaseOutputPath = casecfg.get(gridname, 'CaseOutputPath').strip()
    DefaultDataName = envcfg.get('Domain', 'DefaultDataName').strip()
    LatDimName = envcfg.get('Domain', 'LatDimName').strip()
    LonDimName = envcfg.get('Domain', 'LonDimName').strip()
    GeogDataPath = envcfg.get('Paths', 'GeogDataPath').strip()
    AnalyzeExtent = get_analyze_extent(envcfg)
    BoundaryFracThres = envcfg.getfloat('Domain', 'BoundaryFracThres')
    StudyAreaCriteria = get_study_area_criteria(envcfg)

    corpvalues_file = f"{CaseOutputPath}/{gridname}/Domain/{DefaultDataName}_Correlation_PValues_{gridname}.nc"
    output_dir = f"{CaseOutputPath}/{gridname}/Domain/Study_Area_Plots"

    # Check if the input data files exist
    Tools.File_Exist(corpvalues_file, level="error")
    TopographyDir = f"{GeogDataPath}/topo_30s/"
    os.makedirs(output_dir, exist_ok=True)

    StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat, StudyAreaPlotGeometry = get_study_area(shp, bbox, return_detail=True)
    AdminMaps = get_adm_maps(level='国')

    pval_ds = xr.open_dataset(corpvalues_file)
    IntersectionMask = None

    for var, p in StudyAreaCriteria.items():
        if var not in pval_ds:
            raise KeyError(f"Variable not found in p-value file: {var}")

        logger.debug(f"{Consts.S8}Processing variable: {var}, pressure level: {p}")
        CurrentPValues = pval_ds[var].sel(level=p)

        if LatDimName not in CurrentPValues.dims or LonDimName not in CurrentPValues.dims:
            raise KeyError(f"P-value data must contain '{LatDimName}' and '{LonDimName}' dimensions")

        CurrentMask = CurrentPValues < 0.05
        if IntersectionMask is None:
            IntersectionMask = CurrentMask
        else:
            IntersectionMask, CurrentMask = xr.align(IntersectionMask, CurrentMask, join='inner')
            IntersectionMask = IntersectionMask & CurrentMask

    if IntersectionMask is None or IntersectionMask.sizes.get(LatDimName, 0) == 0 or IntersectionMask.sizes.get(LonDimName, 0) == 0:
        raise ValueError("No valid p-value data is available for the study area plot")

    interpval = xr.where(IntersectionMask, 0, 1)
    elevation = read_elevation(TopographyDir, AnalyzeExtent, 3)
    elevation_land = elevation.where(elevation > 0)
    ElevationPeak = get_elevation_peak(elevation_land)
    ProvinceMaps = get_adm_maps(level='省')

    for j, season in enumerate(["DJF", "MAM", "JJA", "SON"]):
        logger.debug(f"{Consts.S8}Plotting season: {season}")
        interpval_season = interpval.sel(season=j)

        # 绘图
        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()}, constrained_layout=True)
        draw_map_base(ax, AnalyzeExtent, AdminMaps, ProvinceMaps=ProvinceMaps, DrawOcean=True, DrawLake=True)

        # 地形
        mesh = ax.pcolormesh(
            elevation_land.lon, elevation_land.lat, elevation_land,
            cmap=cmaps.WhiteBlueGreenYellowRed, shading="auto",
            vmax=ElevationPeak, vmin=0, transform=ccrs.PlateCarree(), zorder=0
        )
        plt.colorbar(mesh, ax=ax, shrink=0.6, pad=0.04, label="Elevation (m)")

        # 绘制研究区
        draw_study_area(ax, StudyAreaMode, StudyAreaGeometry, StudyAreaLon, StudyAreaLat, StudyAreaPlotGeometry)

        # 不满足所有变量显著性条件的区域画斜线
        ax.contourf(
            interpval_season[LonDimName], interpval_season[LatDimName], interpval_season,
            levels=[0.5, 1.5], colors='none', hatches=['///'],
            transform=ccrs.PlateCarree()
        )

        # 根据显著性区域覆盖比例绘制最终研究区边界
        SignificantMask = interpval_season == 0
        LonFraction = SignificantMask.mean(dim=LatDimName)
        LatFraction = SignificantMask.mean(dim=LonDimName)
        LonValues = interpval_season[LonDimName].values
        LatValues = interpval_season[LatDimName].values
        lonloc = LonValues[(LonFraction.values > BoundaryFracThres) & (LonValues >= AnalyzeExtent[0]) & (LonValues <= AnalyzeExtent[1])]
        latloc = LatValues[(LatFraction.values > BoundaryFracThres) & (LatValues >= AnalyzeExtent[2]) & (LatValues <= AnalyzeExtent[3])]

        if len(lonloc) > 0 and len(latloc) > 0:
            ax.plot(lonloc, np.ones_like(lonloc) * latloc.max(), ls='-', color='yellow', linewidth=3)
            ax.plot(lonloc, np.ones_like(lonloc) * latloc.min(), ls='-', color='yellow', linewidth=3)
            ax.plot(np.ones_like(latloc) * lonloc.max(), latloc, ls='-', color='yellow', linewidth=3)
            ax.plot(np.ones_like(latloc) * lonloc.min(), latloc, ls='-', color='yellow', linewidth=3)
        else:
            logger.warning(f"{Consts.S8}No significant study area boundary found for season: {season}")

        plt.title(f'Significant Study Area ({season})', fontsize=24)
        save_path = os.path.join(output_dir, f'Study_Area_{season}.png')
        plt.savefig(save_path, dpi=600)
        plt.close(fig)

    pval_ds.close()
    logger.info(f"{Consts.S8}-> Study area plots saved to: {output_dir}")
    return output_dir
