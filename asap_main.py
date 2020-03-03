
# -*- coding: utf-8 -*-
"""
Created on Fri May 20 14:38:13 2016

@author: geddesag

alex.geddes@niwa.co.nz


Clean rebuild of the asap program, with implementation of a builder and
the new auxiliary data and flag function


"""

from numpy import *
from matplotlib.pyplot import *
import datetime
import ephem
import win32com.client as w32
import Tkinter as tk
import time
from Tkinter import Tk, RIGHT, BOTH, RAISED, X, N,Y, LEFT, END,TOP,E,S,W,WORD,CHAR,SUNKEN,HORIZONTAL,ACTIVE
import tkFileDialog as filedialog
import threading
from multiprocessing import Process
from dde_client import *
import pygubu
import psutil
#import library
from library import *
import subprocess
import os.path
import sys
from shutil import copyfile,move
from aux_data import *
import json

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

 
class FuncThread(threading.Thread):
    def __init__(self, target, *args):
        self._target = target
        self._args = args
        threading.Thread.__init__(self)
 
    def run(self):
        self._target(*self._args)
 

        
class App():
    def __init__(self):
        
        """Initialise tkinter"""
        
        self.root = tk.Tk()

        self.root.title('ASAP_v2.0 - Contact alex.geddes@niwa.co.nz')
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)

        """Call builder"""
        
        self.builder = builder = pygubu.Builder()

        #2: Load an ui file
        builder.add_from_file('asap.ui')

        #3: Create the widget using a master as parent
        self.mainwindow = builder.get_object('mainwindow', self.root)


       # self.schedule_frame=builder.get_object('schedule_frame',self.root)
        self.aux_window=tk.Toplevel(self.root)
        self.aux_window.protocol('WM_DELETE_WINDOW', self.on_close_aux)
        self.aux_window.withdraw()
        """Now we link to all the objects within the builder that we need to access"""
        
        
        """ Current Info Objects"""
        self.utctime_entry=builder.get_object('utctime_entry',self.root)
        self.localtime_entry=builder.get_object('localtime_entry',self.root)
        self.sza_entry=builder.get_object('sza_entry',self.root)
        self.elv_entry=builder.get_object('elv_entry',self.root)
        
        """ Daily Info Objects"""
        
        self.high_sun_sza_entry=builder.get_object('high_sun_sza_entry',self.root)
        self.high_sun_time_entry=builder.get_object('high_sun_time_entry',self.root)
        self.low_sun_sza_entry=builder.get_object('low_sun_sza_entry',self.root)
        self.low_sun_time_entry=builder.get_object('low_sun_time_entry',self.root)
        self.sunrise_entry=builder.get_object('sunrise_entry',self.root)
        self.sunset_entry=builder.get_object('sunset_entry',self.root)
        self.day_length_entry=builder.get_object('day_length_entry',self.root)
        
        """Task Info Objects"""
        
        self.task_countdown_entry=builder.get_object('task_countdown_entry',self.root)
        self.scheduled_task_entry=builder.get_object('scheduled_task_entry',self.root)
        self.manual_task_entry=builder.get_object('manual_task_entry',self.root)
        self.schedule_combobox=builder.get_object('schedule_combobox',self.root)
        self.dynamic_combobox=builder.get_object('dynamic_combobox',self.root)


        """Command Objects - We'll also need to pull in some variables and link any commands """
        self.dynamic_schedule_mode=tk.IntVar()
        self.dynamic_schedule_mode.set(int(startup['dynamic_schedule_mode']))
        
        self.run_daily_mode=tk.IntVar()
        #self.run_daily_mode.set(int(startup['run_daily_mode']))
        self.run_daily_mode.set(1)
        self.legacy_format_mode=tk.IntVar()
        self.legacy_format_mode.set(int(startup['legacy_format_mode']))
        
        self.use_aux_flag_mode=tk.IntVar()
        self.use_aux_flag_mode.set(int(startup['use_aux_flag_mode']))       
        
        self.schedule_listbox=builder.get_object('schedule_listbox',self.root)
        
        self.schedule_run_button=builder.get_object('schedule_run_button',self.root)
        self.abort_task_button=builder.get_object('abort_task_button',self.root)
        self.manual_task_button=builder.get_object('manual_task_button',self.root)
        self.manual_xpm_button=builder.get_object('manual_xpm_button',self.root)
        self.comment_button=builder.get_object('comment_button',self.root)
        self.guide_button=builder.get_object('guide_button',self.root)
        self.test_opus_button=builder.get_object('test_opus_button',self.root)
        self.view_aux_button=builder.get_object('view_aux_button',self.root)
        self.schedule_run_button.config(command=self.toggle_schedule_run)
        self.abort_task_button.config(command=self.abort_task,state="disabled")
        self.manual_task_button.config(command=self.get_filename_task)
        self.manual_xpm_button.config(command=self.get_filename_xpm)
        self.comment_button.config(command=self.user_entry)
        self.guide_button.config(command=self.help_window_func)
        self.test_opus_button.config(command=self.test_opus)
        self.view_aux_button.config(command=self.aux_window_func)
        
        self.run_daily_checkbutton=builder.get_object('run_daily_checkbutton',self.root)
        self.dynamic_mode_checkbutton=builder.get_object('dynamic_mode_checkbutton',self.root)
        self.legacy_format_checkbutton=builder.get_object('legacy_format_checkbutton',self.root)
        self.use_aux_flag_data_checkbutton=builder.get_object('use_aux_data_checkbutton',self.root)
        self.run_daily_checkbutton.config(variable=self.run_daily_mode,command=self.run_daily_stat)
        self.dynamic_mode_checkbutton.config(variable=self.dynamic_schedule_mode,command=self.dynamic_stat)
        self.legacy_format_checkbutton.config(variable=self.legacy_format_mode,command=self.legacy_format_stat)
        self.use_aux_flag_data_checkbutton.config(variable=self.use_aux_flag_mode,command=self.use_aux_stat)

 
 
        
        """Schedule Objects"""
        
        
        self.schedule_hsbar=builder.get_object('schedule_hsbar',self.root)
        self.schedule_vsbar=builder.get_object('schedule_vsbar',self.root)
        self.schedule_listbox.config(yscrollcommand=self.schedule_vsbar.set,xscrollcommand=self.schedule_hsbar.set)
        self.schedule_hsbar.config(command=self.schedule_listbox.xview)
        self.schedule_vsbar.config(command=self.schedule_listbox.yview)
        self.schedule_listbox.bind("<<ListboxSelect>>", self.OnDouble)

        
        """Command Log and Output Objects"""
        
        self.log_out_text=builder.get_object('log_out_text',self.root)
        self.log_out_scrollbar=builder.get_object('log_out_scrollbar',self.root)
        self.current_status_label=builder.get_object('current_status_label',self.root)
        self.log_out_text.config(yscrollcommand=self.log_out_scrollbar.set)
        self.log_out_scrollbar.config(command=self.log_out_text.yview)
        self.log_out_text.tag_add("here","1.0","2.0")
        self.log_out_text.tag_config("here",foreground="blue")
        self.log_out_text.delete("1.0",END)
        
        """Define Initial Variables"""

        self.schedule_colors=['white','red','red','orange','green','blue']

        self.process_ids=[]   
        self.proc=None
        self.lock=threading.Lock()
        
        self.current_xpm=-1
        
        self.task_status=-1
        self.abort_flag=0
        self.skip_cont=0
        self.reset_flag=1
        self.initialising_flag=0
        

        self.schedule_status=int(startup['schedule_status'])
        self.gui_test_mode=int(startup['gui_test_mode'])
        self.simulator_mode=int(startup['simulator_mode'])
        self.dynamic_margin_time=int(site['dynamic_margin_time'])
        self.get_combofiles()
        self.schedule_combobox.config(values=self.regular_files)
        self.dynamic_combobox.config(values=self.dynamic_files)
        self.schedule_combobox.bind('<<ComboboxSelected>>',self.schedule_selected)
        self.dynamic_combobox.bind('<<ComboboxSelected>>',self.dynamic_selected)

        self.schedule_combobox.set(def_paths_files['schedulefile'])
        self.dynamic_combobox.set(def_paths_files['databasefile'])
        self.schedule_file=def_paths_files['schedulefile']
        self.dynamic_file=def_paths_files['databasefile']




        self.sched_run_flag=0
        self.task_run=0
        self.link=None
        self.id1=None
        self.macro_id=None
        self.polling="Not Polling"
        self.lock=threading.RLock()

        
       # self.create_log_file()
        self.current_schedule_mode=self.dynamic_schedule_mode.get()

        """Configure buttons to appropriate initial states"""
        self.dynamic_mode_checkbutton.configure(state="disabled")
        self.abort_task_button.configure(state="disabled")
        if self.schedule_status==0:
            self.schedule_run_button.config(text="Start Schedule")
            self.dynamic_mode_checkbutton.configure(state="normal")
            self.task_countdown_entry.config(background='red')
            self.scheduled_task_entry.config(background='red')
        else:
            self.task_countdown_entry.config(background='green')
            self.scheduled_task_entry.config(background='green')
        self.create_log_file()
        self.write_output("Welcome to ASAP") 
        
        
        """Plot Window"""
        
#        self.plot_window=FigureCanvasTkAgg(f,self.root)
#        self.plot_window.show()
#        self.plot_window.get_tk_widget().grid(column=0,row=0)
#        
        """Thread out the schedule process"""    
        self.daily_info=None
        self.reset_time=get_local_time(int(site['timezone']))+datetime.timedelta(hours=24)
        self.reset_time=self.reset_time.replace(hour=1,minute=0,second=0)
        
        
        
        """Configure the auxiliary data, we first need to check if the ability to
        gather aux is enabled"""
        self.gather_aux=gather_aux
        if self.gather_aux==0:
            self.aux_flag=0
            self.use_aux_flag_data_checkbutton.configure(state="disabled")
            self.view_aux_button.configure(state="disabled")

        """Create a log file"""

        """Begin the main loop"""
        self.aux_it_stop=int(aux_tp/(0.2))
        self.aux_it=0
        self.update_aux()
        self.threaded_solar()

        self.update_clock_main()
        self.root.mainloop()
        
    def schedule_selected(self,event=None):
        if event:
            selected=self.schedule_combobox.get()
            if selected!=self.schedule_file:
                self.schedule_file=selected
                if self.dynamic_schedule_mode.get()==0:
                    self.threaded_solar()
                    
        
    def dynamic_selected(self,event=None):
        if event:
            selected=self.dynamic_combobox.get()
            if selected!=self.dynamic_file:
                self.dynamic_file=selected
                if self.dynamic_schedule_mode.get()==1:
                    self.threaded_solar()
                    
            
    def get_combofiles(self):
        files = [f for f in os.listdir(def_paths_files['schedulespath']) if os.path.isfile(os.path.join(def_paths_files['schedulespath'], f))]
        dynamic_files=[]
        regular_files=[]
        for f in files:
            if 'database' in f:
                dynamic_files.append(f)
            else:
                regular_files.append(f)
                
        self.regular_files=regular_files
        self.dynamic_files=dynamic_files
        
    
    
    def legacy_format_stat(self):
        if self.legacy_format_mode.get()==1:
            text="Legacy format mode enabled"
        else:
            text="Legacy format mode disabled"
        self.write_output(text)
        
    def run_daily_stat(self):
        if self.run_daily_mode.get()==1:
            text="Run daily mode enabled"
        else:
            text="Run daily mode disabled"
        self.write_output(text)
        
    def dynamic_stat(self):
        if self.dynamic_schedule_mode.get()==1:
            text="Dynamic schedule mode enabled"
        else:
            text="Dynamic schedule mode disabled"

        self.write_output(text)
        self.threaded_solar()

        
    def use_aux_stat(self):
        if self.use_aux_flag_mode.get()==1:
            text="Auxiliary flag mode enabled"
            
        else:
            text="Auxiliary flag mode disabled"
	self.update_aux()
        self.write_output(text)
        
    def on_close_aux(self)   :
        self.aux_window.withdraw()

    def update_aux(self):
        """if gather_aux in the ini is set to 1, this code will attempt to gather
        data and flag using the user created gather_auxiliary_data function in aux_data.py"""
        
        if self.gather_aux==1:
            self.aux_labels=aux_labels
            self.aux_data,self.aux_flag=gather_auxiliary_data()
            #self.view_aux_button.configure(state="normal")
	    #print self.aux_data
        """Decides if you are going to use the flag provided by the aux, if not, then it
        leaves it as zero"""
        if self.use_aux_flag_mode.get()==0:
            self.aux_flag=0
 
        """Updates the data in the aux data window"""
        if self.aux_window.state()=='normal' and self.gather_aux==1:
            dimension=len(self.aux_data)
            self.aux_data_listbox.delete(0,END)
            self.aux_label_listbox.delete(0,END)
            for j in range(len(self.aux_labels)):
                self.aux_label_listbox.insert(END,str(self.aux_labels[j]))
                try:
                    self.aux_data_listbox.insert(END,str(self.aux_data[j]))
                except:
                    self.aux_data_listbox.insert(END,"nan")
            self.aux_data_listbox.insert(END,str(self.aux_flag))  
	    self.aux_label_listbox.insert(END,"Flag")
        
        """Cunningly adds an extra message (or removes it when turned off) if 
        the aux flag has been used to stop a task"""
        if self.schedule_status==1:
            text=self.current_status_label.cget("text")
            if " - Schedule halted due to Aux" not in text and self.aux_flag==1:
                text = text+" - Schedule halted due to Aux"
            if " - Schedule halted due to Aux" in text and self.aux_flag==0:
                text=text.split('-')[0]
            self.current_status_label.configure(text=text)
    
        
       #self.write_output(str( self.aux_flag))
      #  """Runs every aux_tp seconds"""
        #self.root.after(int(aux_tp)*1000, self.update_aux)
        
    def update_aux_main(self):
        """As below but for the aux function"""
        self.update_aux()
        """Runs every aux_tp seconds"""
        self.aux_loop=self.root.after(int(aux_tp)*1000, self.update_aux)
        
    def update_clock_main(self):
        """Function that calls update clock every 200ms, they are separated to allow
        manual calls of update clock"""
        self.update_clock()
        self.main_loop=self.root.after(200, self.update_clock_main)
        
    def update_clock(self):
        """Main running routine, call to refresh values on screen"""
        now=get_local_time(int(site['timezone']))
        """Reset Schedule at 1am each day"""        
        
        if (self.reset_time-now).total_seconds()<0 and self.reset_flag==0: 
            self.reset_flag=1
            self.reset_time=self.reset_time+datetime.timedelta(hours=24)
            self.daily_info=None
            """Move the stdout to the daily directory"""
#            sys.stdout.close()
#            if os.path.exists(log_path+"gui_log.dat"):
#                move(log_path+"gui_log.dat",os.path.dirname(self.schedule_pathout)+"\\gui.log")  
#            if os.path.exists(log_path+"exec_log.dat"):
#                move(log_path+"exec_log.dat",os.path.dirname(self.schedule_pathout)+"\\exec.log")  
#                
#            sys.stdout= open(log_path+"gui_log.dat","a")
#            sys.stderr=sys.stdout
            
            """Begin reset"""
            year=str(now.year)
            month="%02d" % now.month
            day="%02d" % now.day
            hour="%02d" % now.hour
            todayspath=year+month+day
            print "here_1"
            
            """Make a new log file"""
#            self.schedule_pathout=def_paths_files['datapath']+todayspath+"\\"+todayspath+".log"
#            
#            if not os.path.exists(os.path.dirname(self.schedule_pathout)):
#               
#                os.makedirs(os.path.dirname(self.schedule_pathout))

            #reload(library)
            
            print str(get_local_time(int(site['timezone'])))
            self.create_log_file()
            
            """Shall I run the next schedule?"""
            if self.run_daily_mode.get()==0:
                self.turn_off_schedule()
         
            self.current_xpm=-1
            
            self.task_status=-1
            self.skip_cont=0
            self.sched_run_flag=0
            self.task_run=0
            self.log_out_text.delete("1.0",END)
            self.write_output("ASAP Refreshed")

            if len(self.process_ids)>0:
                self.write_output("Performing Cleanup of Lost Processes")
                self.clean_up()
            
            """May as well calculate the next schedule anyway"""
            self.threaded_solar()
              

        """Seperate Execution for different Schedule Modes"""
        
        """Basic Mode"""  
        
        if self.dynamic_schedule_mode.get()==0 and self.reset_flag==0:
            
           # if self.schedule_status==1:
#                self.task_index=find_next_time(array(self.schedule.all_times),self.schedule.task_flags,get_local_time(int(site['timezone'])))
#                self.next_task_time=self.schedule.all_times[self.task_index]
#                self.next_task_name=str(self.schedule.all_ids[self.task_index])
            countdown_out=format_countdown(self.next_task_time-now)
            if self.task_index==-1:
                countdown_out='00:00:00'
                self.next_task_name='Schedule Complete'
                self.scheduled_task_entry.configure(text=self.next_task_name)

            elif (self.next_task_time-now).total_seconds()<0:
                print (self.next_task_time-now).total_seconds(),self.next_task_time
                taskname=self.next_task_name    
                task_id=self.task_index
                self.task_index=find_next_time(array(self.schedule.all_times),self.schedule.task_flags,now+datetime.timedelta(seconds=10))
                self.next_task_time=self.schedule.all_times[self.task_index]
                self.next_task_name=str(self.schedule.all_ids[self.task_index])
                self.scheduled_task_entry.configure(text=self.next_task_name)

                if self.schedule_status==1:

                    if self.task_run==0 and self.aux_flag==0 and self.initialising_flag==0:
                        self.task_status=task_id      
                        self.process_initialisation(taskname,xpmpath=def_paths_files['xpmpath'],taskpath=def_paths_files["taskspath"],task_type="basic_schedule")
                    
                    elif self.initialising_flag==0:
                        if self.task_run!=0 or self.aux_flag==1:
                            text="Skipped "+taskname+' '+str(task_id)+' '
                            if self.aux_flag==1:
                                text=text+" - Aux Flag"
                            if self.task_run==1:
                                text=text+" - Busy"
                            print self.next_task_time
                            self.write_output(text)
                            self.comments[task_id]=text
                            self.schedule.task_flags[task_id]=3
                            self.schedule_listbox.itemconfig(task_id,{'bg':self.schedule_colors[3]})
                   

                else:
                    text="Missed "+taskname+' '+str(task_id)+' - Schedule Not Running'
     
                    print self.next_task_time
                    self.write_output(text)
                    self.comments[task_id]=text
                    self.schedule.task_flags[task_id]=3
                    self.schedule_listbox.itemconfig(task_id,{'bg':'yellow'})
                    
#                self.task_index=find_next_time(array(self.schedule.all_times),self.schedule.task_flags,now+datetime.timedelta(seconds=10))
#                self.next_task_time=self.schedule.all_times[self.task_index]
#                self.next_task_name=str(self.schedule.all_ids[self.task_index])

                    #self.skip_cont=1
#                elif (self.next_task_time-now).total_seconds<0  and self.task_run!=0:# and self.skip_cont==0:
#                    #self.skip_cont=1
#
#                    self.task_index=find_next_time(array(self.schedule.all_times),self.schedule.task_flags,get_local_time(int(site['timezone'])))
#                    self.next_task_time=self.schedule.all_times[self.task_index]
#                    self.next_task_name=str(self.schedule.all_ids[self.task_index])
                    #self.skip_cont=0


#        		if self.next_task_time-now>datetime.timedelta(seconds=1):
#                    self.skip_cont=0


#    

                
        """Dynamic Mode"""    
       
        if self.dynamic_schedule_mode.get()==1 and self.reset_flag==0:
            self.task_index=find_next_time_nf(array(self.schedule.all_times),get_local_time(int(site['timezone'])))
            self.task_time2=self.schedule.all_times[self.task_index]
            countdown_out=format_countdown(self.task_time2-get_local_time(int(site['timezone'])))

            if self.schedule_status==1:
                if self.task_index!=-1:
                    self.time_left=self.task_time2-get_local_time(int(site['timezone']))
                    if self.task_run==0 and self.aux_flag==0 and self.initialising_flag==0:
                        if self.task_index==0:
                            self.next_task_name="Waiting"
                            self.scheduled_task_entry.configure(text=self.next_task_name)
                    
                        else:
                        
                            if self.time_left>datetime.timedelta(minutes=int(self.dynamic_margin_time)) or (self.task_counts[self.task_index-1]>0 and self.time_left>datetime.timedelta(seconds=int(self.durations[self.task_index-1])) and self.schedule.task_types[self.task_index]!="T"):
                                self.next_task_name=str(self.schedule.all_ids[self.task_index-1])
                                self.task_status=self.task_index-1
                                self.scheduled_task_entry.configure(text=self.next_task_name)
                                if self.schedule.task_flags[self.task_status]!=-1:

                                    self.task_counts[self.task_index-1]+=1
                                    self.process_initialisation(self.next_task_name,xpmpath=def_paths_files['xpmpath'],taskpath=def_paths_files["taskspath"],task_type="dynamic_schedule")
                                    self.write_output("counts = "+str(self.task_counts[self.task_index-1]))
                            elif self.time_left<datetime.timedelta(minutes=int(self.dynamic_margin_time)) and self.schedule.task_types[self.task_index]!="T":
                                current_task=self.task_index
                                self.next_task_name=str(self.schedule.all_ids[self.task_index])
                                self.scheduled_task_entry.configure(text=self.next_task_name)
                                self.task_status=self.task_index
                                self.task_counts[self.task_index]+=1
                                self.write_output("counts = "+str(self.task_counts[self.task_index]))
                                self.process_initialisation(self.next_task_name,xpmpath=def_paths_files['xpmpath'],taskpath=def_paths_files["taskspath"],task_type="dynamic_schedule")
                    if self.task_run==0 and self.aux_flag==1:
                            self.next_task_name="Waiting"
                            self.scheduled_task_entry.configure(text=self.next_task_name)     
                    elif self.time_left>=datetime.timedelta(seconds=1) and self.task_run!=0 and self.skip_cont==0 and self.task_counts[self.task_index-1]==0:
                        self.skip_cont=1
                        text="Skipped Task"
                        if self.aux_flag==1:
                            text=text+" - Aux Flag"
                        if self.task_run==1:
                            text=text+" - Busy"
                        self.write_output(text)
                        self.comments[self.task_index-1]=text
                        self.schedule.task_flags[self.task_index-1]=3
                        self.schedule_listbox.itemconfig(self.task_index-1,{'bg':self.schedule_colors[3]})           

                else:
                    countdown_out='00:00:00'
                    self.next_task_name='Schedule Complete'
                    self.scheduled_task_entry.configure(text=self.next_task_name)
        
#        if self.schedule_status==0:
#            countdown_out='  n/a   '
	    
#            self.next_task_name='Schedule Stopped'
#            self.scheduled_task_entry.configure(text=self.next_task_name)


        if self.reset_flag==1:
            countdown_out='  n/a   '
            self.next_task_name='Schedule Loading'
            self.scheduled_task_entry.configure(text=self.next_task_name) 


            
        now_utc=now-datetime.timedelta(hours=int(site['timezone']))
        self.utctime_entry.configure(text=format_time(now_utc))
        self.localtime_entry.configure(text=format_time(now))
        sza=sunzen_ephem(now_utc,float(site['latitude']),float(site['longe']),float(site['pressure']),float(site['temperature']))[0]
        self.sza_entry.configure(text="%.2f" % sza)
        self.elv_entry.configure(text="%.2f" %(90.-sza))
        self.color_lines()
        self.task_countdown_entry.configure(text=countdown_out)
	self.aux_it=self.aux_it+1
	if self.aux_it==self.aux_it_stop:
            self.aux_it=0
	    self.update_aux()
        #self.root.after(200, self.update_clock)



    """ Internal Functions in rough order of use amount"""
    def on_close(self):
        """Function to decide what to do when the gui is closed"""
        self.clean_up()
      #  self.write_output("ASAP Closed")
        self.root.destroy()
        
    def clean_up(self):
        """Clean up any dead processes, shouldnt be needed"""
        processes=psutil.pids()
        for i in range(len(self.process_ids)):
	    try:
            	if self.process_ids[i] in processes:
                    self.write_output("One Orphan Found - "+str(self.process_ids[i]))
                    process=psutil.Process(self.process_ids[i])
                    process.kill()
	    except:
		    self.write_output("Failed to kill Orphan - "+str(self.process_ids[i])+" proceeding anyway")
	self.process_ids=[]
 
    def abort_task(self):
        """Sets an abort flag to true (1) so that the remaining xpms in a task are cancelled"""
        self.abort_flag=1
        self.write_output("Cancelling remaining xpms in task "+self.taskname+". Waiting for current xpm to finish")
        self.abort_task_button.config(state="disabled")
        
    def test_opus(self):
        """Start the threaded processes to check the state of the opus dde link"""
        self.thread_output=None
        xpmpath=def_paths_files["xpmpath"]
        taskpath=def_paths_files["taskspath"]
        to=threading.Thread(target=self.begin_opus_process,args=("test_dde",xpmpath,taskpath,))
        to.start()


    def threaded_solar(self):
        """Starts the solar calculations for the schedule and daily info, ran from thread"""
        
        self.dynamic_mode_checkbutton.config(state="disabled")
        self.dynamic_combobox.config(state='disabled')
        self.schedule_combobox.config(state='disabled')

        #if self.schedule_status==0:
        self.schedule_run_button.config(state="disabled")
#        print self.schedule
#        self.schedule=None
        if self.daily_info==None:
            self.write_output("Calculating Daily Information, Please Wait")
            #self.daily_info=daily_info(float(site['latitude']),float(site['longe']),float(site['timezone']),float(site['pressure']),float(site['temperature']))
            #self.update_info()
            t2=ThreadWithReturnValue(target=daily_info,args=(float(site['latitude']),float(site['longe']),float(site['timezone']),float(site['pressure']),float(site['temperature'])))
            t2.start()
            """While the thread is going, check on it, once finished proceed"""
            while t2.isAlive():
                self.update_clock()
                self.root.update()
                time.sleep(0.2)
            self.daily_info=t2.join()
            self.update_info()
        if self.dynamic_schedule_mode.get()==1:
            self.write_output("Calculating Dynamic Schedule")
            self.schedule=load_schedule(1,def_paths_files['schedulespath']+self.dynamic_file,self.daily_info)
            self.task_counts=zeros(len(self.schedule.all_times))
            self.durations=[datetime.timedelta(seconds=0)]*len(self.schedule.all_times) 
        else:
            self.write_output("Calculating Regular Schedule")
            self.schedule=load_schedule(0,def_paths_files['schedulespath']+self.schedule_file,self.daily_info)
            self.durations=[datetime.timedelta(seconds=0)]*len(self.schedule.all_times)
            
      #  print 'hello',len(self.schedule.all_ids)
        if len(self.schedule.all_ids)!=0:
            self.log_schedule()

            self.current_schedule_mode=self.dynamic_schedule_mode.get()
            
            self.task_info=self.schedule.all_times[:]
            
            self.schedule_listbox.delete(0,END)
    
            for i in range(len(self.schedule.all_times)):
                self.schedule_listbox.insert(END,datetime.datetime.strftime(self.schedule.all_times[i],'%H:%M:%S')+" - "+str(self.schedule.all_ids[i]))
                self.schedule_listbox.itemconfig(i,{'bg':self.schedule_colors[int(self.schedule.task_flags[i])]})
            self.write_output("Completed")
    
            if self.dynamic_schedule_mode.get()==1:
                self.write_output("Loaded Dynamic Schedule")
            if self.dynamic_schedule_mode.get()==0:
                self.write_output("Loaded Regular Schedule")
            self.task_index=find_next_time(array(self.schedule.all_times),self.schedule.task_flags,get_local_time(int(site['timezone'])))
            self.next_task_time=self.schedule.all_times[self.task_index]
            self.next_task_name=str(self.schedule.all_ids[self.task_index])
    
            self.scheduled_task_entry.configure(text=self.next_task_name)
            

        else:
            self.next_task_name='Failed'
            self.scheduled_task_entry.configure(text=self.next_task_name) 
            self.write_output("Failed to Load Schedule")
            
        
        self.reset_flag=0
        self.schedule_run_button.config(state="normal")
        self.dynamic_mode_checkbutton.config(state="normal")
        self.dynamic_combobox.config(state='normal')
        self.schedule_combobox.config(state='normal')
        
    def process_initialisation(self,taskname,xpmpath,taskpath,task_type="manual"):
        """function that calls that initiates the process function in various forms dep
        ending on the job conditions"""
        self.initialising_flag=1
        self.start_time=get_local_time(int(site['timezone']))
        self.config_all_buttons(state="disabled")
        self.abort_task_button.config(state="normal")
        self.taskname=taskname
        
        if task_type=="manual":
            print "here"
           # self.taskname=self.manual_task_entry.cget("text")
            if self.taskname=="Select Task or Xpm":
                self.write_output("No Task or Xpm selected")
                self.config_all_buttons(state="normal")
                self.test_opus_button.config(state="normal")
                self.abort_task_button.config(state="disabled")

            else:
                self.write_output("Running Task - "+str(self.taskname))#+" Macro ID - "+str(self.macro_id))
                self.task_run=1
                self.sched_run_flag=0
                self.timestamp=format_time(self.start_time)
                self.current_status_label.configure(text="Current Status: Running Manual Job")
                print self.taskname
                self.begin_opus_process(self.taskname,xpmpath,taskpath)
              #  self.t1=threading.Thread(target=self.begin_opus_process,args=(self.taskname,xpmpath,taskpath,))
              #  self.t1.start()
            
            
        if task_type=="basic_schedule":
#            self.task_run=1
#            self.sched_run_flag=1
          #  self.taskname=self.scheduled_task_entry.cget("text")
            #self.timestamp=format_time(self.start_time)
            self.write_output("Running Job - "+str(self.taskname))#+" Macro ID - "+str(self.macro_id))
            self.task_run=1
            self.sched_run_flag=1
            self.current_status_label.configure(text="Current Status: Running Scheduled Job")

            self.schedule.task_flags[self.task_status]=4
            self.schedule_listbox.itemconfig(self.task_status,{'bg':self.schedule_colors[int(self.schedule.task_flags[self.task_status])]})
            self.comments[self.task_status]="Running, Started at "+self.timestamp
           # self.update_schedule()
           # self.submit_job(self.taskname,str(self.format_style.get()))

            self.begin_opus_process(self.taskname,xpmpath,taskpath) 
#            self.t1=threading.Thread(target=self.begin_opus_process,args=(self.taskname,xpmpath,taskpath,))
#            self.t1.start()

        if task_type=="dynamic_schedule":
            self.task_run=1
            self.sched_run_flag=1
            #self.taskname=self.scheduled_task_entry.cget("text")
            self.timestamp=format_time(self.start_time)
            self.write_output("Running Job - "+str(self.taskname))#+" Macro ID - "+str(self.macro_id))
            self.current_status_label.configure(text="Current Status: Running Dynamic Job")
            self.schedule.task_flags[self.task_status]=4
            self.schedule_listbox.itemconfig(self.task_status,{'bg':self.schedule_colors[int(self.schedule.task_flags[self.task_status])]})
            self.comments[self.task_status]="Running, Started at "+self.timestamp
           # self.submit_job(self.taskname,str(self.format_style.get()))

            #self.update_schedule()
            self.begin_opus_process(self.taskname,xpmpath,taskpath)
           # self.t1=threading.Thread(target=self.begin_opus_process,args=(self.taskname,xpmpath,taskpath,))
           # self.t1.start()
        
        
 

       # self.root.after(100, self.check_run)
        
        
    def create_log_file(self):
        """Redundant? why do we need create log and create schedule?"""
        now=get_local_time(int(site['timezone']))
        year=str(now.year)
        month="%02d" % now.month
        day="%02d" % now.day
        hour="%02d" % now.hour
        todayspath=year+month+day   
        self.timestamp=format_time(now)
        self.schedule_pathout=def_paths_files['datapath']+todayspath+"\\"+todayspath+".log"
            
        if not os.path.exists(os.path.dirname(self.schedule_pathout)):
            try:
                os.makedirs(os.path.dirname(self.schedule_pathout))
            except:
                pass
	    f=open(self.schedule_pathout,"a")
	    f.write("** weather, cell info\n")
            f.close()

    def log_schedule(self):
        """See above"""
        now=get_local_time(int(site['timezone']))
        year=str(now.year)
        month="%02d" % now.month
        day="%02d" % now.day
        hour="%02d" % now.hour
        todayspath=year+month+day
        """Check if the log exists, I cant think of a case where it wouldnt but lets check"""
        self.create_log_file()
        if self.dynamic_schedule_mode.get()==0:
 
            self.comments=[]

            for i in range(len(self.schedule.all_times)):
                if int(self.schedule.task_flags[i])==1:
                    self.comments.append("Cancelled due to invalid time")
                if int(self.schedule.task_flags[i])==2:
                    self.comments.append("Cancelled due to invalid sza")    
                if int(self.schedule.task_flags[i])==0:
                    self.comments.append("Scheduled")
            print len(self.comments)
            f=open(self.schedule_pathout,"a")
           # f.write(self.timestamp+" BrukeryPy Restarted\n")
        
            f.write("Regular Schedule Mode\n")
            f.write("Log file for "+todayspath+" at "+site["sitename"]+"\n")
            f.write("Site Info: latitude "+site["latitude"]+", Longitude (EAST) "+site["longe"]+", Timezone "+site["timezone"]+"\n")
            f.write("Daily Info: Sunrise "+str(self.daily_info.sunrise)+", Sunset "+str(self.daily_info.sunset)+", Day Length "+str(self.daily_info.day_length)+", High Sun "+str(self.daily_info.high_sun_sza)+" @ "+str(self.daily_info.high_sun_time)+"\n")
      

            f.write("\n")
            f.write("Todays Schedule and Log\n")
            f.write(" \n")
            for i in range(len(self.schedule.all_times)):
                f.write(str(i))
                f.write(" ")
                f.write(str(format_time(self.schedule.all_times[i])))
                f.write(" ")
                f.write(str(self.schedule.all_ids[i]))
                f.write(" ")
                f.write(self.comments[i])
                f.write("\n")
            f.write("\n")
            f.write("Console output and User Comment\n")
            f.write(" \n")
            f.close()
        if self.dynamic_schedule_mode.get()==1:

            self.comments=[]
            #print len(self.task_flags), len(self.all_times)
            offset=9
            for i in range(len(self.schedule.all_times)):
                if int(self.schedule.task_flags[i])==1:
                    self.comments.append("Cancelled due to invalid time")
                if int(self.schedule.task_flags[i])==2:
                    self.comments.append("Cancelled due to invalid sza")    
                if int(self.schedule.task_flags[i])==0:
                    self.comments.append("Scheduled")

            f=open(self.schedule_pathout,"a")
           # f.write(self.timestamp+" BrukeryPy Restarted\n")
            f.write("Dynamic Schedule Mode\n")
            f.write("Log file for "+todayspath+" at "+site["sitename"]+"\n")
            f.write("Site Info: latitude "+site["latitude"]+", Longitude (EAST) "+site["longe"]+", Timezone "+site["timezone"]+"\n")
            f.write("Daily Info: Sunrise "+str(self.daily_info.sunrise)+", Sunset "+str(self.daily_info.sunset)+", Day Length "+str(self.daily_info.day_length)+", High Sun "+str(self.daily_info.high_sun_sza)+" @ "+str(self.daily_info.high_sun_time)+"\n")
            f.write("\n")
            f.write("Todays Schedule and Log\n")
            for i in range(len(self.schedule.all_times)):
                f.write(str(i))
                f.write(" ")
                f.write(str(format_time(self.schedule.all_times[i])))
                f.write(" ")
                f.write(str(self.schedule.all_ids[i]))
                f.write(" ")
                f.write(self.comments[i])
                f.write("\n")
            f.write("\n")
            f.write("Console output and User Comment\n")  
            f.close()
    
    def OnDouble(self, event):
        """on selection in the schedule, return information to the log out"""
        widget = event.widget
        selection=widget.curselection()[0]
        text=str(self.comments[selection])
        """Do I keep the log file open? I think no because if i crash out I will lose it for that day"""
        self.write_output_screen(text)



    def color_lines(self):
        """Removes and applies colour tag for the log output screen"""
        self.log_out_text.tag_remove("here","1.0","end")
        self.log_out_text.tag_add("here","1.0","2.0-1c")



    def write_output(self,text):
        """Write text to the output and to the log file"""
        self.timestamp=format_time(get_local_time(int(site['timezone'])))
        with self.lock:
            self.create_log_file()

            self.log=open(self.schedule_pathout,"a")
            self.log.write(self.timestamp+" "+text+"\n")
            self.log.close()
            self.current_file_size=int(os.path.getsize(self.schedule_pathout))
            self.log_out_text.insert("0.0",self.timestamp+" "+text+"\n")



    def write_output_screen(self,text):
        """Just write to the screen, redundant?"""
        self.timestamp=format_time(get_local_time(int(site['timezone'])))
        self.log_out_text.insert("0.0",self.timestamp+" "+text+"\n")



        
    def config_all_buttons(self,state):
        """Switch the state of the manual buttons"""
        self.manual_task_button.config(state=state)
        self.manual_xpm_button.config(state=state)
        

    def get_filename_task(self):
        
        """Get the manual task to run and execute it"""
        file_path = filedialog.askopenfilename(initialdir=def_paths_files["taskspath"]).split('/')
        filename=file_path[-1]
        if filename=='':
            filename="Select Task or Xpm"
        path=''
        for i in range(len(file_path)-1):
            path=path+file_path[i]+'/'
        self.manual_task_entry.configure(text=filename)
        print path
        
        self.process_initialisation(filename,xpmpath=def_paths_files['xpmpath'],taskpath=path,task_type="manual")


    def get_filename_xpm(self):
        """Get the xpm to run adn execute"""
        file_path = filedialog.askopenfilename(initialdir=def_paths_files["xpmpath"]).split('/')
        filename=str(file_path[-1])
        if filename=='':
            filename="Select Task or Xpm"
        path=''
        for i in range(len(file_path)-1):
            path=path+file_path[i]+'/'
            #print path
        
        self.manual_task_entry.configure(text=filename)  
        self.process_initialisation(filename,xpmpath=path,taskpath=def_paths_files["taskspath"],task_type="manual")
        
    def toggle_schedule_run(self):
        """Turns the schedule on and off and reload the schedule if it has changed
        type"""
        
        if self.schedule_status==1:        
            self.schedule_run_button.config(text="Start Schedule")
            self.schedule_status=0
            self.write_output("Schedule Stopped")
            self.dynamic_mode_checkbutton.config(state="normal")
            self.dynamic_combobox.config(state='normal')
            self.schedule_combobox.config(state='normal')
            self.task_countdown_entry.config(background='red')
            self.scheduled_task_entry.config(background='red')
            self.current_status_label.configure(text="Current Status: Idle")

        elif self.schedule_status==0:
            self.write_output("Schedule Started")
            self.dynamic_combobox.config(state='disabled')
            self.schedule_combobox.config(state='disabled')
            self.dynamic_mode_checkbutton.config(state="disabled")
            self.schedule_run_button.config(text="Stop Schedule")
            self.task_countdown_entry.config(background='green')
            self.scheduled_task_entry.config(background='green')
            self.schedule_status=1
            self.current_status_label.configure(text="Current Status: Waiting for Job")

            if self.current_schedule_mode!=self.dynamic_schedule_mode.get():
                self.current_schedule_mode=self.dynamic_schedule_mode.get()
                if self.dynamic_schedule_mode.get()==1:
                    self.reset_flag=1

                    self.threaded_solar()               
                    self.task_counts=zeros(len(self.schedule.all_times))
                    self.durations=[datetime.timedelta(seconds=0)]*len(self.schedule.all_times)
                else:
                    self.reset_flag=1

                    self.threaded_solar()               
                 
                    self.durations=[datetime.timedelta(seconds=0)]*len(self.schedule.all_times)

                    
                for i in range(len(self.schedule.all_times)):
                    self.schedule_listbox.insert(END,datetime.datetime.strftime(self.schedule.all_times[i],'%H:%M:%S')+" - "+str(self.schedule.all_ids[i]))
                    self.schedule_listbox.itemconfig(i,{'bg':self.schedule_colors[int(self.schedule.task_flags[i])]})


            
    def turn_off_schedule(self):
        """Just turns the schedule off, redundant?"""
        if self.schedule_status==1:
            self.schedule_run_button.config(text="Start Schedule")
            self.schedule_status=0
            self.write_output("Schedule Stopped")
            self.dynamic_mode_checkbutton.config(state="normal")

    def update_info(self):
        """Repopulate the daily info after new data from threaded solar is availabe"""
        self.high_sun_sza_entry.config(text=(str("%#06.2f" % self.daily_info.high_sun_sza)))
        self.high_sun_time_entry.config(text=str(datetime.datetime.strftime(self.daily_info.high_sun_time,'%H:%M:%S')))
        self.low_sun_sza_entry.config(text=(str("%#06.2f" %  self.daily_info.low_sun_sza)))
        self.low_sun_time_entry.config(text=str(datetime.datetime.strftime(self.daily_info.low_sun_time,'%H:%M:%S')))
        self.sunrise_entry.config(text=str(self.daily_info.sunrise))
        self.sunset_entry.config(text=str(self.daily_info.sunset))
        self.day_length_entry.config(text=str(self.daily_info.day_length))
        
    def user_entry(self):
        """Opens a new window to allow user input"""
        self.user_entry = tk.Toplevel()
        self.user_entry.wm_title("User Entry")
        #self.user_entry.grab_set()
        self.user_entry.focus()
        comment_label=tk.Label(self.user_entry,text="Enter User Comment")
        comment_label.grid(row=0,column=0,sticky=W)
        self.user_comment = tk.Text(self.user_entry,width=80,wrap=CHAR)
        
        self.user_comment.grid(row=1,column=0,columnspan=2,rowspan=10,sticky=N+S+E+W)
        comment_button=tk.Button(self.user_entry,text="Write",relief="raised",command=self.write_comment,width=16)
        comment_button.grid(row=11,column=1,sticky=E,padx=5,pady=6)  
        self.user_comment.focus()

    def aux_window_func(self):
        """Displays the hidden auxiliary data window. The key here is deiconify, we want
        to still be able to update our data but we might not want the window open the whole time, when the 
        window is 'closed' it is actually withdrawn, which means it and all its attributes exist but
        are not displayed, on opening (by running this function) we redraw the window and insert all the data.
        
        Ic could actually skip the insert loops and just call update_aux
        """
        self.aux_window.deiconify()
        self.aux_window.wm_title("Auxiliary Data")
        self.aux_window.focus()
        dimension=len(self.aux_data)
        self.aux_data_listbox=tk.Listbox(self.aux_window)
        self.aux_label_listbox=tk.Listbox(self.aux_window)
        self.aux_data_listbox.grid(row=0,column=1)
        self.aux_label_listbox.grid(row=0,column=0)
        self.aux_refresh_button=tk.Button(self.aux_window,text="Refresh Data",command=self.update_aux)
        self.aux_refresh_button.grid(row=1,column=0,columnspan=2)
        self.update_aux()
#        for j in range(len(self.aux_labels)):
#            self.aux_label_listbox.insert(END,str(self.aux_labels[j]))
#        for i in range(dimension):
#             self.aux_data_listbox.insert(END,str(self.aux_data[i]))
#        self.aux_label_listbox.insert(END,"Flag")
#        self.aux_data_listbox.insert(END,str(self.aux_flag))
        
    def help_window_func(self):
        """Displays the help window accessed by the Guide button"""
        self.help_window = tk.Toplevel()
        self.help_window.wm_title("ASAP Info")
        #self.help_window.grab_set()
        self.help_window.focus()
        
        loc_label=tk.Label(self.help_window,text="Site Information").grid(row=0,column=0,columnspan=2,sticky=W)
        location=tk.Label(self.help_window,text=site['sitename']+" Latitude = "+site['latitude']+" Longitude = "+site['longe']+" UTC Offset = "+site['timezone']).grid(row=1,column=0,columnspan=2,sticky=W)
        met_conditions=tk.Label(self.help_window,text="Surface Pressure = "+site['pressure']+"mb Temperature = "+site['temperature']+" Celsius").grid(row=2,column=0,columnspan=2,sticky=W)
        ini_loc=tk.Label(self.help_window,text="INI File is located at C:/asap_v2.0/asap.ini").grid(row=3,column=0,columnspan=2,sticky=W)

        
        spacer=tk.Label(self.help_window,text="")
        spacer.grid(row=4,columnspan=1)      
        
        
        sched_label=tk.Label(self.help_window,text="Schedule Window Colour Guide:")
        sched_label.grid(row=5,column=0,columnspan=2,sticky=W)
        
        spacer=tk.Label(self.help_window,text="")
        spacer.grid(row=6,columnspan=1)
        
        white_item=tk.Label(self.help_window,text="")
        white_item.config({"bg":"white"})
        white_item.grid(row=7,column=0,sticky=E+W,ipadx=50,padx=50)
        white_item=tk.Label(self.help_window,text="Scheduled")
        #white_item.config({"bg":"white"})
        white_item.grid(row=7,column=1,sticky=W)
 
        white_item=tk.Label(self.help_window,text="")
        white_item.config({"bg":"red"})
        white_item.grid(row=8,column=0,sticky=E+W,ipadx=50,padx=50)
        red_item=tk.Label(self.help_window,text="Cancelled due to invalid SZA or Time")
       # red_item.config({"bg":"red"})
        red_item.grid(row=8,column=1,sticky=W)

        white_item=tk.Label(self.help_window,text="")
        white_item.config({"bg":"orange"})
        white_item.grid(row=9,column=0,sticky=E+W,ipadx=50,padx=50)
        orange_item=tk.Label(self.help_window,text="Skipped")
        #orange_item.config({"bg":"orange"})
        orange_item.grid(row=9,column=1,sticky=W)

        white_item=tk.Label(self.help_window,text="")
        white_item.config({"bg":"green"})
        white_item.grid(row=10,column=0,sticky=E+W,ipadx=50,padx=50)
        green_item=tk.Label(self.help_window,text="Running")
        #green_item.config({"bg":"green"})
        green_item.grid(row=10,column=1,sticky=W)
        
        white_item=tk.Label(self.help_window,text="")
        white_item.config({"bg":"blue"})
        white_item.grid(row=11,column=0,sticky=E+W,ipadx=50,padx=50)
        blue_item=tk.Label(self.help_window,text="Completed")
        #blue_item.config({"bg":"blue"})
        blue_item.grid(row=11,column=1,sticky=W)
        
        spacer=tk.Label(self.help_window,text="")
        spacer.grid(row=12,columnspan=2)
        
        mode_label=tk.Label(self.help_window,text="Operating Modes:")
        mode_label.grid(row=13,column=0,columnspan=2,sticky=W)
        
        spacer=tk.Label(self.help_window,text="")
        spacer.grid(row=14,columnspan=1)
        
        cont_label=tk.Label(self.help_window,text="Run Daily: Automatically starts the next days schedule at 1am local")
        cont_label.grid(row=15,column=0,columnspan=2,sticky=W)
        
        dynam_label=tk.Label(self.help_window,text="Dynamic Mode: Generates a schedule tailored to the current day")
        dynam_label.grid(row=16,column=0,columnspan=2,sticky=W)
        
        leg_label=tk.Label(self.help_window,text="Legacy Format: Uses the original output file format, as opposed to something sensible")
        leg_label.grid(row=17,column=0,columnspan=2,sticky=W)
        
        flag_label=tk.Label(self.help_window,text="Use Aux Flag: Uses the flag generated by the auxilliary data to decide whether or not to run a task")
        flag_label.grid(row=18,column=0,columnspan=2,sticky=W)

        s1_label=tk.Label(self.help_window,text="Start / Stop Schedule: Start Schedule, Stop the schedule from running the NEXT task")
        s1_label.grid(row=19,column=0,columnspan=2,sticky=W)
    
        ab_label=tk.Label(self.help_window,text="Abort Task: Stop the CURRENT task from running any furhter xpms")
        ab_label.grid(row=20,column=0,columnspan=2,sticky=W)
    
        br_label=tk.Label(self.help_window,text="Browse xpms and tasks: browse for desired manual job, default path is set in the ini")
        br_label.grid(row=21,column=0,columnspan=2,sticky=W)
    
        ex_label=tk.Label(self.help_window,text="Execute Task or Xpm: Run the task or xpm selected, will warn you if you havent chosen one")
        ex_label.grid(row=22,column=0,columnspan=2,sticky=W)
    
        enter_label=tk.Label(self.help_window,text="Enter Comment: Enter user comment into the log file")
        enter_label.grid(row=23,column=0,columnspan=2,sticky=W)
    
        test_label=tk.Label(self.help_window,text="Test Opus: Test if the link to opus is still working, will return opus version and instrument if no task is running, and currently polling if a task is")
        test_label.grid(row=24,column=0,columnspan=2,sticky=W)
        
        aux_label=tk.Label(self.help_window,text="View Auxiliary Data: View the auxilliary data and flag generated by the gather_auxiliary_data function in aux_data.py")
        aux_label.grid(row=25,column=0,columnspan=2,sticky=W)
        
    def write_comment(self):
        """Grab the text from the user comment and write it to the log and screen, destroys
        the window once complete"""
        text=str(self.user_comment.get("1.0","end-1c"))
        self.write_output("** "+text+" **")
        self.user_entry.destroy()
     
    def monitor(self,xpm_path,experiment,format_mode,schedule_path,a,b,gui,sim): 
        """Run the process and monitor,on completion, wait a few seconds then end.
        this process is threaded"""
        self.proc=subprocess.Popen(['pythonw','exec_xpm.py',str(xpm_path),experiment,format_mode,str(schedule_path),a,b,gui,sim])
        self.proc.communicate()  
        time.sleep(5)           
        self.proc.kill()
    def begin_opus_process(self,taskname,xpmpath,taskpath):
        """Submit the thread monitored process"""
        endoffile=chr(13)+chr(10)
    

        

        if taskname=="test_dde":
            """Don't bother with generating a process, just do a quick dde com test
            the returned values should match what you see in opus"""
            self.write_output("Testing Opus Link")
            if self.gui_test_mode==0:
                if self.link==None:
                    self.link=None
                    self.id1=None
                    python_server=None
                    self.link=DDEClient("Opus","System")
                    output1=self.link.request("GET_VERSION")
                    output2=self.link.request("GET_BENCH")
        
                    output1=output1.strip("\n")
                    output2=output2.strip("\n")
                    output2=output2.strip("\n")
                    
                    output="Opus Ver. "+str(output1)+" Inst. "+str(output2[4:])
                    
                    self.write_output(str(output))
    
                    DDEClient.__del__(self.link)
                    self.link=None
                    self.id1=None
                else:
                    
    
                    
                    output=self.polling
                    
                    self.write_output(str(output))
            if self.gui_test_mode==1:
                self.write_output("No Opus, I'm in gui test mode")
                
        if taskname[-3:]=="tsk":
            """If we are running a task we are going to allow access to the abort task function
            loop through eaxh experiment in the task file, and submit that xpm as process which accesses
            the exec_xpm.py program. The process is then monitored until completion and the next xpm is started
            unless the abort task flag has been triggered. The reason we use a subprocess rather than just do the 
            communication as above is that on older machines the memory allocation was poor and generating an entirely
            new python process was preferable to a thread, which is still part of the parent process."""
            
            self.abort_task_button.config(state="normal")
            self.start_time_total=get_local_time(int(site['timezone']))
            if os.path.exists(taskpath+taskname):
                experiments=read_task(taskpath+taskname)#genfromtxt(def_paths_files['taskspath']+taskname,dtype=str,skip_header=3,skip_footer=1,unpack=True)[0] #load first column from task file
                
                for p in range(len(experiments)):
                    xpm_path=xpmpath
                    exists=1
                    if not os.path.exists(xpm_path+experiments[p]):
    
                        self.write_output("Can't find "+xpm_path+experiments[p])
                      #  most_recent_line=tail((self.schedule_pathout),lines=1)
                    
                    elif self.abort_flag==0:
                        command=['pythonw','exec_xpm.py',xpm_path,str(experiments[p]),str(self.legacy_format_mode.get()),self.schedule_pathout,str(p+1),str(len(experiments)),str(self.gui_test_mode),str(self.simulator_mode)]
                        print command
    
                        self.write_output("Starting Xpm - "+experiments[p]+" ("+str(p+1)+"/"+str(len(experiments))+")")
                        
                        start_time=get_local_time(int(site['timezone']))
                        """start thread monitored process"""
                        t3=threading.Thread(target=self.monitor,args=(xpm_path,str(experiments[p]),str(self.legacy_format_mode.get()),self.schedule_pathout,str(p+1),str(len(experiments)),str(self.gui_test_mode),str(self.simulator_mode)))
                        t3.start()
                        """While the thread is going, check on it, once finished proceed"""
                        self.initialising_flag=0
                        while t3.isAlive():
                            self.update_clock()
                            self.root.update()
                            time.sleep(0.2)
    
                        duration=(get_local_time(int(site['timezone']))-start_time).seconds
                        self.write_output("Xpm Complete - "+experiments[p]+" Duration "+str(duration)+ " Secs.")
                        
                           
    
                    else:
                        break
                    
                self.task_run=5   
               
                self.end_time=get_local_time(int(site['timezone']))
                self.timestamp=format_time(self.end_time)
                self.duration=str((self.end_time-self.start_time_total).seconds)
                if self.abort_flag==0:
                    self.write_output("Job Complete - "+self.taskname+" Duration "+self.duration+ " Secs.")
                if self.abort_flag==1:
                    self.write_output("Job Abandoned - "+self.taskname+" Duration "+self.duration+ " Secs. after "+experiments[p-1]+" ("+str(p)+"/"+str(len(experiments))+")")
                if self.schedule_status==1 and self.sched_run_flag==1:
                    self.schedule.task_flags[self.task_status]=self.task_run
                   
                    self.schedule_listbox.itemconfig(self.task_status,{'bg':self.schedule_colors[self.task_run]})
                    if self.abort_flag==1:
                        self.comments[self.task_status]="Abandoned at "+self.timestamp+" Duration "+self.duration+" Secs. after "+experiments[p-1]+" ("+str(p)+"/"+str(len(experiments))+")"
                    if self.abort_flag==0:
                        self.comments[self.task_status]="Completed at "+self.timestamp+" Duration "+self.duration+" Secs."
                    if self.dynamic_schedule_mode.get()==1:
                        self.comments[self.task_status]="Completed at "+self.timestamp+" Duration "+self.duration+" Secs. Counts "+str(self.task_counts[self.task_status])
                        if self.abort_flag==1:
                            self.comments[self.task_status]="Abandoned at "+self.timestamp+" Duration "+self.duration+" Secs.  after "+experiments[p-1]+" ("+str(p)+"/"+str(len(experiments))+") Counts "+str(self.task_counts[self.task_status])
    
                    self.durations[self.task_status]=self.duration
                    self.sched_run_flag=0
                 
            else:
                self.end_time=get_local_time(int(site['timezone']))
                self.timestamp=format_time(self.end_time)
                self.duration=str((self.end_time-self.start_time_total).seconds)
                self.write_output("Can't find Task File")

                if self.schedule_status==1 and self.sched_run_flag==1:
                    self.schedule.task_flags[self.task_status]=-1
                   
                    self.schedule_listbox.itemconfig(self.task_status,{'bg':self.schedule_colors[3]})
                    self.comments[self.task_status]="Couldnt find task"

                    self.durations[self.task_status]=self.duration
                    self.sched_run_flag=0
            """Various things to do on completion, update comments and colours, write output
            re-enable various buttons..."""
            

            self.config_all_buttons(state="normal")


            self.task_run=0
            self.manual_task_entry.configure(text="Select Task or Xpm")  
            self.current_status_label.configure(text="Current Status: Waiting for Job")


            self.abort_flag=0
            self.abort_task_button.config(state="disabled")     
                
        
#        
        if taskname[-3:]=="xpm" or taskname[-3:]=="XPM":
            """the same as above, but as its a single xpm, no abort function or loop 
            is needed"""
            xpm_path=xpmpath

            self.abort_task_button.config(state="disabled")
            command='pythonw exec_xpm.py "'+xpmpath+'" '+taskname+' '+str(self.legacy_format_mode.get())+' "'+str(self.schedule_pathout)+'" 1 1 '+str(self.gui_test_mode)+' '+str(self.simulator_mode)
            #command="pythonw exec_xpm.py "+xpmpath+" "+taskname+" "+str(self.legacy_format_mode.get())+" "+self.schedule_pathout+" 1 1 "+str(self.gui_test_mode)+" "+str(self.simulator_mode)
            print command
            
            """Quick check to that the previous process is dead, not really needed"""

            self.write_output("Starting Xpm - "+taskname)
            
            start_time=get_local_time(int(site['timezone']))

            t3=threading.Thread(target=self.monitor,args=(xpm_path,taskname,str(self.legacy_format_mode.get()),self.schedule_pathout,'1','1',str(self.gui_test_mode),str(self.simulator_mode)))
            t3.start()
            self.initialising_flag=0

            while t3.isAlive():
                self.update_clock()
                self.root.update()
                time.sleep(0.2)

            duration=(get_local_time(int(site['timezone']))-start_time).seconds
            self.write_output("Xpm Complete - "+taskname+" Duration "+str(duration)+ " Secs.")
            
            """Far less to do for a single xpm"""
            self.config_all_buttons(state="normal")
            self.manual_task_entry.configure(text="Select Task or Xpm")  
            self.current_status_label.configure(text="Current Status: Waiting for Job")
            self.task_run=0    
        
if __name__=='__main__':
    
    "Lets get down to business! First off, lets get all the default_info from the ini file"
    config=ConfigParser.ConfigParser()
    config.read('asap.ini')
    
    

    site=config_out('site',config)
    def_paths_files=config_out('paths/files',config)
    try:
        gather_aux=json.loads(config.get("aux_properties","gather_aux"))
        aux_labels=json.loads(config.get("aux_properties","labels"))
        aux_tp=json.loads(config.get("aux_properties","time_period"))
    except:
        aux_labels=[]
        aux_tp=60
        gather_aux=0
    
    startup=config_out('startup',config)
    log_path=def_paths_files['python_log_path']
    """Setup python log file"""
#    sys.stdout= open(log_path+"\\gui_log.dat","a")
#    sys.stderr=sys.stdout

    "Start App!"
   # f=Figure(figsize=(5,5),dpi=100)

    App()

    
    
        
        






