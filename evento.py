import numpy as np
import pandas as pd
from string import Template
from ifis_tools import asynch_manager as am
from ifis_tools import auxiliar as aux
from multiprocessing import Pool
import os
import glob

#Warper function
def WarpQsub(comando):
    os.system(comando)

def WarpUpdateGlobals(L):
    am.UpdateGlobal(L[0], L[1])

class Event:

    def __init__(self):
        self.pos1 = None
        self.pos2 = None
        self.Qobs = None
        self.Q190 = None
        self.setups_prev = False

    def SetupBashHeader(self):
        self.BashLines=[
            '#!/bin/sh\n',
            '#$ -N lambdaExp\n',
            '#$ -j y\n',
            '#$ -cwd\n',
            '#$ -pe smp 18\n',
            '####$ -l mf=16G\n',
            '#$ -q IFC\n',
            '#$ -M nicolas-giron@uiowa.edu\n',
            '#$ -m e\n',
            '/bin/echo Running on host: `hostname`.\n',
            '/bin/echo In directory: `pwd`\n',
            '/bin/echo Starting on: `date`\n',
            'module use /Dedicated/IFC/.argon/modules\n',
            'module load asynch\n',
            'source /Users/nicolas/Virtual/forLambdaExp/bin/activate\n'
            'path_exec='+self.path+'/ForRun\n']


    #Funtion to read the base global file 
    def SetTemplate(self,path):
        #Loads the global file
        f = open(path, 'r')
        Global = f.readlines()
        f.close()
        #Read global file 
        self.template = Template(''.join(Global))

    def CheckEpochEnd(self):
        flag = True
        #Check the number of files contained
        while flag:
            numFiles = os.listdir(self.path+'/Initial/') # dir is your directory path
            if len(numFiles) == self.numsetups:
                flag = False
        #Check the total size of the files contained
        flag = True
        while flag:
            #size = os.path.getsize(self.path+'/Initial/')
            size = sum(os.path.getsize(self.path+'/Initial/'+f) for f in os.listdir(self.path+'/Initial/'))
            print(size)
            if size > 10000*len(numFiles):
                flag = False
                print('Termina epoca')

    def Setups_Create(self, RCs, Lambdas):
        #Values of RV, lambda
        Sets = {}
        c = 1
        for Lam in Lambdas:
            for rc in RCs:
                Sets.update({'Set_'+str(c): [Lam, rc]})
                c+=1
        self.setups = Sets
        self.numsetups = c-1

    def Setups_Create2(self, RCs, Lambda):
        #Values of RV, lambda
        Sets = {}
        c = 1
        for rc in RCs:
            Sets.update({'Set_'+str(c): [Lambda, rc]})
            c+=1
        self.setups = Sets
        self.numsetups = c-1

    def CreateInitialDBC(self, initial, path, path_out, nameRun, date1, link):
        proj = am.ASYNCH_project(path,
            path_out,
            nameRun,
            date1 = date1,
            date2 = date1,
            model = '190')
        proj.linkID = link
        proj.__ASYNCH_setInitialFile__(initial,proj.date1[:4],proj.linkID)

    def Setups_Write(self, path, path_out,nameRun, date1, date2, link,Lambda, RC, path2gbl, 
        nprocess = 8, Initial = None, Snapshots = None, SnapInterval =None):
        '''Set_190Run: set a complete asynch project from scratch'''
        proj = am.ASYNCH_project(path,
            path_out,
            nameRun,
            date1 = date1,
            date2 = date2,
            model = '190')
        proj.linkID = link
        # Set lambda
        proj.parameters[2] = Lambda
        # Set RC
        proj.parameters[4] = RC
        #Set the files for run
        #proj.ASYNCH_setRunFile(path2gbl=path2gbl,nprocess=nprocess)
        proj.ASYNCH_setGlobal(OutStatesName=nameRun+'.dat',
            snapName = Snapshots,
            snapTime = SnapInterval,
            createSav = True,
            initial_name = Initial,
            initial_exist = True)

    def execute(self, func, ListaComandos):
        #Multiprocess exec
        p = Pool(processes=8)
        p.map(func, ListaComandos)
        p.close()
        p.join()

    def UpdateGlobals(self, dt, initial_old, initial_new):
        #Actual date
        date_old = self.dateEvent
        date_new = self.dateEvent + pd.Timedelta(dt)
        date_fut = date_new + pd.Timedelta(dt)
        #Get old and new dates
        date_old_t = date_old.strftime('%Y-%m-%d %H:%M')
        date_new_t = date_new.strftime('%Y-%m-%d %H:%M')
        date_fut_t = date_fut.strftime('%Y-%m-%d %H:%M')
        #Unix times to replace
        unix1 = str(aux.__datetime2unix__(date_old_t) + 12*3600)
        unix2 = str(aux.__datetime2unix__(date_new_t) + 12*3600)
        unix3 = str(aux.__datetime2unix__(date_fut_t) + 12*3600)
        #Creates the dictionary with the keys to replace 
        D = {'date_f': {'old': date_new_t, 'new': date_fut_t},
            'date_i': {'old': date_old_t, 'new': date_new_t},
            'initial': {'old': initial_old, 'new': initial_new},
            'unix_f': {'old': unix2, 'new': unix3},
            'unix_i': {'old': unix1, 'new': unix2}}
        #Creates the list for updates of the globals
        Lista = []
        for k in self.setups.keys():
            Lista.append([self.path+'/ForRun/'+k+'.gbl', D])
        #Update globals with a multiprocessing approach
        self.execute(WarpUpdateGlobals, Lista)
        self.dateEvent = date_new

    def ClearInitial(self, Best):
        #Copy the best run 
        comand = 'cp '+self.path+'/Initial/'+Best+'.h5 '+self.path+'/ForRun/Initial.h5' 
        os.system(comand)
        #Erase the rest
        L = glob.glob(self.path+'/Initial/*')
        Lista = []
        for l in L:
            Lista.append('rm '+l)
        self.execute(WarpQsub, Lista)

    def CreateBashFile(self, name=None, status = 'update',nprocess = 8, 
        path = None,d1=None, d2=None, linkID = None, rcs = None, lam = None,
        last = False):
        #Open the files and writes the header
        if status == 'start':
            self.f = open(path, 'w')
            self.f.writelines(self.BashLines)
            print('Start Bash file for run at: '+self.path)
        #Writes the process
        if status == 'update':
            if last is False:
                self.f.write('mpirun -np '+str(nprocess)+' asynch $path_exec/'+name+'.gbl &\n')
            else:
                self.f.write('mpirun -np '+str(nprocess)+' asynch $path_exec/'+name+'.gbl\n')
        #Closes one iterarion
        if status == 'cepoc':
            self.f.write('python analyze.py '+str(linkID)+' '+d1+' '+d2+' '+self.path+' ') 
            self.f.write(' '+lam+' -r ')
            for r in rcs:
                self.f.write(str(r)+' ')
            self.f.write('\n')
        #Closes the file 
        if status == 'close':
            self.f.close()
            print('End writing bash file at: '+self.path)




