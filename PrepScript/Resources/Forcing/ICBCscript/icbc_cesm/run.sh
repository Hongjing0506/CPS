#!/bin/bash
#set -x
#Author: SunLei; 20170512
#Modify: Haoran; 20190718 for Merra2 ICBC
#Modify: Haoran; 20200322 for GISS ICBC
#Modify: Haoran; 20200426 for CESM(CMPI6) ICBC
#Modify: Haoran; 20200505 for CESM(CMPI6) US ICBC
#Modify: Haoran; 20201112 for CESM(CMPI6) US ICBC （no leap year）
#Modify: Haoran; 20210312 for CESM(CMPI6) CN ICBC （no leap year）

yr=$1
mon=$2
daysta=$3
dayend=$4
# "+YR+MON+"_met
yrstr=`printf "%04d" $yr`
monstr=`printf "%02d" $mon`
daystastr=`printf "%02d" $daysta`
dayendstr=`printf "%02d" $dayend`
BASE_DIR=/share/home/dq048/oscar/future/hist/runmet_cesm/hist/CESM_MET/${yrstr}_${monstr}_met/
GCM_DIR=/share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM/


CWPS_DIR=/share/home/dq048/CWRF/CWPS/CWRF-CWPS_master/
GEO_DIR=/share/home/dq048/CWRF/CWPS/CWPS_static/
NML_DIR=/share/home/dq048/oscar/future/hist/icbc_cesm/
EXE_DIR=/share/home/dq048/CWRF/CWPS/exes/

start_time=${yrstr}${monstr}${daystastr}00
#start_time=${yr}022700
#start_time=${yr}100100
# end_time=${yr}123118
end_time=${yrstr}${monstr}${dayendstr}18
#end_time=$[yr+1]010100
#end_time=${yr}030118
#end_time=${yr}103118
echo "start_time: "${start_time}
echo "end_time: "${end_time}
prefix=("CESM")

#export NETCDF=/home/export/online1/zhaoyang/mylib/netcdf/4.x.x
#export PATH=${NETCDF}/bin:/scratch/users/xhr@umd.edu/DATA/CWRF_static:${PATH}
#export LD_LIBRARY_PATH=${NETCDF}/lib:${LD_LIBRARY_PATH}

/bin/rm -rf $BASE_DIR
echo BASE_DIR: ${BASE_DIR}
if [ ! -d $BASE_DIR ]; then
#base dir for processing data
mkdir -p $BASE_DIR
#make temporary dictionary to save the line files
mkdir -p ${BASE_DIR}/CESM
#mkdir ${BASE_DIR}/MET_ERI # folder to store eri met files
fi


#link ERI-MET files into temporary dictionary

# echo "link needed ERI-MET files into temporary dictionary"
# cd ${ERI_MET_DIR}
# for yr in `seq ${start_time:0:4} ${end_time:0:4}`;do
# cd ${ERI_MET_DIR}$yr
# for fname in `ls met_em*` ;do
# date2=`echo ${fname} | cut -d. -f3`
# year=`echo ${date2:0:4}`
# mon=`echo ${date2:5:2}`
# day=`echo ${date2:8:2}`
# hour=`echo ${date2:11:2}`
# date1=`echo ${year}${mon}${day}${hour}`
# if [ ${date1} -ge ${start_time} ] && [ ${date1} -le ${end_time} ]; then #note: space before and bracket
# #echo $date1
# ln -sf ${ERI_MET_DIR}${yr}/${fname}  ${BASE_DIR}/MET_ERI
# fi
# if [ ${date1} -eq ${end_time} ]; then
# break
# fi
# done
# done


#link CESM files into temporary dictionary
echo "link needed CESM files into Basedir"
for yr in `seq ${start_time:0:4} ${end_time:0:4}`;do
cd ${GCM_DIR}${yr}
pwd
for fname in `ls CESM:*`;do
date1=`echo ${fname} | cut -d: -f2 | awk '{split($0,a,"-");print a[1]a[2]a[3]}' | awk '{split($0,a,"_"); print a[1]a[2]}'`
if [ ${date1} -ge ${start_time} ] && [ ${date1} -le ${end_time} ]; then
ln -sf ${GCM_DIR}$yr/${fname}  ${BASE_DIR}/
fi
if [ ${date1} -eq ${end_time} ]; then
break
fi
done
done


#link oisst nc files into temporary dictionary

# for yr in `seq ${start_time:0:4} ${end_time:0:4}`;do
# cd ${SST_DIR}$yr
# for fname in `ls avhrr*` ; do
# date1=`echo ${fname} | cut -d. -f2`
# if [ ${date1}00 -ge ${start_time} ] && [ ${date1}00 -le ${end_time} ]; then
# ln -sf ${SST_DIR}$yr/${fname}  ${BASE_DIR}/SST
# fi
# if [ ${date1} -eq ${end_time} ]; then
# break
# fi
# done
# done

#add needed cwps files into Basedir
echo "add needed cwps files into Basedir"
cd ${BASE_DIR}
#ln -s /scratch/users/xhr@umd.edu/DATA/CWRF_static/geo_US_30km/geo/geo_em.d01.nc .  #US_domain
ln -s ${GEO_DIR}/geo_em.d01_updated201705.nc   geo_em.d01.nc
# ln -s ${GEO_DIR}/geo_em.d01_veg.nc   geo_em.d01.nc
ln -s ${EXE_DIR}/* .
cp -s ${GEO_DIR}/METGRID.TBL.sq.nolandsea   METGRID.TBL          # use METGRID.TBL from sunqing
ln -s ${CWPS_DIR}/ungrib/Variable_Tables .
#ln -s ${GEO_DIR}/SOILHGT_MERRA2  soilhgt_merra2  # soilhgt for merra2 in intermediate format
cp ${NML_DIR}/namelist.wps.CESM   namelist.wps
cp ${CWPS_DIR}/link_grib.csh .

# modify interval start&end time
str="interval_seconds =21600,"
sed -i "/interval_seconds/c${str}"  namelist.wps
str="start_date = ${start_time:0:4}-${start_time:4:2}-${start_time:6:2}_${start_time:8:2}:00:00,"
sed -i "/start_date/c${str}" namelist.wps
str="end_date = ${end_time:0:4}-${end_time:4:2}-${end_time:6:2}_${end_time:8:2}:00:00,"
sed -i "/end_date/c${str}" namelist.wps


# echo "===============>sst process<=========================="
# #sst process
# cd ${BASE_DIR}/SST
# echo "change SST files from nc into intermediate"
# for fname in `ls avhrr*`
# do
# date1=`echo ${fname} | cut -d. -f2`
# nc2im_oisst  ${fname}   ../SST:${date1:0:4}-${date1:4:2}-${date1:6:2}_00
# done
# cd ${BASE_DIR}
# for fname in `ls SST\:*`
# do
# f1=`echo ${fname} | cut -d'_' -f1`
# for num_t in  06 12 18
# do
# cp ${fname} ${f1}_${num_t}
# done
# done


#run mod_levs.exe to unify the vertical layers
# echo "mod_lev===>processing MERRA2 varible"
# for fname in `ls  ${BASE_DIR}/MERRA/*`  ; do
# tmp_name=`echo $fname | awk -F'/' '{print $NF}'` # get the last field
# ./mod_levs.exe ${fname} ${tmp_name} &>> mod_lev.ls
# done


echo "===============>CESM Metgrid process<=========================="
# edit namelist.wps&metgrid
str="fg_name = \"CESM\" "
sed  -i "/fg_name/c${str}" namelist.wps
#str="constants_name= \"soilhgt_merra2\","
#sed  -i "/constants_name/c${str}" namelist.wps
str="opt_output_from_metgrid_path= \"./\","
sed  -i "/opt_output_from_metgrid_path/c${str}" namelist.wps
./metgrid.exe &> metgrid.CESM.ls

echo "===============>CESM met files process<=========================="
#merra_met_mod_test.py ${BASE_DIR}/MET_ERI ${BASE_DIR}

echo "===============>SST Processing<=========================="
# optimize the sst in water gird including lake
fs=(`ls met_em*`)
for (( c=0; c<=${#fs[@]}-1; c=c+4 ))
do
YYYYMMDD=`echo ${fs[c]}| cut -d'.' -f 3 | cut -d'_' -f 1 `  #form YYYY-MM-DD
YYYYMMDD=${YYYYMMDD:0:4}${YYYYMMDD:5:2}${YYYYMMDD:8:2}   #YYYYMMDD
./sst_avg ${YYYYMMDD}
echo "processing=====>"${YYYYMMDD}
done



exit 
