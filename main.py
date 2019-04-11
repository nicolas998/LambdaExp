#!/usr/bin/env python

################################################################################################################
#PAKAGES IMPORT
################################################################################################################
# Import packages 
import argparse
import textwrap
import files as fl
import pandas as pd
from multiprocessing import Pool
import os
import glob

################################################################################################################
#PARAMETERS PARSE
################################################################################################################
#Parametros de entrada del trazador

parser=argparse.ArgumentParser(
    prog='Actualiza_Caudales_Hist',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description=textwrap.dedent('''\
            Make the overall analysis of lamda'''))
#Parametros obligatorios
################################################################################################################
#CODE STARTS
parser.add_argument("link",help="Link of Iowa to be analyzed ")
parser.add_argument("-r","--rc",
    nargs='+',
    default=[0.0, 0.05, 0.1, 0.3,0.6,0.8, 0.9,0.99],
    type=float,
    help="List with the RC values to iterate")
parser.add_argument("-l","--lam",
    nargs='+',
    default=[0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5],
    type=float,
    help="List with the Lambda values to iterate", )
parser.add_argument("-t","--dt",default='3h', type=str,
    help="The time delta used to test the changes of RC and Lambda in the experiment")
parser.add_argument("-u","--umbral", default = 50, type = int,
    help="The treshold of the percentile to determine the magnitude of the evaluated events.")
args=parser.parse_args()

################################################################################################################
#DEPLOYS FOLDERS
###############################################################################################################
fullPath = 'Links/'+args.link

#Test if there is a folder for that link if not, makes it
fl.Files_makeFolder(fullPath)
#Read the streamflow data and find the peaks.
fl.Files_Read_Qo_Q190(args.link, True, args.umbral)
#ASk for the event to be evaluated









#numEvent = input('Put the number of the event to eval: \n')
#numEvent = int(numEvent)
#fl.Evento.numEvent = numEvent
#fl.Evento.dateEvent = fl.Evento.pos1[numEvent]
##Create the folder for the selected event
#dateText = fl.Evento.dateEvent.strftime('%Y%m%d-%H%M')
#fl.Evento.path = fullPath+'/'+dateText
#fl.Files_makeFolder(fl.Evento.path)
#fl.Files_makeFolder(fl.Evento.path+'/Initial')
#fl.Files_makeFolder(fl.Evento.path+'/ForRun')
#fl.Files_makeFolder(fl.Evento.path+'/Results')
#fl.Files_makeFolder(fl.Evento.path+'/Trash')
#
#
#################################################################################################################
##CREATES FIRST TIME RUN FILES (ForRun)
################################################################################################################
#
##Creates the dictionary with the events
#fl.Evento.Setups_Create(args.rc, args.lam)
##Initial and end date of the event
#d_initial = fl.Evento.dateEvent.strftime('%Y-%m-%d %H:%M')
#d_end = fl.Evento.dateEvent + pd.Timedelta(args.dt)
#d_end = d_end.strftime('%Y-%m-%d %H:%M')
##Creates the initial file of the dbc in order to avoid multiprocessing errror
#fl.Evento.CreateInitialDBC(
#        fl.Evento.path+'/ForRun/initial.dbc',
#        fl.Evento.path+'/ForRun/',
#        fl.Evento.path+'/Results/',
#        'noname',
#        d_initial,
#        d_end,
#        args.link)
##Warp function to write the files
#def Warp(L):
#    fl.Evento.Setups_Write(
#        fl.Evento.path+'/ForRun/',
#        fl.Evento.path+'/Results/',
#        L[0],
#        d_initial,
#        d_end,
#        args.link,
#        L[1],L[2],
#        path2gbl = fl.Evento.path+'/ForRun/',
#        Initial = fl.Evento.path+'/ForRun/initial.dbc',
#        Snapshots = fl.Evento.path+'/Initial/'+L[0]+'.h5'
#    )
##Writes the setups for the project
#ListFiles = []
#ListQsub = []
#SetsStates = {}
#for k in fl.Evento.setups.keys():
#    ListFiles.append([k, str(fl.Evento.setups[k][0]), str(fl.Evento.setups[k][1])])
#    ListQsub.append('qsub '+fl.Evento.path+'/ForRun/'+k+'.sh')
#    SetsStates.update({k:{'run':False, 'name':''}})
#print('Writing run files at: '+ fl.Evento.path+'/ForRun/')
#p = Pool(processes=8)
#p.map(Warp, ListFiles)
#p.close()
#p.join()
#print('Files for runing async 190 created at: '+fl.Evento.path+'/ForRun/')
#
#################################################################################################################
##RUN THE MODEL
#################################################################################################################
#
#pathParam = fl.Evento.path+'/Results/BestParam.txt'
#Best = 'Set_3'
#cont = 1
#initial_old = '3 '+fl.Evento.path + '/ForRun/initial.dbc'
#
## Creates the initial document to records the best lambdas and rcs
#fl.WriteBestLambdaRC(pathParam,True)
#for i in range(15):
#    # Send the first exec to qsub jobs to hpc
#    fl.Evento.execute(fl.events.WarpQsub, ListQsub)
#    # Check end of runing.
#    #fl.CheckRun(SetsStates, d_end)
#    fl.Evento.CheckEpochEnd()
#    #Update the end date of the run
#    d_end = fl.Evento.dateEvent + pd.Timedelta(args.dt)
#    d_end = d_end.strftime('%Y-%m-%d %H:%M')
#    #Select the best for initial conditions of the next gen. 
#
#    # Save the simulated streamflow for that dt
#    pathIn = fl.Evento.path+'/Results/'+Best+'.dat'
#    pathOut = fl.Evento.path+'/Results/QBestSim'+str(cont)+'.dat'
#    fl.CopyBestStream(pathIn, pathOut)
#    # Save the value of lambda and RC for the dt
#    lamb = fl.Evento.setups[Best][0]
#    rc = fl.Evento.setups[Best][1]
#    fl.WriteBestLambdaRC(pathParam,
#        first = False,
#        date = d_end,
#        lamb = lamb,
#        rc = rc)
#    # Erase old h5 files and copy the good one
#    fl.Evento.ClearInitial(Best)
#    # Update dates and path to initial file 
#    initial_new = '4 '+fl.Evento.path+'/ForRun/'+Best+'.h5' 
#    fl.Evento.UpdateGlobals(args.dt, initial_old, initial_new)
#    # Run next generation
#    cont+=1
#    initial_old = initial_new
#    # Avisa como va 
#    print('End of ...'+d_end)
#    #os.system('rm rSet_*')

