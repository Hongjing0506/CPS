import os
import argparse
from multiprocessing import Process
#import to determine leap year
import calendar
parser = argparse.ArgumentParser()
parser.add_argument("YR", help="Year", type=str)

args = parser.parse_args()
YR = args.YR

def link(YR):
    os.system("mkdir -p /share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM//"+YR)
    os.system("mkdir -p /share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM//"+YR+"/ncs/")
    os.system("ln -sf /share/home/dq048/oscar/future/hist/cesm/*"+str(YR)+"* /share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM//"+str(YR)+"/ncs/")
    os.system("ln -sf /share/home/dq048/oscar/future/hist/cesm/*"+str(int(YR)+1)+"* /share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM//"+str(YR)+"/ncs/")
    os.system("ln -sf /share/home/dq048/oscar/future/hist/cesm/*"+str(int(YR)-1)+"* /share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM//"+str(YR)+"/ncs/")
def run_one_command(YR,MON,DAY):
    print("cd /share/home/dq048/oscar/future/hist/runicbc_cesm/hist/CESM_IM//"+YR+"&&ncl /share/home/dq048/oscar/future/hist/icbc_cesm/convert.ncl YR="+YR+" MON="+MON+" DAY="+DAY)

#loop over all days in the year with no leap year
# 31 days: 1,3,5,7,8,10,12
# 30 days: 4,6,9,11
# 28 days: 2
# 
cpu_to_use = 20
# if leap year
if calendar.isleap(int(YR)):
    days = [31,29,31,30,31,30,31,31,30,31,30,31]
else:
    days = [31,28,31,30,31,30,31,31,30,31,30,31]
link(YR)
for MON in range(1,13):
    for DAY in range(1,days[MON-1]+1):
        p = Process(target=run_one_command, args=(YR,str(MON).zfill(2),str(DAY).zfill(2)))
        p.start()
        cpu_to_use -= 1
        if cpu_to_use == 0:
            p.join()
            cpu_to_use = 20

