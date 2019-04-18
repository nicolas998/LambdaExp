#!/usr/bin/env python

import os
import textwrap
import pandas as pd
import numpy as np
from ifis_tools import asynch_manager as am
from ifis_tools import series_tools as ser
import argparse
import datetime
import glob

################################################################################################################
#PARAMETERS PARSE
################################################################################################################
#Parametros de entrada del trazador

parser=argparse.ArgumentParser(
    prog='analyze.py',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description=textwrap.dedent('''\
            Analyze runs of 190 asynch to determine the best'''))
#Parametros obligatorios
################################################################################################################
#CODE STARTS
parser.add_argument("link",help="Link of Iowa to be analyzed ")
parser.add_argument('d1', type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d-%H%M'))
parser.add_argument("d2", type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d-%H%M'))
parser.add_argument("folder",help = "folder with the data")
parser.add_argument("lam",type=str,help="Strgin with the value of lambd, used for the record", )
parser.add_argument("-r","--rc",nargs='+',type=float,help="List with the RC values to iterate")
parser.add_argument("-f","--first",default = 'no', type = str)
args=parser.parse_args()

################################################################################################################
#READ STREAMFLOW DATA 
###############################################################################################################
d1 = pd.Timestamp(args.d1)
d2 = pd.Timestamp(args.d2)

#def ErrorEstimator(qobs, qsim):
#    p = np.where(np.isfinite(qobs))[0]
#    if p.size / qobs.size > 0.2:
#        Error = np.abs((qobs[p] - qsim[p])/qobs[p])
#        return Error.mean(), 0
#    else:
#        return -9, 1


#def ErrorEstimator(qobs, qsim):
#    p = np.where(np.isfinite(qobs))[0]
#    if p.size / qobs.size > 0.2:
#        Vo = qobs[p].sum()
#        Vs = qsim[p].sum()
#        Error = np.abs(Vo - Vs)
#        return Error, 0
#    else:
#        return -9, 1

def ErrorEstimator(qobs, qsim):
    qobs = qobs.values
    qsim = qsim.values
    c = 1
    flag = True
    while flag:
        if np.isfinite(qobs[-c]):
            Error = np.abs((qobs[-c] - qsim[-c]))
            flag = False
            return Error, 0
        else:
            c+=1
        if c>=qobs.size:
            flag = False
            return -9, 1


#Observed data
Qo = pd.read_msgpack('/Users/nicolas/LambdaExp/BaseData/USGS/'+args.link+'.msg')
Qo.index = Qo.index
#Initial state of some variables 
Best = '0'
BestRute = ''
BestH5 = ''
Eold = 99999
#List of simulations and initial conditions
name = d1.strftime('%Y%m%d%H%M')+'_*_'+args.lam
#ListH5 = glob.glob(args.folder+'/Initial/*_'+args.lam+'.h5')
ListH5 = glob.glob(args.folder+'/Initial/'+name+'.h5')
ListH5.sort()
#ListSim = glob.glob(args.folder+'/Results/*_'+args.lam+'.dat')
ListSim = glob.glob(args.folder+'/Results/'+name+'.dat')
ListSim.sort()

#Find the best one
Values = []
for l1 in ListSim:
    data = am.ASYNCH_results(l1)
    Qs = data.ASYNCH_dat2Serie(args.link, args.d1, '15min')
    Qs = Qs.resample('30min').mean()
    Values.append(Qs.values)
Values = np.array(Values)
E = np.abs(Values - Qo[Qs.index].values)
#E = np.abs(Values[:,-1] - Qo[Qs.index][-1])
#Best = np.argmin(np.nanmean(E,axis = 1))
Best = np.argmin(E)
BestRute = ListSim[Best]
BestH5 = ListH5[Best]
BestRc = args.rc[Best]

print('#################################################')
print('El mejor')
print(BestRc, np.nanmean(E,axis = 1)[Best])
print('#################################################')


##Iterates for all records to compae who is the best
#for l1,l2 in zip(ListSim, ListH5):
#    #Obtaines the number of the run
#    Run = l1.split('_')[1].split('.')[0]
#    #Obtains the data
#    data = am.ASYNCH_results(l1)
#    Qs = data.ASYNCH_dat2Serie(args.link, args.d1, '15min')
#    Qs = Qs.resample('30min').mean()
#    #Qs.index = Qs.index - pd.Timedelta('12h')
#    Enew,status = ErrorEstimator(Qo[Qs.index], Qs)
#    if Enew < Eold:
#        Eold = Enew
#        Best = Run
#        BestRute = l1
#        BestH5 = l2
#        BestRc = args.rc[int(Run)]
#        print('####################################################################')
#        print('EL mejooooor')
#        print(Run, Eold)
#        print('####################################################################')
#Replace initial conditions
os.system('cp '+BestH5+' '+args.folder+'/ForRun/Initial_'+args.lam+'.h5')
#Cleans the bad initial files.
for l in ListH5:
    os.system('rm '+l)
#Reads the last best simulated data
data = am.ASYNCH_results(BestRute)
Qs = data.ASYNCH_dat2Serie(args.link, args.d1, '15min')
Data = pd.DataFrame(Qs.values, Qs.index, columns=['Qsim',])
Data['RC'] = BestRc
Data['lambda'] = args.lam
#Reads the old best simulated data
if args.first == 'si':
    with open(args.folder+'/Results/Qsim_'+args.lam+'.csv', 'a') as f:
        Data.to_csv(f, header=True)
if args.first == 'no':
    with open(args.folder+'/Results/Qsim_'+args.lam+'.csv', 'a') as f:
        Data[1:].to_csv(f, header=False)
##Erase the .dat files 
for l in ListSim:
    os.system('rm '+l)


