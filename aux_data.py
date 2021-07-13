# -*- coding: utf-8 -*-
"""
Created on Fri Jun 30 13:42:13 2017

@author: geddesag


Here is the module you must import and edit for your auxiliary data, I've included a 
few dummy examples which you can copy into the main function if you just want to play around


"""
from numpy import *
import time
import datetime
import urllib

def find_nearest(array,value):
    idx = (abs(array-value)).argmin()
    return idx
    
#def gather_data():
#    """Most simple example"""
#    data=arange(10)
#    suspend_flag=0
#    return data, suspend_flag
#    
#def gather_data_2():
#    """Bit cleverer, looks vaguely physical"""
#    data=array([1000,27.,0,5,5,5])
#    factor=array([30,10,1,5,5,5])
#    rand_arr=random.rand(len(data))
#    data=data+factor*rand_arr
#    if data[0]>1000:
#        suspend_flag=1
#    else:
#        suspend_flag=0
#    
#    return data, suspend_flag
#    
#def gather_from_file():
#    """Takes the most recent line from a txt file"""
#    data=array(tail("aux_data.dat").split(),dtype=float)
#    if data[0]>1020:
#        suspend_flag=1
#    else:
#        suspend_flag=0
#    return data,suspend_flag
def convert(input_array,time_now)  :
    """some custom conversion code for a dummy version of my own aux function, ignore"""
    date_out=[]
    for input_val in input_array:
        hours=int(input_val[0:2])
        minutes=int(input_val[2:4])
        seconds=int(input_val[4:6])
        date_out.append(datetime.datetime(time_now.year,time_now.month,time_now.day,hours,minutes,seconds))
    return date_out
    
def gather_auxiliary_data2():

    
    time_now=datetime.datetime.now()
    
    data=loadtxt('V:/bruker/bruker.dat/120hr/mir/2017_06/120hr/20170620/solar.txt',unpack=True,dtype=str)
    dates=convert(data[0],time_now)
    index=find_nearest(array(dates),time_now)
    
    flag=data[-1][index]
    data_out=data[:,index][:-1]
    if flag=="cloudy":
        return data_out,1
    else:
        return data_out,0


def gather_auxiliary_data():
    """Here is the real function, it must be named as above, I do not care what
    you do here as long as you return a list or 1d array as well as an integer flag
    value, 1 = do not run as the flag has been set, 0 means all is well, no flag set"""
    now=datetime.datetime.now()
    year=str(now.year)
    month="%02d" % now.month
    day="%02d" % now.day
    todayspath=year+month+day
    try:
    	f=urllib.urlopen("http://10.10.0.100:8080/logs/"+todayspath+"/solar.txt").read()
    	lastline=(f.split("\n")[-2]).split()
    	if lastline[-1] not in ["cloudy","stopped","north"] :
		flag=0
    	else:
		flag=1
    except:
        flag=0
	lastline=[""]
    return lastline[:],flag
