import os
import calendar
def sub_im():
    subfil=open('submit_im.lsf','r')
    content=subfil.read()

    for year in range(1970,1990):
        TEMPcontent=content.replace('TARGET',str(year))
        outfil=open('lsfs/submit_'+str(year)+'_im.lsf','w')
        outfil.write(TEMPcontent)
        outfil.close()
        os.system('bsub<lsfs/submit_'+str(year)+'_im.lsf')


def sub_met():
    subfil=open('submit_met.lsf','r')
    content=subfil.read()
    daysofmonth=[31,28,31,30,31,30,31,31,30,31,30,31]
    leapdaysofmonth=[31,29,31,30,31,30,31,31,30,31,30,31]
    # for year in range(2021,2025):
    # for year in range(2025,2035):
    # for year in range(2023,2035):
    # for year in range(2035,2045):
    # for year in range(2033,2035):
    # for year in range(2044,2055):
    # for year in range(2043,2044):
    # for year in range(2055,2065):
    # for year in range(2043,2044):
    # for year in range(1970,1990):
    # for year in range(1980,1981):
    # for year in range(2015,2030):
    for year in range(2045,2060):
        for month in range(1,13):
            if year==2015 and month==1:
                startday=2
            else:
                startday=1
            TEMPcontent=content.replace('TARGETYEAR',str(year))
            TEMPcontent=TEMPcontent.replace('TARGETMON',str(month))
            TEMPcontent=TEMPcontent.replace('STARTDAY',str(startday))
            if calendar.isleap(year):
                TEMPcontent=TEMPcontent.replace('ENDDAY',str(leapdaysofmonth[month-1]))
            else:
                TEMPcontent=TEMPcontent.replace('ENDDAY',str(daysofmonth[month-1]))
            outfil=open('lsfs/submit_'+str(year)+str(month).zfill(2)+'_met.lsf','w')
            outfil.write(TEMPcontent)
            outfil.close()
            os.system('bsub<lsfs/submit_'+str(year)+str(month).zfill(2)+'_met.lsf')

def sub_real():
    subfil=open('submit_icbc.lsf','r')
    content=subfil.read()
    # for year in range(2015,2024):
    # for year in range(2024,2034):
    # for year in range(2034,2044):
    # for year in range(2054,2064):
    # for year in range(1990,1991):
    # for year in range(2015,2030):
    for year in range(2045,2060):
    #for year in range(2016,2029,4):
    # for year in range(1970,1989):
        TEMPcontent=content.replace('TARGETYEAR',str(year))
        outfil=open('lsfs/submit_'+str(year)+'_icbc.lsf','w')
        outfil.write(TEMPcontent)
        outfil.close()
        os.system('bsub<lsfs/submit_'+str(year)+'_icbc.lsf')


def clean():
    # for year in range(2024,2035):
    for year in range(2053,2064):
        # os.system("rm -fr ../ICBC_RUN/SSP245/CESM_IM/"+str(year)+"/")
        # os.system("rm -fr ../ICBC_RUN/SSP245/CESM_MET/"+str(year)+"_*")
        os.system("rm -fr ../ICBC_RUN/SSP245/CESM_REAL/"+str(year)+"_*")


sub_im()
# sub_met()
# sub_real()

# clean()
