import os
import argparse
from multiprocessing import Process
#import args YR MON DAY
parser = argparse.ArgumentParser()
parser.add_argument("YR", help="Year", type=str)
parser.add_argument("MON", help="Month", type=str)
parser.add_argument("startday", help="Start day", type=str)
parser.add_argument("endday", help="End day", type=str)

args = parser.parse_args()
YR = args.YR
MON = args.MON
startday = args.startday
endday = args.endday



os.system("sh /share/home/dq048/oscar/future/hist/icbc_cesm/run.sh "+YR+" "+MON+" "+startday+" "+endday)
