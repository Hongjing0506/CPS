;******************************************************************************
; NCL script to convert CESM1 (ds316.0) data to Intermediate file format
;
; This script does not look for specific dates in a file - simply convert
; all dates in the input file to IM format, so it is the users responsibility
; to ensure the input data is consistent

;2020/09/23 input or not 取消，添加土壤数据的写入，使用mpi 月土壤数据
;2020/11/8  修改以适用CESM CMIP6 数据，无 T2 U10 V10 Q2数据
;******************************************************************************

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_csm.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/contrib/cd_string.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/contributed.ncl"
load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/popRemap.ncl"

  outDIR="/share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM"
;******************************************************************************
; Which CASE are we doing.
; CASE is only used for naming conventions, but make sure this is correct,
; else you could clobber exisiting files.
;******************************************************************************
if ( .not. isvar("YR") ) then
  print("We need to know which YR we are running")
  exit
end if

if ( .not. isvar("MON") ) then
  print("We need to know which MON we are running")
  exit
end if

if ( .not. isvar("DAY") ) then
  print("We need to know which DAY we are running")
  exit
end if

if ( .not. isvar("IM_root_name") ) then
  IM_root_name = "CESM"
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
  topt=0
  units = "days since 0001-01-01 00:00:00"
  topt@calendar = "noleap"
  date1 = cd_inv_calendar(year,month,day,hour,minute,second,units, topt)
  date=sprinti("%0.2i",YR)+sprinti("%0.2i",MON)+sprinti("%0.2i",DAY)
  print("================opening files======================")
  print("=         date: "+date+"  "+date1+"               =")
  print("================opening files======================")
;************************************************
; file handling
;************************************************
  dataDIR="/share/home/dq048/oscar/future/hist/cesm"

;************** 3D(6hr) ******************************
if (year.lt.1980) then
  file_start  ="197001010000"
  file_start2 ="19700101"
else if (year.lt.1990) then
  file_start  ="198001010000"
  file_start2 ="19800101"
else if (year.lt.2000) then
  file_start  ="199001010000"
  file_start2 ="19900101"
else if (year.lt.2010) then
  file_start  ="200001010000"
  file_start2 ="20000101"
else
  file_start  ="201001010000"
  file_start2 ="20100101"
end if
end if
end if
end if
; print(year)
; print(file_start)

  f1_atm1  = systemfunc("ls "+dataDIR+"/ta_*"+file_start+"-*.nc")
  in_atm1  = addfile(f1_atm1,"r")                        ; ta(3D)
  f1_atm2  = systemfunc("ls "+dataDIR+"/ua_*"+file_start+"-*.nc")
  in_atm2  = addfile(f1_atm2,"r")                        ; ua(3D)
  f1_atm3  = systemfunc("ls "+dataDIR+"/va_*"+file_start+"-*.nc")
  in_atm3  = addfile(f1_atm3,"r")                        ; va(3D)
  f1_atm4  = systemfunc("ls "+dataDIR+"/hus_*"+file_start+"-*.nc")
  in_atm4  = addfile(f1_atm4,"r")                        ; sh(3D)
;************** 2D(no data from CESM CIMP6) ******************************
  f1_atm5  = systemfunc("ls "+dataDIR+"/tas_*"+file_start2+"-*.nc")
  in_atm5  = addfile(f1_atm5,"r")                          ; ta-2m(2D)
  ; in_atm6  = addfile(dataDIR2+"uas_"+year+".nc","r")     ; ua-10m(2D)
  ; in_atm7  = addfile(dataDIR2+"vas_"+year+".nc","r")     ; va-10m(2D)
  ; in_atm8  = addfile(dataDIR2+"huss_"+year+".nc","r")    ; sh-2m(2D)
;************** 2D(6hr) ******************************
  f1_sf1   = systemfunc("ls "+dataDIR+"/ps_*"+file_start+"-*.nc")
  in_atm9  = addfile(f1_sf1,"r")                        ; ps(2D)
;   f1_sf2   = systemfunc("ls "+dataDIR+"/psl_*"+file_start2+"-*.nc")
;   in_atm0  = addfile(f1_sf2,"r")                        ; psl(2D)
;************** 2D(day-HIS ) ******************************
  ; f1_sf3   = systemfunc("ls "+dataDIR+"/tslsi_day_CESM2_historical_r11i1p1f1_gn_19500101-19991231.nc")
  ; in_skt   = addfile(f1_sf3,"r")
  ; in_sst   = addfile(dataDIR+"//tos_Oday_CESM2_historical_r11i1p1f1_gn_19500102-20000101-new.nc","r")     ; SST(daily)
;************** 3D SOIl(daily) ****************************************
  ; in_TSOIL = addfile(dataDIR+"/tsl_Eday_CESM2_historical_r11i1p1f1_gn_19500101-19991231.nc","r")  ;soil temperature (daily)
  ; in_MSOIL = addfile(dataDIR+"/mrsol_Eday_CESM2_historical_r11i1p1f1_gn_19500101-19991231.nc","r")  ;soil moisture (daily)
;************** 2D(fx) ******************************
  dataDIR3 = "/share/home/dq048/oscar/future/hist/cesm/"
  in_zsfc  = addfile(dataDIR3+"orog_fx_CESM2_historical_r11i1p1f1_gn.nc","r")   ; PHIS:static surface geopotential
  ;in_land  = addfile(dataDIR3+"sftlf_fx_CESM2_historical_r11i1p1f1_gn.nc","r")  ; static land mask
  in_land  = addfile(dataDIR3+"sftlf_fx_CESM2_historical_r11i1p1f1_gn.nc","r")
  in_phis  = addfile(dataDIR3+"b.e21.BHIST.f09_g17.CMIP6-historical.010.cam.h0.1999-12.nc","r")


  if (year.le.1999) then
  f1_sf3   = systemfunc("ls "+dataDIR+"/tslsi_day_CESM2_historical_r11i1p1f1_gn_19500101-19991231.nc")
  in_skt   = addfile(f1_sf3,"r")
  in_sst   = addfile(dataDIR+"/tos_all_grid.nc","r")     ; SST(daily)
  in_TSOIL = addfile(dataDIR+"/tsl_Eday_CESM2_historical_r11i1p1f1_gn_19500101-19991231.nc","r")  ;soil temperature (daily)
  in_MSOIL = addfile(dataDIR+"/mrsol_Eday_CESM2_historical_r11i1p1f1_gn_19500101-19991231.nc","r")  ;soil moisture (daily)
else
  f1_sf3   = systemfunc("ls "+dataDIR+"/tslsi_day_CESM2_historical_r11i1p1f1_gn_20000101-20150101.nc")
  in_skt   = addfile(f1_sf3,"r")
  in_sst   = addfile(dataDIR+"/tos_all_grid.nc","r")     ; SST(daily)
  in_TSOIL = addfile(dataDIR+"/tsl_Eday_CESM2_historical_r11i1p1f1_gn_20000101-20150101.nc","r")  ;soil temperature (daily)
  in_MSOIL = addfile(dataDIR+"/mrsol_Eday_CESM2_historical_r11i1p1f1_gn_20000101-20150101.nc","r")  ;soil moisture (daily)
end if











  LMASK = in_land->sftlf(:,:)
  LMASK = where(LMASK.le.12,0,1)  ; 0-ocean, 1-land  ; 0, 1
  ZSFC  = in_zsfc->orog(:,:)
  PHIS  = in_phis->PHIS(0,:,:)
;----------- dims --------------------
  lon   = in_atm1->lon    ; atm grid
  lat   = in_atm1->lat
;----------- time --------------------
 time  = in_atm1->time({date1:date1+0.75})
;  print(time)
;************************************************
; read needed variables from file
;************************************************
; we need to read in bottom --> top
  print("read variables in atm")
  ;printVarSummary(in_atm1->ta)
  T = in_atm1->ta({date1:date1+0.75},:,:,:)       ;Ta  in CESM his  1 --> 32 bottom --> top
;   print(num(ismissing(T)))
  U = in_atm2->ua({date1:date1+0.75},::-1,:,:)    ;Ua  in CESM his  1 --> 32 bottom --> top
  V = in_atm3->va({date1:date1+0.75},::-1,:,:)    ;Va  in CESM his  1 --> 32 bottom --> top
  Q = in_atm4->hus({date1:date1+0.75},::-1,:,:)   ;hus in CESM his  1 --> 32 bottom --> top
;===============================================
  print("read variables on surface")
  T2  = in_atm5->tas({date1:date1+0.25},:,:)     ;daily
  U10 = U(:,0,:,:)
  V10 = V(:,0,:,:)
  PS  = in_atm9->ps({date1:date1+0.75},:,:)
  ; SLP = in_atm0->psl({date1:date1+0.75},:,:)
  ;-----  sst and  skt
  TSKIN = in_skt->tslsi({date1:date1+0.25},:,:)
;   printVarSummary(TSKIN)    ;daily
  SST   = in_sst->tos({date1:date1+0.25},:,:)+273.16   ;daily



  TSKIN = where(ismissing(TSKIN),SST,TSKIN)
  ;   system("rm -f test_tskin.nc")
;   fout=addfile("test_tskin.nc","c")
;   fout->TSKIN=TSKIN
  do i = 0,192-1
    TSKIN(0,i,:)=where(ismissing(TSKIN(0,i,:)),dim_avg_n(TSKIN(0,i,:), 0),TSKIN(0,i,:))
  end do
;===============================================
  print("read variables in soil")
  TSOIL = in_TSOIL->tsl({date1:date1+0.25},:19,:,:)    ;daily
  MSOIL = in_MSOIL->mrsol({date1:date1+0.25},:,:,:)   ;daily
  depth = in_MSOIL->depth

; Calculate the pressures on each hybrid level (bottom up)
f_ab=addfile("/share/home/dq048/oscar/future/hist/cesm/b.e21.BHIST.f09_g17.CMIP6-historical.010.cam.h0.1999-12.nc","r")
P0   = f_ab->P0
hyam = f_ab->hyam(::-1)
hybm = f_ab->hybm(::-1)
hyai = f_ab->hyai(::-1)
hybi = f_ab->hybi(::-1)
print ("calculate P")
P = T
P = pres_hybrid_ccm(PS,P0,hyam,hybm)




  SLP:=new((/4,192,288/),"float")
  do i = 0,3
  SLP(i,:,:)=pslec(T(i,0,:,:),PHIS,PS(i,:,:),P(i,0,:,:))
  end do
; outfilname="testslp.nc"
; system("rm -f "+outfilname)
; outfil=addfile(outfilname, "c")
; outfil->SLP=SLP
; outfil->T=T
; outfil->T=T

  ; printVarSummary(PS)
  ; printVarSummary(SLP)
  ; printVarSummary(TSKIN)
  ; printVarSummary(SST)
  ; printVarSummary(TSOIL)
  ; printVarSummary(MSOIL)
;======= check time size   =============
size=new((/6/),"integer")
var_name=(/"T","U","V","Q","PS","SLP"/)
  size(0)=dimsizes(T(:,0,0,0))
  size(1)=dimsizes(U(:,0,0,0))
  size(2)=dimsizes(V(:,0,0,0))
  size(3)=dimsizes(Q(:,0,0,0))
  size(4)=dimsizes(PS(:,0,0))
  size(5)=dimsizes(SLP(:,0,0))
printVarSummary(SLP)
printVarSummary(PS)
do i = 0, 5
  if (size(i).ne.4) then
    print(var_name(i)+" time size error")
    exit
  end if
end do

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
if (any(ismissing(TSKIN(0,{0:75},1:)))) then
 print(" Data TSKIN contains some more then 5 missing value, exit")
 exit
end if
;------------------------------------------------
  TSKIN6 = conform_dims(dimsizes(PS),TSKIN,(/0,1,2/))   ;daily to 6hr
  TAVGSFC6  = TSKIN6
  TSKIN:= TSKIN6
  ;SST6 = conform_dims(dimsizes(PS),SST,(/0,1,2/))        ;daily to 6hr
  ;SST6 = where (ismissing(SST6), -1.E30, SST6) ; set missing value to default for METGRID.TBL
  ;SST6@_FillValue=-1.E30
  SST6 = TSKIN6
  T2  := conform_dims(dimsizes(PS),T2,(/0,1,2/))     ;daily to 6hr
;-----------  topo and land mask


;===================================
; Get bottom level temperature for vertical extrapolation
;  TBOT = T(:,0,:,:)
;------------------------

; printVarSummary(P)
; printMinMax(P(0,31,:,:)/100.,0)
; exit

;==========================
print("calculate Z")
  tv= T*(1.+0.61*Q)
  Z =cz2ccm(PS,PHIS,tv(:,::-1,:,:),P0,hyam,hybm,hyai,hybi)
  Z = Z(:,::-1,:,:)
;printVarSummary(Z)
;printMinMax(Z(0,8,:,:),0)

; Uses stock RH function in ncl
  print("calculate RH")
  R = T
  R = relhum(T,Q,P)
  R = where(R.gt.100.0, 100.0, R)
  R2= R(:,0,:,:)
 ;printMinMax(R,0)

;  outfilname="testRR.nc"
; system("rm -f "+outfilname)
; outfil=addfile(outfilname, "c")
; outfil->P=P
; outfil->Q=Q
; outfil->T=T
; outfil->R=R

; exit()

;---------------------------------------------
;------------- Interpolate ST and SM----------
 deptho = (/0.07,0.28,1.0,2.55/)
 depthoT = (/0.035,0.175,0.64,1.775/)
 ;print(TSOIL(0,:,130,80))
 TSOIL1 := linint1_n_Wrap(depth,TSOIL,False,depthoT,0,1)
 ;printVarSummary(TSOIL1)
 ;print(TSOIL1(0,:,130,80))
 zt=(/0.,0.07,0.28,1.0/)
 zb=(/0.07,0.28,1.0,2.55/)
 dz=(/0.07,0.21,0.72,1.55/)
 ;cal fraction
 q      =new((/1,20,192,288/),"float")
 MSOIL1 =MSOIL(:,0:3,:,:)
 MSOIL1 =0

 z      =new((/21/),"double")
 z(0)   =0
 z(1:20)=depth
 z:=doubletofloat(z)

do i = 0,dimsizes(depth)-1
    q(:,i,:,:)=MSOIL(:,i,:,:)/(z(i+1)-z(i))
end do

do n = 0, 3
  xt:=zt(n)
  xb:=zb(n)
  do k=1,20
   if ((k.eq.1.and.xt.le.z(k-1)).or.(z(k-1).le.xt.and.xt.lt.z(k))) then     ;---the top boundary
      MSOIL1(:,n,:,:)=MSOIL1(:,n,:,:)+q(:,k-1,:,:)*(z(k)-xt)
   else if ((k.eq.20.and.xb.ge.z(k)).or.(z(k-1).le.xb.and.xb.lt.z(k))) then ;---the bottom boundary
      MSOIL1(:,n,:,:)=MSOIL1(:,n,:,:)+q(:,k-1,:,:)*(xb-z(k-1))
   else if (xt.le.z(k-1).and.z(k).le.xb) then                               ;---the inner layers
      MSOIL1(:,n,:,:)=MSOIL1(:,n,:,:)+q(:,k-1,:,:)*(z(k)-z(k-1))
   end if
   end if
   end if
  end do
end do
do i = 0,3
    MSOIL1(:,i,:,:)=MSOIL1(:,i,:,:)/(1000*dz(i))
end do


 SNOWW6 = PS ; dummy
 SNOWW6 = 0
 SNOWW6 = where (SNOWW6.lt.0, -1.E30, 1000*SNOWW6)
 SNOWW6 = where (ismissing(SNOWW6), -1.E30, SNOWW6)

 TSOIL1_6 = TSKIN
 TSOIL1_6 = conform_dims(dimsizes(TSKIN),TSOIL1(:,0,:,:),(/0,1,2/))
 TSOIL1_6 = where (ismissing(TSOIL1_6), 285, TSOIL1_6)

 TSOIL2_6 = TSKIN
 TSOIL2_6 = conform_dims(dimsizes(TSKIN),TSOIL1(:,1,:,:),(/0,1,2/))
 TSOIL2_6 = where (ismissing(TSOIL2_6), 285, TSOIL2_6)

 TSOIL3_6 = TSKIN
 TSOIL3_6 = conform_dims(dimsizes(TSKIN),TSOIL1(:,2,:,:),(/0,1,2/))
 TSOIL3_6 = where (ismissing(TSOIL3_6), 285, TSOIL3_6)

 TSOIL4_6 = TSKIN
 TSOIL4_6 = conform_dims(dimsizes(TSKIN),TSOIL1(:,3,:,:),(/0,1,2/))
 TSOIL4_6 = where (ismissing(TSOIL4_6), 285, TSOIL4_6)

 MSOIL1_6 = TSKIN
 MSOIL1_6 = conform_dims(dimsizes(TSKIN),MSOIL1(:,0,:,:),(/0,1,2/))
 MSOIL1_6 = where (ismissing(MSOIL1_6), 1, MSOIL1_6)

 MSOIL2_6 = TSKIN
 MSOIL2_6 = conform_dims(dimsizes(TSKIN),MSOIL1(:,1,:,:),(/0,1,2/))
 MSOIL2_6 = where (ismissing(MSOIL2_6), 1, MSOIL2_6)

 MSOIL3_6 = TSKIN
 MSOIL3_6 = conform_dims(dimsizes(TSKIN),MSOIL1(:,2,:,:),(/0,1,2/))
 MSOIL3_6 = where (ismissing(MSOIL3_6), 1, MSOIL3_6)

 MSOIL4_6 = TSKIN
 MSOIL4_6 = conform_dims(dimsizes(TSKIN),MSOIL1(:,3,:,:),(/0,1,2/))
 MSOIL4_6 = where (ismissing(MSOIL4_6), 1, MSOIL4_6)
 ; printMinMax(MSOIL4_6,0)
 ; fout=addfile("test.nc","c")
 ; fout->TSOIL1_6=TSOIL1_6
 ; fout->MSOIL1_6=MSOIL1_6
 ; exit

 ; TSOIL1_6 = TSKIN
 ; TSOIL1_6 = 273.16
 ; TSOIL1_6 = where (ismissing(TSOIL1_6), -1.E30, TSOIL1_6)
 ;
 ; TSOIL2_6 = TSKIN
 ; TSOIL2_6 = 273.16
 ; TSOIL2_6 = where (ismissing(TSOIL2_6), -1.E30, TSOIL2_6)
 ;
 ; TSOIL3_6 = TSKIN
 ; TSOIL3_6 = 273.16
 ; TSOIL3_6 = where (ismissing(TSOIL3_6), -1.E30, TSOIL3_6)
 ;
 ; TSOIL4_6 = TSKIN
 ; TSOIL4_6 = 273.16
 ; TSOIL4_6 = where (ismissing(TSOIL4_6), -1.E30, TSOIL4_6)
 ;
 ; MSOIL1_6 = TSKIN
 ; MSOIL1_6 = 1.
 ; MSOIL1_6 = where (ismissing(MSOIL1_6), -1.E30, MSOIL1_6)
 ;
 ; MSOIL2_6 = TSKIN
 ; MSOIL2_6 = 1.
 ; MSOIL2_6 = where (ismissing(MSOIL2_6), -1.E30, MSOIL2_6)
 ;
 ; MSOIL3_6 = TSKIN
 ; MSOIL3_6 = 1.
 ; MSOIL3_6 = where (ismissing(MSOIL3_6), -1.E30, MSOIL3_6)
 ;
 ; MSOIL4_6 = TSKIN
 ; MSOIL4_6 = 1.
 ; MSOIL4_6 = where (ismissing(MSOIL4_6), -1.E30, MSOIL4_6)


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
    opt@map_source             = "CESM/his CMIP6"
  else
    opt@map_source             = "CESM/ssp585 CMIP6"
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


    ; Write each level of the 3D fields out separately
    do LEV=0,30   ;   ;delete top layer of hybrid levls pressure lt 5hpa
      opt@level = doubletofloat(31-LEV)

      wrf_wps_write_int(PATH_FIL,FIELD_U,UNITS_U,DESC_U, U(TIM,LEV,:,:),opt)
      wrf_wps_write_int(PATH_FIL,FIELD_V,UNITS_V,DESC_V, V(TIM,LEV,:,:),opt)
      wrf_wps_write_int(PATH_FIL,FIELD_T,UNITS_T,DESC_T, T(TIM,LEV,:,:),opt)
      wrf_wps_write_int(PATH_FIL,FIELD_R,UNITS_R,DESC_R, R(TIM,LEV,:,:),opt)
      wrf_wps_write_int(PATH_FIL,FIELD_Z,UNITS_Z,DESC_Z, Z(TIM,LEV,:,:),opt)
      wrf_wps_write_int(PATH_FIL,FIELD_P,UNITS_P,DESC_P, P(TIM,LEV,:,:),opt)

    end do

    ; move the file to the outDIR directory
      system ("mkdir -p " + outDIR + "/" +YR+"/")
      print ("mv " + OFILE + "   " + outDIR + "/" +YR+"/")
      system ("mv " + OFILE + "   " + outDIR + "/" +YR+"/")
      print("  ")

     delete(HDATE)
     delete(OFILE)
  end do


