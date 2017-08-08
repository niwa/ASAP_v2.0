# -*- coding: utf-8 -*-
"""
Created on Tue Feb 21 08:11:49 2017

@author: bruker
"""

from numpy import *
from matplotlib.pyplot import *
import datetime
import win32com.client as w32
import time

import ConfigParser
from dde_client import *
from library import *
import os
    
import sys

if __name__=='__main__':
    
    config=ConfigParser.ConfigParser()
    config.read('brukerpy.ini')
    site=config_out('site',config)
    def_paths_files=config_out('paths/files',config)
    startup=config_out('startup',config)
    log_path=def_paths_files['python_log_path']
    

    sys.stdout= open(log_path+"exec_log.dat","a")
    sys.stderr=sys.stdout
    print sys.argv[1:]


	
    xpm_path,xpm_name,style,log,a,b,gui_test_mode,simulator_mode=sys.argv[1:]
    xpm_file=xpm_name

    if int(gui_test_mode)==0:
        """Submit a proper experiment to opus"""
        print xpm_name
        link=None
        id1=None
        python_server=None
        link=DDEClient("Opus","System")
        param_num = " 4"
        macroname = def_paths_files['macrofilespath']+def_paths_files['macrofile'] #create ini file first please
        macrorequest = "RUN_MACRO " + macroname + param_num
        endoffile=chr(13)+chr(10)

       # print xpm_path
        start_time=datetime.datetime.now()
        print start_time
#        f=open(log,'a')
#        timestamp=format_time(start_time)
#        f.write(timestamp+" Starting Xpm - "+xpm_file+" ("+str(a)+"/"+str(b)+")\n")
#        f.close()
        output_path, output_file=format_xpm_file(xpm_file,def_paths_files,site,style=style)
        if simulator_mode==1:
            xpm_file=def_paths_files['simulator_xpm']
        #time.sleep(20)
        link.request("REQUEST_MODE")        
        link.request(macrorequest)
        link.request(output_path+endoffile)
        link.request(output_file+endoffile)
        link.request(xpm_file+endoffile)
        id1=link.request(xpm_path+endoffile)     
        macro_id=str(id1[4:-1])
	print 'submitted'
        #Executes Experiment, need to wait until it is complete. This process will be threaded so the gui will be fine, but i dont want to spam opus
        try:
            while link.request("MACRO_RESULTS "+macro_id)[4]=='0':
                time.sleep(1)
        except:
            print("Error in Opus polling, im probably ok so will proceed")
        DDEClient.__del__(link)
         
        end_time=datetime.datetime.now()
        timestamp=format_time(end_time)
        duration=str((end_time-start_time).seconds)
        print end_time
#        f=open(log,'a')
#        f.write(timestamp+" Xpm Complete - "+xpm_name+" Duration "+duration+ " Secs.\n")
#        f.close()
        link=None
        id1=None
    if int(gui_test_mode)==1:
       #print 'dummy xpm'    
        dummy_time=int(site['gui_test_xpm_time'])
       # f=open(log,'a')
        start_time=datetime.datetime.now()
        print style
        timestamp=format_time(start_time)
        print timestamp+' dummy xpm'    

#        f.write(timestamp+" Starting Xpm - Dummy "+xpm_file+" ("+str(a)+"/"+str(b)+")\n")
#        f.close()
        time.sleep(dummy_time)
        end_time=datetime.datetime.now()
        duration=str((end_time-start_time).seconds)
        output_path, output_file=format_xpm_file(xpm_file,def_paths_files,style=style)
        f=open(output_path+"/"+output_file,"w")
        f.write("created as dummy")
        f.close()
        
        if exists==0:
            f=open(log,'a')
            f.write(timestamp+" Xpm Doesnt exist, check paths")
            f.close()
    sys.stdout.close()
    sys.exit(0)