# -*- coding: utf-8 -*-
"""
Created on Thu May 19 11:35:49 2016

@author: geddesag

Title: Brukerpy Development Code Library

Desc.: Library of functions to be used in the brukerpy module, also serves as
a test bed for new ideas


"""

from numpy import *
from matplotlib.pyplot import *
import datetime
import ephem
import time
#from default_settings import *
import os.path
import subprocess
import win32com.client
import ConfigParser





def config_out(section,con_in):
    config=con_in
    dict1 = {}
    options = config.options(section)
    for option in options:
        try:
            dict1[option] = config.get(section, option)
            if dict1[option] == -1:
                DebugPrint("skip: %s" % option)
        except:
            print("exception on %s!" % option)
            dict1[option] = None
    return dict1
    
def open_opus():
    subprocess.Popen('C:\Program Files\OPUS_65\opus.exe')
    time.sleep(10)
    i=0
    while i<10:
        try:
            print "enter attempt "+str(i)
            shell=win32com.client.Dispatch("WScript.Shell")
            shell.AppActivate("Opus")
            time.sleep(5)   
            shell.SendKeys("{ENTER}", 1) 
            
            time.sleep(10)
            i=i+1
        except:
            pass

    
def close_opus():
    i=0
    while i<5:
        try:
            print "kill attempt "+str(i)
            subprocess.Popen('taskkill /IM opus.exe')
            i=i+1
            time.sleep(5)
        except:
            i=5
            pass
    time.sleep(60)
    
def tail( filename, lines=20 ):
    f=open(filename,'r')
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
                # from the end of the file
    while lines_to_go > 0 and block_end_byte > 0:
        if (block_end_byte - BLOCK_SIZE > 0):
            # read the last block we haven't yet read
            f.seek(block_number*BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0,0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count('\n')
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = ''.join(reversed(blocks))
    f.close()
    return '\n'.join(all_read_text.splitlines()[-total_lines_wanted:])
    
def format_xpm_file(xpm_file,def_paths_files,site,style="1"):
    """"
    New format is Site Letter, Filter No., YYYY_MM_DD_HH.X where X iterates, i.e
    L22016053109.1
    
    """
    def_paths_files=def_paths_files
    if style=="0":
        prefix=site['site_id']+site['inst_id']+"_"+xpm_file[0:3]
        now=datetime.datetime.now()
        year=str(now.year)
        month="%02d" % now.month
        day="%02d" % now.day
        hour="%02d" % now.hour
        suffix=0
        todayspath=year+month+day
        filepath_out=def_paths_files['datapath']+todayspath
        
        filename_out=prefix+"_"+year+"_"+month+"_"+day+"_"+hour+"."+str(suffix)
       
        
        """
        Here we check if the output file already exists, and if it does, it increases the suffix value.
        The limit here is a maximum suffix value of 999, but dont worry, it breaks the loop if it creates an 
        acceptable file name. Probably on suffix value 3 or 4 at most really. 
        """
        
        while suffix<999:
            filename_out=prefix+"_"+year+month+day+hour+"."+str(suffix)
            if os.path.exists(filepath_out+"\\"+filename_out)==False:
                break
            suffix=suffix+1
        
        
    if style=="1":
        prefix=xpm_file[0:2]
        now=datetime.datetime.now()
        yearf=chr(65+now.year-2000)
        if now.month<10:
            monthf=str(now.month)
        else:
            monthf=chr(65+now.month-10)
        
        year=str(now.year)
        month="%02d" % now.month
        day="%02d" % now.day
        hour="%02d" % now.hour
        suffix=0
        todayspath=year+month+day
        
        filepath_out=def_paths_files['datapath']+todayspath
        filename_out=prefix+yearf+monthf+day+hour+"."+str(suffix)
        
        while suffix<999:
            filename_out=prefix+yearf+monthf+day+hour+"."+str(suffix)
            if os.path.exists(filepath_out+"\\"+filename_out)==False:
                break
            suffix=suffix+1
            
    return filepath_out, filename_out
    
def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return idx

def FNR(D,P3):
	#function used by SunZen
	return ((D/P3)-int(D/P3))*P3
 

def decdeg2dms(dd):
   is_positive = dd >= 0
   dd = abs(dd)
   minutes,seconds = divmod(dd*3600,60)
   degrees,minutes = divmod(minutes,60)
   degrees = degrees if is_positive else -degrees
   return str(int(degrees))+":"+str(int(minutes))+":"+str(seconds)
   
   
def day_to_date(year,day):
    date_in=datetime.datetime(year, 1, 1) + datetime.timedelta(day - 1)
    return date_in.year,date_in.month,date_in.day
    
def sunzen_ephem(time,Lat,Lon,psurf,temp):
    
    observer = ephem.Observer()
    observer.lon = decdeg2dms(Lon)
    observer.lat = decdeg2dms(Lat)
    observer.date = time
 
    observer.pressure=psurf
    observer.temp=temp
    sun = ephem.Sun(observer)
   # sun.compute(observer)
    alt_atr = float(sun.alt)
    solar_altitude=180.0*alt_atr/pi
    solar_zenith=90.0-solar_altitude
    solar_azimuth=180*float(sun.az)/pi
    return solar_zenith, solar_azimuth




"""
now we need a quick thing that calculates how long until a certain sza or time
"""

class load_schedule(object):
    def __init__(self,dynamic_schedule_mode,schedule_file,lat,lon,utc_offset,psurf,temp):
        self.high_sun_time=0.0
        self.high_sun_sza=0.0
        self.low_sun_time=0.0
        self.low_sun_sza=90.0
        self.sunrise="00:00:00"
        self.sunset="00:00:00"
        self.day_length="00:00:00"
        self.all_times=["00:00:00"]
        self.all_ids =[]
        self.task_flags=[]
        self.task_types=[]
        if dynamic_schedule_mode==0:
            self.high_sun_time,self.high_sun_sza,self.low_sun_time,self.low_sun_sza,self.sunrise,self.sunset,self.day_length,self.all_times, self.all_ids, self.task_flags = expected_time_schedule(schedule_file,lat,lon,utc_offset,psurf,temp)
        if dynamic_schedule_mode==1:
            self.high_sun_time,self.high_sun_sza,self.low_sun_time,self.low_sun_sza,self.sunrise,self.sunset,self.day_length, self.all_times, self.all_ids, self.task_flags,self.task_types=dynamic_schedule(schedule_file,lat,lon,utc_offset,psurf,temp)

        
def expected_time_schedule(a,lat,lon,utc_offset,psurf,temp):
    """read schedule 'a' and compute an expected time schedule based on the szas and times required
    """
    #  schedule=genfromtxt(a,skipheader=1,skipfooter=1,dtype=str) #Annoyingly the format of each line is a load of crap, will need to read line by line instead :(
    time_utc=datetime.datetime.utcnow()
   
    time_local=time_utc+datetime.timedelta(hours=utc_offset)
    
    with open(a) as f:
        content1=f.readlines()
    task_type=[]
    task_sza=[]
    task_time=[]
    task_sza_ap=[]
    task_id=[]
    for i in range(1,len(content1)-1):
        
        info=content1[i].split()
        if info[0]=="Z" or info[0]=="T":
            task_type.append(info[0])
            task_id.append(info[-1])
            if info[0]=='Z':
                task_sza.append(info[1])
                task_sza_ap.append(info[2])
            if info[0]=="T":
                x=datetime.datetime(time_local.year,time_local.month,time_local.day,int(info[1][0:2]),int(info[1][3:5]),int(info[1][6:9]))
                task_time.append(x)
#            if info[0]=="C":
#                x=datetime.datetime(time_local.year,time_local.month,time_local.day,int(info[1][0:2]),int(info[1][3:5]),int(info[1][6:9]))
#                task_time.append(x) 
        else:
            continue              
    times=[]
    times_utc=[]



    #day_of_year_local=time_local.timetuple().tm_yday
    sza_ref=[]
    sza_ref2=[]
    
    times_array=[]
    for i in range(86400):
        times_array.append(datetime.datetime(time_local.year,time_local.month,time_local.day,0,0,0)+datetime.timedelta(seconds=i)-datetime.timedelta(hours=utc_offset))
        sza_ref.append(sunzen_ephem(times_array[i],lat,lon,psurf,temp)[0])
        times.append(times_array[i]+datetime.timedelta(hours=utc_offset))
   #this is the utc date, this will need to be updated to whatever supplies the time  
    
    
        
#    for i in range(24)): #1 second resolution
#        for j in range(60):
#            for k in range(60):
#                
#                #sza_ref.append(float(sunzen_ephem(time_local.year,day_of_year_local,i,j,k,lat,lon)[0]))
#                sza_ref.append(float(sunzen(time_local.year,day_of_year_local,i,j,k,lat,lon)[0]))
#                times.append(datetime.datetime(time_local.year,time_local.month,time_local.day,i,j,k))
    
    #now we have all the szas, we could do one of two things, create a function that fits the data, or just say find the nearest entry.
    #creating a function woud be more efficient with a larger number of tasks, its also irrelevant as we arent super concerned with
    #processing at this point. Lets just find the nearest entry, we will have to be careful to distinguish am and pm
 
    #find high sun (mimumum solar zenith angle)
    sza_time_local=[]
    high_sun_idx=where(array(sza_ref)==min(array(sza_ref)))[0][0]
    low_sun_idx=where(array(sza_ref)==max(array(sza_ref)))[0][0]
    high_sun_sza=sza_ref[high_sun_idx]
    low_sun_sza=sza_ref[low_sun_idx]
    high_sun_time=format_time(times[high_sun_idx].time())
    low_sun_time=format_time(times[low_sun_idx].time())
    #if low_sun_sza>=91.:
    #    low_sun_sza='n/a'
        #low_sun_time='Horizon'
    #if high_sun_sza>=91.:
    #    high_sun_sza='Below'
    #    high_sun_time='Horizon'

    #this should be in local time really, whatever timezone it is at 1am when we initialise such that sunrise is always first
    sunrise_idx=find_nearest(array(sza_ref[0:high_sun_idx]),90.0)
    sunset_idx=find_nearest(array(sza_ref[high_sun_idx:]),90.0)+high_sun_idx
    sunrise_s=sza_ref[sunrise_idx]
    sunset_s=sza_ref[sunset_idx]
    
    sunrise=times[sunrise_idx].time()
    sunset=times[sunset_idx].time()
    day_length=str(times[sunset_idx]-times[sunrise_idx])

    if sunrise_s<=89 or sunrise_s>=91.:
        sunrise="n/a"
    
    if sunset_s<=89 or sunset_s>=91.:
        sunset="n/a"    
        
        
        
    for i in range(len(task_sza)):
        if task_sza_ap[i]=='A':
            #sza_time.append(times[find_nearest(array(sza_ref[0:high_sun_idx]),task_sza[i])])
            
            index2=find_nearest(array(sza_ref[0:high_sun_idx]),float(task_sza[i]))
            sza_time_local.append(times[index2])
        if task_sza_ap[i]=='P':
            sza_time_local.append(times[find_nearest(array(sza_ref[high_sun_idx:]),float(task_sza[i]))+high_sun_idx])
    
    
    #sza_times succesfully obtained now we need to recompile the list of task and times
    
    times_out=[]
    times_out_utc=[]
    tasks_out=[]
    task_flags=zeros(len(task_type))
    k=0
    j=0
    for i in range(len(task_type)):

        if task_type[i]=='Z':
            times_out.append(sza_time_local[k])
            if float(task_sza[k])<high_sun_sza:
                task_flags[i]=2
            if float(task_sza[k])>low_sun_sza:
                task_flags[i]=2

            #times_out_utc.append((sza_time_local[k]+datetime.timedelta(hours=-utc_offset)))
            k=k+1
        else:    
            times_out.append(task_time[j])
            
            #times_out_utc.append((sza_time_local[j]+datetime.timedelta(hours=-utc_offset)))
            j=j+1
    
    ##Remove tasks that are not in order and create log file with warning
    removed_time=[]
    removed_id=[]
    removed_number=[]
    all_times=times_out[:]
    all_ids=task_id[:]

    good_time=times_out[0]
    
    
    for i in range(1,len(all_times)):
        if task_flags[i]!=2:
            if (all_times[i]-good_time)<datetime.timedelta(seconds=0):
                task_flags[i]=1
            else:
                good_time=all_times[i]

#    
   
    return high_sun_time, high_sun_sza, low_sun_time, low_sun_sza, sunrise,sunset,day_length, all_times, all_ids, task_flags
    
    #We have returned all the salient information, local task times, the tasks to be performed, and bonus
    #info like high sun time and sza. we could include sunrise and sunset no problem, its already calculated.
                   
def find_next_time(array,flags,value):
    diff=(array-value)
    for i in range(len(diff)):
        if diff[i]>datetime.timedelta(0,0,0) and flags[i]==0:
            break
    if diff[i]<datetime.timedelta(0,0,0):
        i=-1
    return i
    
def find_next_time_nf(array,value):
    diff=(array-value)
    for i in range(len(diff)):
        if diff[i]>datetime.timedelta(0,0,0):
            break
    if diff[i]<datetime.timedelta(0,0,0):
        i=-1
    return i
    
def format_countdown(timedelta_obj):
    days=timedelta_obj.days
    hours, remainder = divmod(timedelta_obj.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    out =str('%02d:%02d:%02d' % (int(hours), int(minutes), int(seconds)))
    return out

def format_time(datetime_obj):
    out =str('%02d:%02d:%02d' % (int(datetime_obj.hour), int(datetime_obj.minute), int(datetime_obj.second)))
    return out

def read_task(taskname):
    """Read task file: search for first and last xpm line, list in between. Should mean we can mess about with headers and footers,
    second columns, to our hearts content
    """
    xpms=[]
    with open(taskname) as f:
        content=f.readlines()
        
    for i in range(len(content)):
        
        if content[i].find(".xpm")!=-1:
            
            xpms.append(content[i][0:content[i].find(".xpm")+4])
        elif content[i].find(".XPM")!=-1:
            xpms.append(content[i][0:content[i].find(".XPM")+4])

    return array(xpms)
    
    
    
def dynamic_schedule(a,lat,lon,utc_offset,psurf,temp):

    """read schedule 'a' and compute an expected time schedule based on the szas and times required
    """
    time_utc=datetime.datetime.utcnow()
   
    time_local=time_utc+datetime.timedelta(hours=utc_offset)
    
    database=loadtxt(a,dtype=str,unpack=True,skiprows=2)
    times_local=[]
    sza_ref=[] 
    times_utc=[]
    
    for i in range(86400):
        times_utc.append(datetime.datetime(time_local.year,time_local.month,time_local.day,0,0,0)+datetime.timedelta(seconds=i)-datetime.timedelta(hours=utc_offset))
        sza_ref.append(sunzen_ephem(times_utc[i],lat,lon,psurf,temp)[0])
        times_local.append(times_utc[i]+datetime.timedelta(hours=utc_offset))

    sza_time_local=[]
    high_sun_idx=where(array(sza_ref)==min(array(sza_ref)))[0][0]
    low_sun_idx=where(array(sza_ref)==max(array(sza_ref)))[0][0]
    high_sun_sza=sza_ref[high_sun_idx]
    low_sun_sza=sza_ref[low_sun_idx]
    high_sun_time=format_time(times_local[high_sun_idx].time())
    low_sun_time=format_time(times_local[low_sun_idx].time())

    sunrise_idx=find_nearest(array(sza_ref[0:high_sun_idx]),90.0)
    sunset_idx=find_nearest(array(sza_ref[high_sun_idx:]),90.0)+high_sun_idx
    sunrise_s=sza_ref[sunrise_idx]
    sunset_s=sza_ref[sunset_idx]
    
    sunrise=times_local[sunrise_idx].time()
    sunset=times_local[sunset_idx].time()
    
    
    day_length=str(times_local[sunset_idx]-times_local[sunrise_idx])
    
    """Last little thing, may or may not be useful. if nearest value to 90 is above 91 or below 89, 
    the sun is permanently set or risen. So I return an n/a value for the formatted string."""
    
    if sunrise_s<=89 or sunrise_s>=91.:
        sunrise="n/a"
        day_length="n/a"
    
    if sunset_s<=89 or sunset_s>=91.:
        sunset="n/a"    
        day_length="n/a" 
        
    windows_start=[]
    windows_stop=[]
    window_identity=[]
    
    windows_start_m=[]
    windows_stop_m=[]
    window_identity_m=[]
    
    
    """Ok so what I have done here is to first of all calculate all the start and stop times for the sza tasks. This is complicated
    by tasks that will have split windows or no windows. Hence the calls to high_sun_sza and the different inequalities
    to split windows in to seperate instances, the database.size==4 if statement is to allow a single task database"""
    if database.size==4: 
        ranges=database[1:3]
        if database[0]=="Z":
            
            if float(ranges[0])>high_sun_sza<float(ranges[1]):
                start_am=times_local[find_nearest(array(sza_ref[0:high_sun_idx]),float(ranges[0]))]
                windows_start.append(start_am)
                window_identity.append(0)
                stop_pm=times_local[find_nearest(array(sza_ref[high_sun_idx:]),float(ranges[0]))+high_sun_idx]
                windows_stop.append(stop_pm)
            if float(ranges[0])>high_sun_sza>float(ranges[1]):
                start_am=times_local[find_nearest(array(sza_ref[0:high_sun_idx]),float(ranges[0]))]
                windows_start.append(start_am)
                window_identity.append(0)
                stop_pm=times_local[find_nearest(array(sza_ref[high_sun_idx:]),float(ranges[0]))+high_sun_idx]
                windows_stop.append(stop_pm)
        if database[0]=='T':
            start=datetime.datetime(times_local[0].year,times_local[0].month,times_local[0].day,int(ranges[0][0:2]),int(ranges[0][3:5]),int(ranges[0][6:9]))
            stop=datetime.datetime(times_local[0].year,times_local[0].month,times_local[0].day,int(ranges[1][0:2]),int(ranges[1][3:5]),int(ranges[1][6:9]))
            windows_start.append(start)
            window_identity.append(0)
            windows_stop.append(stop)
        windows_start=windows_start
        windows_start.append(stop_pm)
        tasknames_out=[database[3],'Complete']
        task_types_out=[database[0],'F']
        task_flags=[0,0]
    else: 
        for i in range(len(database[0])):
            ranges=database[1:3,i]
            if database[0][i]=='Z':
                if float(ranges[0])>high_sun_sza<float(ranges[1]):
                    start_am=times_local[find_nearest(array(sza_ref[0:high_sun_idx]),float(ranges[0]))]
                    windows_start.append(start_am)
                    window_identity.append(i)
                    stop_am=times_local[find_nearest(array(sza_ref[0:high_sun_idx]),float(ranges[1]))]
                    windows_stop.append(stop_am)
                    start_pm=times_local[find_nearest(array(sza_ref[high_sun_idx:]),float(ranges[1]))+high_sun_idx]
                    windows_start.append(start_pm)
                    window_identity.append(i)
                    stop_pm=times_local[find_nearest(array(sza_ref[high_sun_idx:]),float(ranges[0]))+high_sun_idx]
                    windows_stop.append(stop_pm)
        
                if float(ranges[0])>high_sun_sza>float(ranges[1]):
                    start_am=times_local[find_nearest(array(sza_ref[0:high_sun_idx]),float(ranges[0]))]
                    windows_start.append(start_am)
                    window_identity.append(i)
                    stop_pm=times_local[find_nearest(array(sza_ref[high_sun_idx:]),float(ranges[0]))+high_sun_idx]
                    windows_stop.append(stop_pm)
            
            """Here is the same but simpler because it is for the time specfied windows"""
            if database[0][i]=='T':
                start=datetime.datetime(times_local[0].year,times_local[0].month,times_local[0].day,int(ranges[0][0:2]),int(ranges[0][3:5]),int(ranges[0][6:9]))
                stop=datetime.datetime(times_local[0].year,times_local[0].month,times_local[0].day,int(ranges[1][0:2]),int(ranges[1][3:5]),int(ranges[1][6:9]))
                windows_start_m.append(start)
                window_identity_m.append(i)
                windows_stop_m.append(stop)
              
        #windows_start.sort()
        #windows_stop.sort()
        merged_windows_sza=array([window_identity,windows_start,windows_stop])
        for i in range(len(merged_windows_sza)):
            merged_windows_sza[i]=merged_windows_sza[i][argsort(merged_windows_sza[2])]
        
        
        
        window_identity=list(merged_windows_sza[0])
        windows_start=list(merged_windows_sza[1])
        windows_stop=list(merged_windows_sza[2])
        """Now we have to merge the two lists of windows together. This is non trivial as the time dependent list
        will overlap multiple windows"""
        
        windows_start.append(max(windows_stop))
        window_identity.append("Complete")
        for i in range(len(windows_start_m)):
            if windows_stop_m[i]>max(windows_stop):
                windows_start[-1]=windows_stop_m[i]
                
           
            next_stop=find_next_time_nf(array(windows_start),windows_stop_m[i])
            next_start=find_next_time_nf(array(windows_start),windows_start_m[i])
    
    
      
            if next_start==next_stop:
                
                windows_start.insert(next_start,windows_start_m[i])
                window_identity.insert(next_start,window_identity_m[i])
                windows_start.insert(next_start+1,windows_stop_m[i])
                window_identity.insert(next_start+1,window_identity[next_start-1])
            if next_stop-next_start==1:
                
                windows_start.insert(next_start,windows_start_m[i])
                window_identity.insert(next_start,window_identity_m[i])
                windows_start[next_start+1]=windows_stop_m[i]
                
            if next_stop-next_start>1:
                to_delete=(next_stop-next_start)-1
                j=0
                while j<to_delete:
                    
                    del windows_start[next_start]
                    del window_identity[next_start]
                    j=j+1
                
                windows_start.insert(next_start,windows_start_m[i])
                window_identity.insert(next_start,window_identity_m[i])
                windows_start[next_start+1]=windows_stop_m[i]
            if windows_start[-1]==windows_start[-2]:
                del windows_start[-2]
                del window_identity[-2]
            if windows_start[next_start-1]==windows_start[next_start]:
                del windows_start[next_start-1]
                del window_identity[next_start-1]
        tasknames_out=[]
        for i in range(len(window_identity)-1):    
            
            tasknames_out.append(database[3][int(window_identity[i])])
        tasknames_out.append(window_identity[-1])
        task_types_out=[]
        for i in range(len(window_identity)-1):
            task_types_out.append(database[0][int(window_identity[i])])
        task_types_out.append("F")
        task_flags=zeros(len(tasknames_out))
#    all_times=task_exec_time[:]
#    all_ids=task_exec_name[:]
    #flag_out=0
    return high_sun_time, high_sun_sza, low_sun_time, low_sun_sza, sunrise, sunset,day_length, windows_start, tasknames_out, task_flags,task_types_out
    