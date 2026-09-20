#******************************************************************************
# Python script to convert netCDF files to intermediate format for WPS
# Parallel version (no progress bar)
# Author: Omarjan
# Date: September, 2025
#******************************************************************************
import os
import argparse
import subprocess
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

#------------------------------------------------------------------------------#
parser = argparse.ArgumentParser()
parser.add_argument('-fname', '--forcename', required=True,
                    help='name of the forcing dataset (e.g., MPI-ESM1-2-HR_hist)', type=str)
parser.add_argument('-sdate', '--startdate', required=True,
                    help='start date, format: YYYY-MM-DD', type=str)
parser.add_argument('-edate', '--enddate', required=True,
                    help='end date, format: YYYY-MM-DD', type=str)
parser.add_argument('-indir', '--inputdir', required=True,
                    help='input directory containing netCDF files', type=str)
parser.add_argument('-outdir', '--outputdir', required=True,
                    help='output directory for intermediate files', type=str)
parser.add_argument('-nprocs', '--nprocs', default=4,
                    help='number of parallel processes', type=int)
parser.add_argument('-env', '--envname', default='wrf',
                    help='name of the conda environment with pywinter module', type=str)
args = parser.parse_args()

force_name  = args.forcename
start_date  = pd.to_datetime(args.startdate, format='%Y-%m-%d')
end_date    = pd.to_datetime(args.enddate,   format='%Y-%m-%d')
input_dir   = Path(args.inputdir).resolve()  # 绝对路径
output_dir  = Path(args.outputdir).resolve()  # 绝对路径
n_procs     = int(args.nprocs)
envname     = args.envname
current_dir = Path.cwd()
#------------------------------------------------------------------------------#
print("\n\nConfiguration:")
print(f"  Forcing dataset    : {force_name}")
print(f"  Start date         : {start_date.strftime('%Y-%m-%d')}")
print(f"  End date           : {end_date.strftime('%Y-%m-%d')}")
print(f"  Input directory    : {input_dir}")
print(f"  Output directory   : {output_dir}")
print(f"  Number of processes: {n_procs}")
print(f"  Conda environment  : {envname}")
print(f"  Current directory  : {current_dir}")
#------------------------------------------------------------------------------#

# I/O checks
if not input_dir.exists():
    raise FileNotFoundError(f"Input directory {input_dir} does not exist.")
output_dir.mkdir(parents=True, exist_ok=True)

# Date range (daily)
date_range = pd.date_range(start=start_date, end=end_date, freq='D')
if len(date_range) == 0:
    raise ValueError("Empty date_range: check start/end dates.")

# 安全拆分（保持 pandas Timestamp，不变成 numpy.datetime64）
idx_chunks = np.array_split(np.arange(len(date_range)), n_procs)
date_chunks = [date_range[idx] for idx in idx_chunks if len(idx) > 0]



#------------------------------------------------------------------------------#
def run_MPI_ESM1_2_HR_hist(iproc: int, dates: pd.DatetimeIndex) -> int:
    """
    每个 worker 处理自己的一段日期，并写入独立日志文件。
    返回 iproc 仅用于收集结果。
    """
    print(f"[iproc {iproc:03d}] Processing {len(dates):4d} days from {dates[0]} to {dates[-1]}")
    work_root = output_dir / f"_work_iproc{iproc:04d}"
    work_root.mkdir(parents=True, exist_ok=True)
    logfile = output_dir / f"ungrib.log.{iproc:04d}"
    with open(logfile, 'a', buffering=1) as log:
        for date in dates:
            # 每个日期再用一个子目录，彻底隔离 .inTer* 等临时文件
            year, month, day = date.year, date.month, date.day
            cmd = (
                f"conda run -n {envname} "
                f"python {current_dir}/convert_MPI-ESM1-2-HR_hist.py "
                f"-Y {year} -M {month} -D {day} "
                f"-indir {input_dir} -outdir {output_dir}"
            )
            # 运行转换脚本，stdout/stderr 均写入该进程的日志文件
            # 限制底层并行库的线程数，避免过度超订阅
            env = os.environ.copy()
            env.update({
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
            })
            try:
                subprocess.run(cmd, shell=True, stdout=log, stderr=log, check=True, env=env, cwd=work_root)
            except subprocess.CalledProcessError as e:
                log.write(f"[iproc {iproc}] Error processing date {date}: {e}\n")
                log.write(f"[iproc {iproc}] Command was: {cmd}\n")
                print(f"[iproc {iproc}] Log file: {logfile}\n")
                raise

            # 产物校验（如果你的脚本以 00 时刻写出日频文件）
            date_str = date.strftime("%Y-%m-%d_%H")
            for tag in ("2D", "3D", "SST"):
                fpath = output_dir / f"{tag}:{date_str}"
                if not fpath.exists():
                    raise FileNotFoundError(f"[iproc {iproc}] Missing {fpath}")
            # 清理工作目录
            shutil.rmtree(work_root / "*", ignore_errors=True)
        shutil.rmtree(work_root, ignore_errors=True)

    return iproc



#------------------------------------------------------------------------------#
if __name__ == "__main__":
    print(f"\nStarting conversion for forcing dataset: {force_name}")
    if force_name != "MPI-ESM1-2-HR_hist":
        raise ValueError(f"Unsupported forcing dataset: {force_name}")

    n_jobs = min(n_procs, len(date_chunks))
    tasks = [(i, ch) for i, ch in enumerate(date_chunks)]

    shutil.rmtree(output_dir / "ungrib.log.*", ignore_errors=True)  # 删除旧工作目录
    # 并行执行：每个 chunk 一个独立进程、一个独立日志
    results = Parallel(n_jobs=n_jobs, backend="loky", verbose=0)(
        delayed(run_MPI_ESM1_2_HR_hist)(ip, ch) for ip, ch in tasks
    )

    print("All done!")
