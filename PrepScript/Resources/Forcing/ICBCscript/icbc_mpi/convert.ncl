;******************************************************************************
; NCL script to convert CESM1 (ds316.0) data to Intermediate file format
;
; This script does not look for specific dates in a file - simply convert
; all dates in the input file to IM format, so it is the users responsibility
; to ensure the input data is consistent

;2020/09/23 input or not 取消，添加土壤数据的写入，使用mpi 月土壤数据
;******************************************************************************

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/popRemap.ncl"


outDIR="/share/home/dq048/oscar/future/hist/runicbc_mpi/hist/MPI_IM/"


;clmDIR="/scratch/users/xhr@umd.edu/DATA/merra2_ICBC/new/"
;******************************************************************************
; Which CASE are we doing.
; CASE is only used for naming conventions, but make sure this is correct,
; else you could clobber exisiting files.
;******************************************************************************

if ( .not. isvar("YR") ) then
print("We need to know which case we are running")
exit
end if

if ( .not. isvar("MON") ) then
print("We need to know which case we are running")
exit
end if

if ( .not. isvar("DAY") ) then
print("We need to know which case we are running")
exit
end if

if ( .not. isvar("IM_root_name") ) then
IM_root_name = "MPI"
else
IM_root_name = IM_root_name
end if


if ( .not. isvar("outDIR") ) then
;  outDIR = "OUTPUT"
print("We need to know where to put the data")
exit
end if


;******************************************************************************
; Don't change anything below this line
;******************************************************************************
; get date
;==============================================================================
year   = tointeger(YR)
month  = tointeger(MON)
day    = tointeger(DAY)
hour   = 0
minute = 0
second = 0
;units  = "days since 1859-12-01"
topt=0
units = "days since 0001-01-01 00:00:00"
topt@calendar = "proleptic_gregorian"
date1 = cd_inv_calendar(year,month,day,hour,minute,second,units, topt)


units2 = "days since 1850-1-1 00:00:00"
topt@calendar = "proleptic_gregorian"
date2 = cd_inv_calendar(year,month,day,hour,minute,second,units2, topt)


;************************************************
; file handling
;************************************************
data_large="/share/home/dq048/oscar/future/hist/runicbc_mpi/hist/MPI_IM//"+year+"/ncs/"
dataDIR="/share/home/dq048/oscar/future/hist/mpi/"
dataDIR3  = dataDIR
dataDIR2  = dataDIR3
date=sprinti("%0.2i",YR)+sprinti("%0.2i",MON)+sprinti("%0.2i",DAY)
print("================opening files======================")
print("=         date: "+date+"  "+date1+"  "+date2+"     ")
print("================opening files======================")
;MPI  1 --> 95 layers are bottom --> top
;************** 3D(6hr) ******************************
f1_atm1  = systemfunc("ls "+data_large+"/ta_*01010000-*.nc")
in_atm1  = addfiles(f1_atm1,"r")                        ; ta(3D)
f1_atm2  = systemfunc("ls "+data_large+"/ua_*01010000-*.nc")
in_atm2  = addfiles(f1_atm2,"r")                        ; ua(3D)
f1_atm3  = systemfunc("ls "+data_large+"/va_*01010000-*.nc")
in_atm3  = addfiles(f1_atm3,"r")                        ; va(3D)
f1_atm4  = systemfunc("ls "+data_large+"/hus_*01010000-*.nc")
in_atm4  = addfiles(f1_atm4,"r")       

; sh(3D)
;************** 2D(3hr-HIS 6hr-SSP585) ******************************

filebundles5=systemfunc("ls "+dataDIR+"/tas_*01010600-*.nc")
in_atm5  = addfiles(filebundles5,"r")     ; ta-2m(2D)
filebundles6 = systemfunc("ls "+dataDIR+"/uas_*01010600-*.nc")
in_atm6  = addfiles(filebundles6,"r")     ; ua-10m(2D)
filebundles7 = systemfunc("ls "+dataDIR+"/vas_*01010600-*.nc")
in_atm7  = addfiles(filebundles7,"r")     ; va-10m(2D)
filebundles8 = systemfunc("ls "+dataDIR+"/huss_*01010600-*.nc")
in_atm8  = addfiles(filebundles8,"r")    ; sh-2m(2D)
;************** 2D(6hr) ******************************
filebundles9 = systemfunc("ls "+dataDIR+"/ps_*01010600-*.nc")
in_atm9  = addfiles(filebundles9,"r")     ; ps(2D)
filebundles0 = systemfunc("ls "+dataDIR+"/psl_*01010600-*.nc")
in_atm0  = addfiles(filebundles0,"r")    ; psl(2D)
;************** 2D(day-HIS 6hr-SSP585) ******************************\
filebundlessst = systemfunc("ls "+dataDIR+"/ts_*0101-*.nc")
in_sst   = addfiles(filebundlessst,"r")    ; SST(daily)
;************** 3D SOIl(mon) ****************************************
filebundlestsoil = systemfunc("ls "+dataDIR+"/tsl_*01-*.nc")
in_TSOIL = addfiles(filebundlestsoil,"r")    ; soil temperature (daily)
filebundlesmsoil = systemfunc("ls "+dataDIR+"/mrsol_*01-*.nc")
in_MSOIL = addfiles(filebundlesmsoil,"r")    ; soil moisture (daily)
;************** 2D(fx) ******************************
in_zsfc  = addfile(dataDIR2+"orog_fx_MPI-ESM1-2-HR_historical_r1i1p1f1_gn.nc","r")   ; PHIS:static surface geopotential
in_land  = addfile(dataDIR2+"sftlf_fx_MPI-ESM1-2-HR_historical_r1i1p1f1_gn.nc","r")  ; static land mask


;----------- dims --------------------
lon   = in_atm1[0]->lon    ; atm grid
lat   = in_atm1[0]->lat
;----------- ti[0]me --------------------
time  = in_atm2[:]->time({date1:date1+0.75})

print(cd_calendar(in_atm2[:]->time({date1:date1+0.75}), 3))
;************************************************
; read needed variables from file
;************************************************
print("read variables in atm")



T = in_atm1[:]->ta({date1:date1+0.75},:,:,:)
U = in_atm2[:]->ua({date1:date1+0.75},:,:,:)
V = in_atm3[:]->va({date1:date1+0.75},:,:,:)
Q = in_atm4[:]->hus({date1:date1+0.75},:,:,:)

;===============================================

T2  = in_atm5[:]->tas({date2:date2+0.75},:,:)     ;near-surface data are in 3hr
U10 = in_atm6[:]->uas({date2:date2+0.75},:,:)
V10 = in_atm7[:]->vas({date2:date2+0.75},:,:)
Q2  = in_atm8[:]->huss({date2:date2+0.75},:,:)
PS  = in_atm9[:]->ps({date2:date2+0.75},:,:)
printVarSummary(PS)
SLP = in_atm0[:]->psl({date2:date2+0.75},:,:)
;Z = in_atm->Z3(:,::-1,:,:)                    ; "Geopotential Height (above sea level)"
TSOIL = in_TSOIL[:]->tsl(  (year-1970)*12+month-1,:,:,:)
MSOIL = in_MSOIL[:]->mrsol((year-1970)*12+month-1,:,:,:)

;======= check time size   =============
size=new((/10/),"integer")
var_name=(/"T","U","V","Q","T2","U10","V10","Q2","PS","SLP"/)
size(0)=dimsizes(T(:,0,0,0))
size(1)=dimsizes(U(:,0,0,0))
size(2)=dimsizes(V(:,0,0,0))
size(3)=dimsizes(Q(:,0,0,0))
size(4)=dimsizes(T2(:,0,0))
size(5)=dimsizes(U10(:,0,0))
size(6)=dimsizes(V10(:,0,0))
size(7)=dimsizes(Q2(:,0,0))
size(8)=dimsizes(PS(:,0,0))
size(9)=dimsizes(SLP(:,0,0))


do i = 0, 9
if (size(i).ne.4) then
print(var_name(i)+" time size error for"+date)
exit
end if
end do

;-------------------------
; SNOW_DEPTH = in_clm->SNOW_DEPTH
; SOIL_TEMP  = in_clm->TSOI(:,:,:,:)
; SOIL_LIQ   = in_clm->SOILLIQ(:,:,:,:)
; SNOW_DEPTH = in_clm2->SNOWDP(0,:,:)
; SOIL_ICE  = in_clm->SOILICE(:,:,:,:)
; SOIL_LIQ =  SOIL_LIQ+SOIL_ICE
; pftmask  = in_clm->pftmask
;-----  sst & ice
TSKIN = in_sst[:]->ts({date2+0.5},:,:)   ;daily


;------check missing value-----------------------
if (any(ismissing(T))) then
print(" Data T contains some missing value, exit")
exit
end if
if (any(ismissing(U))) then
print(" Data U contains some missing value, exit")
exit
end if
if (any(ismissing(V))) then
print(" Data V contains some missing value, exit")
exit
end if
if (any(ismissing(Q))) then
print(" Data Q contains some missing value, exit")
exit
end if
if (any(ismissing(PS))) then
print(" Data PS contains some missing value, exit")
exit
else if (any(PS.le.0))
print(" Data PS contains some uncommon value, exit")
exit
end if
end if
if (any(ismissing(SLP))) then
print(" Data SLP contains some missing value, exit")
exit
end if
if (any(ismissing(T2))) then
print(" Data T2 contains some missing value, exit")
exit
end if
if (any(ismissing(Q2))) then
print(" Data Q2 contains some missing value, exit")
exit
end if
if (any(ismissing(U10))) then
print(" Data U10 contains some missing value, exit")
exit
end if
if (any(ismissing(V10))) then
print(" Data V10 contains some missing value, exit")
exit
end if
if (any(ismissing(TSKIN))) then
print(" Data TSKIN contains some more then 5 missing value, exit")
exit
end if
;------------------------------------------------
if (year.le.2014) then
TSKIN6 = conform_dims(dimsizes(PS),TSKIN,(/1,2/))   ;daily to 6hr
TAVGSFC6  = TSKIN6
TSKIN:= TSKIN6
SST6 = TSKIN6
SST6 = where (ismissing(SST6), -1.E30, SST6) ; set missing value to default for METGRID.TBL
else
TSKIN6 = TSKIN                                      ;6hr to 6hr
TAVGSFC6  = TSKIN6
SST6 = TSKIN6
SST6 = where (ismissing(SST6), -1.E30, SST6) ; set missing value to default for METGRID.TBL
end if

;=====test======
;out_file=addfile("/scratch/users/xhr@umd.edu/DATA/merra2_ICBC/new/test_tskin.nc","c")
;out_file->TSKIN=TSKIN6
;out_file->T2m=T2
;==============

;-----------  topo and land mask
LMASK= in_land->sftlf(:,:)
LMASK:=where(LMASK.eq.0,0,1)  ; 0-ocean, 1-land  ; 0, 1
ZSFC = in_zsfc->orog(:,:)
PHIS = ZSFC*9.8
;===================================
; Get bottom level temperature for vertical extrapolation
;  TBOT = T(:,0,:,:)
;------------------------
; Calculate the pressures on each hybrid level (bottom up)
;f_ab=addfile("/scratch/users/xhr@umd.edu/DATA/GISS-E2-R/history/ta/ta_6hrLev_GISS-E2-R_historical_r6i1p3_195001010600-195007010000.nc","r")
p0   = 1
hyam = in_atm1[0]->a
;hyam:= hyam/p0
hybm = in_atm1[0]->b
hyai = in_atm1[0]->a_bnds(:,0)
hybi = in_atm1[0]->b_bnds(:,0)
print ("calculate P")
P = T
temp = pres_hybrid_ccm(PS,p0,hyam,hybm)
printVarSummary(P)
printVarSummary(PS)

exit
P = pres_hybrid_ccm(PS,p0,hyam,hybm)
; printMinMax(P,1)
; exit
;print(P(0,:,1,0))
;printVarSummary(P)
;==========================
print("calculate Z")
exit
; P0= 100000
; hyam:= hyam/P0
; hyai:= hyai/P0

P0= 1
tv= T*(1.+0.61*Q)
Z =cz2ccm(PS,PHIS,tv(:,::-1,:,:),P0,hyam,hybm,hyai,hybi)
Z = Z(:,::-1,:,:)
printVarSummary(Z)
; print((Z(0,60,100,80)))
; exit
; Uses stock RH function in ncl
print("calculate RH")
R = T
R = relhum(T,Q,P)
R = where(R.gt.100.0, 100.0, R)
; printMinMax(R,0)
; exit
R2= relhum(T2,Q2,PS)
R2= where(R2.gt.100.0, 100.0, R2)
;---------------------------------------------
;------------- set land vars
print("read variables in lnd")

SNOWW6 = PS ; dummy
SNOWW6 = 0
SNOWW6 = where (SNOWW6.lt.0, -1.E30, 1000*SNOWW6)
SNOWW6 = where (ismissing(SNOWW6), -1.E30, SNOWW6)

TSOIL1_6 = TSKIN
TSOIL1_6 = conform_dims(dimsizes(TSKIN),TSOIL(0,:,:),(/1,2/))
TSOIL1_6 = where (ismissing(TSOIL1_6), -1.E30, TSOIL1_6)

TSOIL2_6 = TSKIN
TSOIL2_6 = conform_dims(dimsizes(TSKIN),TSOIL(1,:,:),(/1,2/))
TSOIL2_6 = where (ismissing(TSOIL2_6), -1.E30, TSOIL2_6)

TSOIL3_6 = TSKIN
TSOIL3_6 = conform_dims(dimsizes(TSKIN),TSOIL(2,:,:),(/1,2/))
TSOIL3_6 = where (ismissing(TSOIL3_6), -1.E30, TSOIL3_6)

TSOIL4_6 = TSKIN
TSOIL4_6 = conform_dims(dimsizes(TSKIN),TSOIL(3,:,:),(/1,2/))
TSOIL4_6 = where (ismissing(TSOIL4_6), -1.E30, TSOIL4_6)

MSOIL1_6 = TSKIN
MSOIL1_6 = (conform_dims(dimsizes(TSKIN),MSOIL(0,:,:),(/1,2/)))/(1000*0.065)
MSOIL1_6 = where (ismissing(MSOIL1_6), -1.E30, MSOIL1_6)

MSOIL2_6 = TSKIN
MSOIL2_6 = (conform_dims(dimsizes(TSKIN),MSOIL(1,:,:),(/1,2/)))/(1000*0.254)
MSOIL2_6 = where (ismissing(MSOIL2_6), -1.E30, MSOIL2_6)

MSOIL3_6 = TSKIN
MSOIL3_6 = (conform_dims(dimsizes(TSKIN),MSOIL(2,:,:),(/1,2/)))/(1000*0.913)
MSOIL3_6 = where (ismissing(MSOIL3_6), -1.E30, MSOIL3_6)

MSOIL4_6 = TSKIN
MSOIL4_6 = (conform_dims(dimsizes(TSKIN),MSOIL(3,:,:),(/1,2/)))/(1000*2.902)
MSOIL4_6 = where (ismissing(MSOIL4_6), -1.E30, MSOIL4_6)

; fout=addfile("test.nc","c")
; fout->MSOIL1_6=MSOIL1_6
; exit
;------------------------
; get dimensions from dummy variable
dsizes_x = dimsizes(T)
ntim     = dsizes_x(0)
nlev     = dsizes_x(1)
nlat     = dsizes_x(2)
nlon     = dsizes_x(3)

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
; WRITE OUT DATA TO WRF INTERMEDIATE FORMAT (CALL FORTRAN SUBROUTINE VIA WRAPIT)
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
print("write out data to WRF intermediate files")

; Set the IM header information
; These are all passed to the write script as resources

opt = True
if (year.le.2014) then
opt@map_source             = "MPI/his CMIP6"
else
opt@map_source             = "MPI/ssp585 CMIP6"
end if
opt@projection             = 0  ;  must be 0, 1, 3, 4, 5  or "Equidistant_Lat_Lon", "Mercator", "Lambert", "Gaussian","Polar_Stereograhic"
opt@startloc               = "SWCORNER"
opt@startlon               = doubletofloat(lon(0))
opt@startlat               = doubletofloat(lat(0))
opt@deltalon               = doubletofloat(lon(1) - lon(0))
opt@deltalat               = doubletofloat(lat(1) - lat(0))
opt@nlats   = nlat/2
opt@is_wind_earth_relative = False
; nlats: Number of latitudes north of equator (for Gaussian grids)

; set the format to use for the date
date_format  = "%Y-%N-%D_%H:00:00"        		; 24 chars exact for binary file
date_format2 = "%Y-%N-%D_%H"                                  ; for filename
yyyy_format  = "%Y" 						; for output directory

; Set up field specific header information
;======================================
;======================================
FIELD_P       ="PRESSURE"
UNITS_P       ="Pa"
DESC_P        ="Pressure"
;======================================
;======================================
FIELD_T       ="TT"
UNITS_T       ="K"
DESC_T        ="Temperature"

FIELD_U       ="UU"
UNITS_U       ="m s-1"
DESC_U        ="Zonal Wind Speed"

FIELD_V       ="VV"
UNITS_V       ="m s-1"
DESC_V        ="Meridional Wind Speed"


FIELD_Q       ="SPECHUMD"
UNITS_Q       ="kg kg-1"
DESC_Q        ="Specific Humidity"

FIELD_R       ="RH"
UNITS_R       ="%"
DESC_R        ="Relative Humidity"

FIELD_Z       ="GHT"
UNITS_Z       ="m"
DESC_Z        ="Geopotential Height"

FIELD_SLP     ="PMSL"
UNITS_SLP     ="Pa"
DESC_SLP      ="Sea level pressure"
XLVL_SLP      = 201300.

FIELD_PS      ="PSFC"
UNITS_PS      ="Pa"
DESC_PS       ="Surface pressure"

FIELD_U10     ="UU"
UNITS_U10     ="m s-1"
DESC_U10      ="10 m Zonal Wind Speed"

FIELD_V10     ="VV"
UNITS_V10     ="m s-1"
DESC_V10      ="10 m Meridional Wind Speed"

FIELD_T2      ="TT"
UNITS_T2      ="K"
DESC_T2       ="2 m Temperature"

FIELD_Q2      ="SPECHUMD"
UNITS_Q2      ="kg kg-1"
DESC_Q2       ="2 m Specific Humidity"

FIELD_R2      ="RH"
UNITS_R2      ="%"
DESC_R2       ="2 m Relative Humidity"

FIELD_SNOWW6  ="SNOW"
UNITS_SNOWW6  ="kg m-2"
DESC_SNOWW6   ="Water Equivalent of Accum Snow Depth"

FIELD_TSKIN6  ="SKINTEMP"
UNITS_TSKIN6  ="K"
DESC_TSKIN6   ="Skin Temperature"

FIELD_TAVGSFC6="TAVGSFC"
UNITS_TAVGSFC6="K"
DESC_TAVGSFC6 ="Daily mean of surface air temperature"

FIELD_SST6    ="SST"
UNITS_SST6    ="K"; 25 chars exact
DESC_SST6     ="Sea Surface Temperature"

FIELD_ICE6    ="SEAICE"
UNITS_ICE6    ="fraction"
DESC_ICE6     ="Sea-Ice-Fraction"

FIELD_TSOIL1_6="ST000007"
UNITS_TSOIL1_6="K"
DESC_TSOIL1_6 ="Soil Temperature 0-7 cm layer"

FIELD_TSOIL2_6="ST007028"
UNITS_TSOIL2_6="K"
DESC_TSOIL2_6 ="Soil Temperature 7-28 cm layer"

FIELD_TSOIL3_6="ST028100"
UNITS_TSOIL3_6="K"
DESC_TSOIL3_6 ="Soil Temperature 28-100 cm layer"

FIELD_TSOIL4_6="ST100255"
UNITS_TSOIL4_6="K"
DESC_TSOIL4_6 ="Soil Temperature 100-255 cm layer"

FIELD_MSOIL1_6="SM000007"
UNITS_MSOIL1_6="fraction"
DESC_MSOIL1_6 ="Soil Moisture 0-7 cm layer"

FIELD_MSOIL2_6="SM007028"
UNITS_MSOIL2_6="fraction"
DESC_MSOIL2_6 ="Soil Moisture 7-28 cm layer"

FIELD_MSOIL3_6="SM028100"
UNITS_MSOIL3_6="fraction"
DESC_MSOIL3_6 ="Soil Moisture 28-100 cm layer"

FIELD_MSOIL4_6="SM100255"
UNITS_MSOIL4_6="fraction"
DESC_MSOIL4_6 ="Soil Moisture 100-255 cm layer"

FIELD_LMASK   ="LANDSEA"
UNITS_LMASK   ="proprtn"
DESC_LMASK    ="Land/Sea Flag; 0=Ocean; 1=Land"

FIELD_ZSFC    ="SOILHGT"
UNITS_ZSFC    ="m"
DESC_ZSFC     ="Terrain Elevation"


; Loop through each time period - do final calculations and write data to the IM format
;    PATH_FIL = outDIR + "/" + IM_root_name    ; try
PATH_FIL = IM_root_name
print("FIL= " + PATH_FIL)
do TIM = 0,ntim-1


HDATE = cd_string(time(TIM), date_format)                          ; set dates
OFILE = IM_root_name+":" + cd_string(time(TIM), date_format2)      ; figure the output file name so that we can clobber it
yyyy  = cd_string(time(TIM), yyyy_format)                          ; figure out the year so that we can make directories
print("HDATE= " + HDATE)
print("OFILE= " + OFILE)

system ("mkdir -p " + outDIR )	               	       ; make the output directories
system ("rm -f " + OFILE)                   ; delete the file, so that we don't append to an existing file
system ("rm -f " + outDIR + "/" + OFILE)                   ; delete the file, so that we don't append to an existing file

;=====================================
opt@date = HDATE

; write any non-level variables (including treament of soil temp/moisture profiles as single levels each)
; Due to the fact that other programs will read these files, and there we assume the fields to in a in given order,
; these order of the writes below are import for this application
print("-----------------")
;printVarSummary(MSOIL1_6)
print("-----------------")


opt@level = 200100.
wrf_wps_write_int(PATH_FIL,FIELD_LMASK,UNITS_LMASK,DESC_LMASK, LMASK(:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_ZSFC,UNITS_ZSFC,DESC_ZSFC,(ZSFC(:,:)),opt)
wrf_wps_write_int(PATH_FIL,FIELD_TSKIN6,UNITS_TSKIN6,DESC_TSKIN6, TSKIN6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_TAVGSFC6,UNITS_TAVGSFC6,DESC_TAVGSFC6, TAVGSFC6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_SST6,UNITS_SST6,DESC_SST6, SST6(TIM,:,:),opt)
;wrf_wps_write_int(PATH_FIL,FIELD_ICE6,UNITS_ICE6,DESC_ICE6, ICE6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_SNOWW6,UNITS_SNOWW6,DESC_SNOWW6, SNOWW6(TIM,:,:),opt)


wrf_wps_write_int(PATH_FIL,FIELD_TSOIL1_6,UNITS_TSOIL1_6,DESC_TSOIL1_6, TSOIL1_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_TSOIL2_6,UNITS_TSOIL2_6,DESC_TSOIL2_6, TSOIL2_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_TSOIL3_6,UNITS_TSOIL3_6,DESC_TSOIL3_6, TSOIL3_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_TSOIL4_6,UNITS_TSOIL4_6,DESC_TSOIL4_6, TSOIL4_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_MSOIL1_6,UNITS_MSOIL1_6,DESC_MSOIL1_6, MSOIL1_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_MSOIL2_6,UNITS_MSOIL2_6,DESC_MSOIL2_6, MSOIL2_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_MSOIL3_6,UNITS_MSOIL3_6,DESC_MSOIL3_6, MSOIL3_6(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_MSOIL4_6,UNITS_MSOIL4_6,DESC_MSOIL4_6, MSOIL4_6(TIM,:,:),opt)




opt@level = XLVL_SLP	; Need a different level for SLP
wrf_wps_write_int(PATH_FIL,FIELD_SLP,UNITS_SLP,DESC_SLP, SLP(TIM,:,:),opt)

opt@level = 200100.		; Reset level back to regular surface value
wrf_wps_write_int(PATH_FIL,FIELD_PS,UNITS_PS,DESC_PS, PS(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_U10,UNITS_U10,DESC_U10, U10(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_V10,UNITS_V10,DESC_V10, V10(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_T2,UNITS_T2,DESC_T2, T2(TIM,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_R2,UNITS_R2,DESC_R2, R2(TIM,:,:),opt)

; TonP=T(TIM,::-1,:,:)
; UonP=U(TIM,::-1,:,:)
; VonP=V(TIM,::-1,:,:)
; RonP=R(TIM,::-1,:,:)
; ZonP=Z(TIM,::-1,:,:)

;;;;modified by OSCAR testing level reversion
TonP=T(TIM,:,:,:)
UonP=U(TIM,:,:,:)
VonP=V(TIM,:,:,:)
RonP=R(TIM,:,:,:)
ZonP=Z(TIM,:,:,:)
;;;;modified by OSCAR testing level reversion

; Write each level of the 3D fields out separately
;do LEV=0,dimsizes(pnew)-1
; p1d=P&lev
; printVarSummary(p1d)
do LEV=0,60   ;   ;delete top layer of hybrid levls pressure lt 5hpa
opt@level = doubletofloat(61-LEV)

wrf_wps_write_int(PATH_FIL,FIELD_U,UNITS_U,DESC_U, UonP(LEV,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_V,UNITS_V,DESC_V, VonP(LEV,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_T,UNITS_T,DESC_T, TonP(LEV,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_R,UNITS_R,DESC_R, RonP(LEV,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_Z,UNITS_Z,DESC_Z, ZonP(LEV,:,:),opt)
wrf_wps_write_int(PATH_FIL,FIELD_P,UNITS_P,DESC_P, P(TIM,LEV,:,:),opt)

end do

; move the file to the outDIR directory
print ("mv " + OFILE + "   " + outDIR + "/" +YR+"/")
system ("mv " + OFILE + "   " + outDIR + "/" +YR+"/")
print("  ")

delete(HDATE)
delete(OFILE)
end do


