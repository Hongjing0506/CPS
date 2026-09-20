import os
import argparse
from multiprocessing import Process
#import args YR MON DAY
parser = argparse.ArgumentParser()
parser.add_argument("-YR", help="Year", type=int)

args = parser.parse_args()
YR = str(args.YR)

# def run_one_met(YR,MON,startday,endday):
os.system("mkdir -p /share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_REAL/"+YR)
os.chdir("/share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_REAL/"+YR)
os.system("ln -sf /share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_MET/"+YR+"*/met_em*.nc ./")
os.system("ln -sf /share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_MET/"+str(int(YR)+1)+"_01_met/met_em*.nc ./")
if int(YR)>2015:
    os.system("ln -sf /share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_MET/"+str(int(YR)-1)+"_10_met/met_em*.nc ./")
    os.system("ln -sf /share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_MET/"+str(int(YR)-1)+"_11_met/met_em*.nc ./")
    os.system("ln -sf /share/home/dq048/oscar/future/ICBC_RUN/SSP245/MPI_MET/"+str(int(YR)-1)+"_12_met/met_em*.nc ./")
if YR=="2015":
    STARTYEAR=2015
    STARTMON=1
    STARTDAY=2
else:
    STARTYEAR=int(YR)-1
    STARTMON=10
    STARTDAY=1
if int(YR)<2029:
    ENDYEAR=int(YR)
    ENDMON=12
    ENDDAY=30
ENDYEAR=int(YR)+1
ENDMON=1
ENDDAY=3


os.system("sh /share/home/dq048/oscar/future/mpi245/icbc_mpi245/real.sh "+YR+" "+str(STARTYEAR)+" "+str(ENDYEAR)+" "+str(STARTMON)+" "+str(STARTDAY)+" "+str(ENDMON)+" "+str(ENDDAY))
