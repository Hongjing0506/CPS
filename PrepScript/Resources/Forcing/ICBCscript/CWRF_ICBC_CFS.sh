#!/bin/bash
#set -x
#SunLei; 20170325
#First Modified ZhangHan; 20171111
#Second Modified ZhangHan; 20171207
#ThisScript was produced by minecraft.py at 2017-12-18 16:39:33.030349
#cwrf preprocessing for CFSRR(ungrib->metgrid->real.exe->vbs.exe )
#Tip1: one variable in grib1 file can be only used once in the Variable from bottom to end (SST>SKINTEMP)
#Tip2(wrfsst): if no SST=>  # value no in wrfsst(i.e. the sst was set to constant);
#              if has sst=> # wrfsst has daily updated values masked by landmask (0:water;1:land)
#Tip3(2D sst in wrfinput):just the renamed skintemp and then must be masked by landmask

BASE_PATH_DIR=/home/chengs24/stu01/CFSV2_ICBCdata/040100/  #存放ICBC的路径
#命令行输入起始时间和终止时间 格式示例./CWRF_ICBC_CFS.sh 2016040100 2016110100
start_time=$1
end_time=$2
year=${start_time:0:4}
START_HOUR="040100" #起报时间
#========================================================
CWPS_DIR=/tera07/zhangsl/wumej22/Omarjan/CRESMDataPrep/CRESM_ToolBox/ToolBox/CWRF-CWPS/
CFSRR_DIR=/home/chengs24/stu02/CFSV2/operational-9-month-forecast/
CFSV2data_2d="${CFSRR_DIR}/6-hourly-flux/"
CFSV2data_3d="${CFSRR_DIR}/6-hourly-by-pressure/"
GEO_DIR=/home/chengs24/stu01/CFSV2_ICBCdata/geo_CFSv2_pearl15/
NML_DIR=/home/chengs24/stu01/CFSV2_ICBCdata/geo_CFSv2_pearl15/
EXE_DIR=/tera07/zhangsl/wumej22/Omarjan/CRESMDataPrep/CRESM_ToolBox/ToolBox/CWRF_Tools/executable/



prefix=("2D" "3D" "SST" ) #"SOIL" "SST"


DateForm()
{
str_i=$1
str_o="${str_i:0:4}-${str_i:4:2}-${str_i:6:2} ${str_i:8:2}:00:00"
sec=`date -d "${str_o}" +%s`
((sec=sec-0))
time=`date -d @${sec} +%Y%m%d%H`
echo ${time}
}

GetDate2()
{
yyyymmddhh=`echo $1 | cut -d'.' -f1|cut -d'f' -f3`
echo $yyyymmddhh
}

GetDate3()
{
yyyymmddhh=`echo $1 | cut -d'.' -f1|cut -d'f' -f2`
echo $yyyymmddhh
}



start_time_s=$(DateForm ${start_time})
end_time_s=$(DateForm ${end_time})

echo $start_time_s $end_time_s

BASE_DIR=${BASE_PATH_DIR}"/"$start_time"/"
mkdir -p ${BASE_DIR}
mkdir -p ${BASE_DIR}/2D
mkdir -p ${BASE_DIR}/3D
mkdir -p ${BASE_DIR}/SST

#/bin/rm -rf $BASE_DIR
echo BASE_DIR: ${BASE_DIR}
if [ ! -d $BASE_DIR ]; then
#base dir for processing data
mkdir $BASE_DIR
#make temporary dictionary to save the line files
mkdir ${BASE_DIR}/2D
mkdir ${BASE_DIR}/3D
mkdir ${BASE_DIR}/SST
fi

#link 2d files into temporary dictionary


echo "link needed 2d files into temporary dictionary"
#echo ${CFSRR_DIR}/FLXF/${start_time:0:4}/${start_time:0:6}/${start_time}

for yr in `seq ${start_time_s:0:4} ${end_time_s:0:4}`;do
cd ${CFSV2data_2d}/${START_HOUR}/${yr}

#for yr in `seq ${start_time_s:0:4} ${end_time_s:0:4}`;do
#cd ${CFSRR_DIR}${yr}
for fname in `ls flxf*.01.*${start_time:0:4}${START_HOUR}*grb2` ;do

date1=$(GetDate2 ${fname})
if [ ${date1} -ge ${start_time_s} ] && [ ${date1} -le ${end_time_s} ]; then #note: space before and bracket
ln -sf ${CFSV2data_2d}/${START_HOUR}/${yr}/${fname}  ${BASE_DIR}/2D/
fi
if [ ${date1} -eq ${end_time_s} ]; then
break
fi
done
done

#link 3d files into temporary dictionary
echo "link needed 3d files into temporary dictionary"

for yr in `seq ${start_time:0:4} ${end_time:0:4}`;do
cd ${CFSV2data_3d}/${START_HOUR}/${yr}
#for yr in `seq ${start_time:0:4} ${end_time:0:4}`;do
#cd ${ERI_3D_DIR}$yr
for fname in `ls pgbf*.01.*${start_time:0:4}${START_HOUR}*grb2`
do
date1=$(GetDate3 ${fname})
if [ ${date1} -ge ${start_time} ] && [ ${date1} -le ${end_time} ]; then
ln -sf ${CFSV2data_3d}/${START_HOUR}/${yr}/${fname}  ${BASE_DIR}/3D/
fi
if [ ${date1} -eq ${end_time} ]; then
break
fi
done
done

#add needed cwps files into Basedir
echo "add needed cwps files into Basedir"
cd ${BASE_DIR}
#ln -s ${GEO_DIR}/geo_em.d01.nc_ls   geo_em.d01.nc
ln -sf ${GEO_DIR}/geo_em.d01_veg.nc   geo_em.d01.nc
ln -sf ${EXE_DIR}/* .
cp ${GEO_DIR}/METGRID.TBL   METGRID.TBL          # use METGRID.TBL from sunqing
ln -sf ${CWPS_DIR}/ungrib/Variable_Tables .
ln -sf ${GEO_DIR}/soilhgt_cfsrr soilhgt  # intermediate format
ln -sf ${GEO_DIR}/sbcs .
cp ${NML_DIR}/namelist.wps .
cp ${NML_DIR}/namelist.input_ICBC  ./namelist.input
cp ${CWPS_DIR}/link_grib.csh .



echo "===============>ungrib process<=========================="

#substitude the start_time & end_time
#Ver 1
#num_row=`cat -An namelist.wps | grep start_date| cut -f 1`
#str="start_date = ${start_time:0:4}-${start_time:4:2}-${start_time:6:2}_00:00:00,"
#sed  -i "${num_row}c${str}" namelist.wps
#num_row=`cat -An namelist.wps | grep end_date| cut -f 1`
#str="end_date = ${end_time:0:4}-${end_time:4:2}-${end_time:6:2}_00:00:00,"
#sed  -i "${num_row}c${str}" namelist.wps

# modify interval start&end time
str="interval_seconds =21600,"
sed -i "/interval_seconds/c${str}"  namelist.wps
str="start_date = ${start_time:0:4}-${start_time:4:2}-${start_time:6:2}_${start_time:8:2}:00:00,"
sed -i "/start_date/c${str}" namelist.wps
str="end_date = ${end_time:0:4}-${end_time:4:2}-${end_time:6:2}_${end_time:8:2}:00:00,"
sed -i "/end_date/c${str}" namelist.wps


#ungrib 2D files
echo "Ungrib===>processing CFSRR 2D varible"
ln -sf ./Variable_Tables/Vtable.CFSR_sfc_flxf06 Vtable
./link_grib.csh  2D/*
str="prefix = \"${prefix[0]}\","
sed -i "/prefix/c${str}"  namelist.wps
./ungrib.exe &> ungrib_2d.ls
mv ungrib.log ungrib_2d

#ungrib SST from skintemp in cfsrr 2d files
echo "Ungrib===>processing CFSRRSST"
ln -sf ./Variable_Tables/Vtable.SST  Vtable
str="prefix = \"${prefix[2]}\","
sed -i "/prefix/c${str}"  namelist.wps
./ungrib.exe &> ungrib_sst.ls
mv ungrib.log ungrib_sst



#ungrib 3D files
echo "Ungrib===>processing CFSRR 3D varible"
rm -rf GRIBFILE.*
ln -sf ./Variable_Tables/Vtable.CFSR_press_pgbh06  Vtable
./link_grib.csh  3D/*
str="prefix = \"${prefix[1]}\","
sed -i "/prefix/c${str}"  namelist.wps
./ungrib.exe &> ungrib_3d.ls
mv ungrib.log ungrib_3d



#run mod_levs.exe to unify the vertical layers
echo "mod_lev===>processing CFSRR 3D varible"
for fname in `ls -l "${prefix[1]}"* | grep ^- | awk '{print $9}'`
do
#echo $fname
./mod_levs.exe ${fname} ${fname}.tmp &>> mod_lev.ls1
mv -f ${fname}.tmp ${fname}
done
#exit


echo "===============>Metgrid process<=========================="
# edit namelist.wps.&metgrid
str="fg_name = \"${prefix[0]}\", \"${prefix[1]}\",  \"${prefix[2]}\""
sed  -i "/fg_name/c${str}" namelist.wps
str="constants_name= \"soilhgt\","
sed  -i "/constants_name/c${str}" namelist.wps
./metgrid.exe &> metgrid.ls



echo "===============>SST Processing<=========================="
# optimize the sst in water gird including lake
fs=(`ls met_em*`)
for (( c=0; c<=${#fs[@]}-1; c=c+4 ))
do
YYYYMMDD=`echo ${fs[c]}| cut -d'.' -f 3 | cut -d'_' -f 1 `  #form YYYY-MM-DD
YYYYMMDD=${YYYYMMDD:0:4}${YYYYMMDD:5:2}${YYYYMMDD:8:2}   #YYYYMMDD
./sst_avg_d01 ${YYYYMMDD}
echo "processing=====>"${YYYYMMDD}
done



echo "===============>real process<=========================="
cd ${BASE_DIR}
#cp ${NML_DIR}/namelist.input  .
#ln -s ${CWRF_DIR}/main/real.exe .

met_file=met_em.d01.${start_time:0:4}-${start_time:4:2}-${start_time:6:2}_${start_time:8:2}:00:00.nc
num_vertical=`ncdump -h ${met_file} |   \
             grep BOTTOM-TOP_GRID_DIMENSION | cut -d" " -f 3`

sed -i -e "/start_year/c\ start_year = ${start_time:0:4},"  \
    -e "/start_month/c\ start_month = ${start_time:4:2},"  \
    -e "/start_day/c\ start_day = ${start_time:6:2},"  \
    -e "/start_hour/c\ start_hour = ${start_time:8:2}," \
    -e "/end_year/c\ end_year = ${end_time:0:4},"  \
    -e "/end_month/c\ end_month = ${end_time:4:2},"  \
    -e "/end_day/c\ end_day = ${end_time:6:2},"  \
    -e "/end_hour/c\ end_hour = ${end_time:8:2}," \
    -e "/num_metgrid_levels/c\ num_metgrid_levels = ${num_vertical},"  \
    namelist.input


./real.exe &> real.ls



cd ${BASE_DIR}
echo "===============>vbs process<=========================="
#vbs process
#ln -s /home/export/online1/sunlei/CWRF/geo/sbcs  .
cat > vbs.input << EOF
${start_time:0:4} ${start_time:4:2} ${start_time:6:2}
${end_time:0:4} ${end_time:4:2} ${end_time:6:2}
EOF
./vbs.re.exe < vbs.input &> vbs.ls
# echo "===============>changing the name<=========================="
# rm -f 2D:*
# rm -f 3D:*
# rm -f SST:*
# rm -f PFILE:*
# rm -f GRIBFILE.???
# rm -f met_em.d01*
#mv wrfinput_d01 wrfinput_d01.${start_time}
#mv wrfbdy_d01 wrfbdy_d01.${start_time}
#mv wrflowinput_d01 wrflowinput_d01.${start_time}
#mv wrfsst_d01 wrfsst_d01.${start_time}
#mv wrfveg_d01 wrfveg_d01.${start_time}
echo "===============>successfully<=========================="
