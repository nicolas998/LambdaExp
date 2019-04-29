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
import numpy as np
import glob
from ifis_tools import auxiliar as aux


def WarpFunc(Lista):
    #Updates Global file
    Global = fl.WriteGlobal(Lista[0],Lista[1],
        Lista[2],Lista[3],Lista[4],
        Lista[5], Lista[6],Lista[7],
        Lista[8], Lista[9], Lista[10]
    )
    #Writes the global file
    f = open(Lista[11], 'w')
    f.write(Global)
    f.close()

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
parser.add_argument("link",help="Link of Iowa to be analyzed ", type = str)
parser.add_argument("-r","--rc",
    nargs='+',
    #default=[0.0, 0.05, 0.1, 0.3,0.6,0.8, 0.9,0.99],
    default=[0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1],
    type=float,
    help="List with the RC values to iterate")
parser.add_argument("-l","--lam",
    nargs = '+',
    default = [0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50],
    type=float,
    help="List with the Lambda values to iterate", )
parser.add_argument("-t","--dt",default='3h', type=str,
    help="The time delta used to test the changes of RC and Lambda in the experiment")
parser.add_argument("-s","--start", default = '0h', 
    help="extra time added at the start of the event")
parser.add_argument("-e","--end", default = '0h', 
    help="extra time added at the end of the event")
parser.add_argument("-g","--globalfile", default='190BaseGlobal.gbl')
parser.add_argument("-u","--umbral", default = 50, type = int, 
    help="threshold to determine the magnitude of the peak values")
args=parser.parse_args()

################################################################################################################
#DEPLOYS FOLDERS
###############################################################################################################
fullPath = 'Links/'+args.link
#fullPath = '/localscratch/Users/nicolas/'+args.link


#Test if there is a folder for that link if not, makes it
fl.Files_makeFolder(fullPath)
#Read the streamflow data and find the peaks.
fl.Files_Read_Qo_Q190(args.link, True, umbral = args.umbral)
#ASk for the event to be evaluated
numEvent = input('Put the number of the event to eval: \n')
numEvent = int(numEvent)
fl.Evento.numEvent = numEvent
fl.Evento.dateStartEvent = fl.Evento.pos1[numEvent] - pd.Timedelta(args.start)
fl.Evento.dateEndEvent = fl.Evento.pos2[numEvent] + pd.Timedelta(args.end)
#Create the folder for the selected event
dateText = fl.Evento.dateStartEvent.strftime('%Y%m%d-%H%M')
dateShort = fl.Evento.dateStartEvent.strftime('%Y%m%d')
fl.Evento.path = fullPath+'/'+dateText

fl.Evento.SetTemplate(args.globalfile)
fl.Files_makeFolder(fl.Evento.path)
fl.Files_makeFolder(fl.Evento.path+'/Initial')
fl.Files_makeFolder(fl.Evento.path+'/ForRun')
fl.Files_makeFolder(fl.Evento.path+'/Results')
fl.WriteControlSav(fl.Evento.path+'/ForRun/control.sav', args.link)


################################################################################################################
#CREATES FILES FOR RUN
###############################################################################################################
#Creates the dates for the execution
Dates = pd.date_range(
    fl.Evento.dateStartEvent,
    fl.Evento.dateEndEvent,
    freq = args.dt)
#Creates the initial file of the dbc in order to avoid multiprocessing errror
d_initial = Dates[0].strftime('%Y-%m-%d %H:%M')
fl.Evento.CreateInitialDBC(
        fl.Evento.path+'/ForRun/initial.dbc',
        fl.Evento.path+'/ForRun/',
        fl.Evento.path+'/Results/',
        'noname',
        d_initial,
        args.link)

################################################################################################################
#CREATES THE GLOBAL FILES FOR THE DIFFERENT LAMBDAS
###############################################################################################################
#Iterate trough lambdas
for lam in args.lam:

    #Get the name of the lambda parameter used
    lamb = str(lam)
    lambdaName = lamb.replace('.','')
    #Starts to write the bash file for the overall exec
    fl.Evento.SetupBashHeader('N'+dateShort+'_'+lambdaName)
    fl.Evento.CreateBashFile(status = 'start',
        path ='./Run_'+dateText+'_'+lambdaName+'.sh')

    #First initial condition 
    Initial = fl.Evento.path+'/ForRun/initial.dbc'
    initFlag = '3'

    #Creates the gbl files for each epoc
    first = 'si'
    for d1, d2 in zip(Dates[:-1], Dates[1:]):
        #Dates in string format
        d_initial = d1.strftime('%Y-%m-%d %H:%M')
        d_end = d2.strftime('%Y-%m-%d %H:%M')
        #Creates the list for execution
        unix1 = str(aux.__datetime2unix__(d_initial))#+12*3600)
        unix2 = str(aux.__datetime2unix__(d_end))#+12*3600)
        #Iterates 
        Lista = []
        for c,rc in enumerate(args.rc):
            #Name of the project
            name = d1.strftime('%Y%m%d%H%M')+'_'+str(c)+'_'+lambdaName
            #Parameters
            params = '6 0.75 %s -0.2 %s 0.1 2.2917e-05' % (lamb, str(rc))
            #List for that run
            L = [d_initial, d_end, params, args.link, initFlag,
                Initial, unix1, unix2,
                fl.Evento.path+'/Results/'+name+'.dat',
                fl.Evento.path+'/ForRun/control.sav',
                fl.Evento.path+'/Initial/'+name+'.h5', 
                fl.Evento.path+'/ForRun/'+name+'.gbl'
                ]
            #Updates the list 
            Lista.append(L)
            #If it is the last comand of that epoc dont put the upersand
            if c == len(args.rc)-1:
                #Updates exec file 
                fl.Evento.CreateBashFile(name, status = 'update', last = True)
            else:
                fl.Evento.CreateBashFile(name, status = 'update')
        #Creates the gbl files for that date
        p = Pool(processes = len(args.rc))
        p.map(WarpFunc, Lista)
        p.close()
        p.join()
        #Changes the initial 
        Initial = fl.Evento.path+'/ForRun/Initial_'+lambdaName+'.h5'
        initFlag = '4'
        #Closes one epoc at the exec file
        fl.Evento.CreateBashFile(status = 'cepoc',
            linkID = args.link,
            nprocess = np.floor(56/len(args.lam)),
            d1 = d1.strftime('%Y-%m-%d-%H%M'),
            d2 = d2.strftime('%Y-%m-%d-%H%M'),
            rcs = args.rc,
            lam = lambdaName,
            first = first)
        first = 'no'
        print('Write gbl files for '+d1.strftime('%Y%m%d%H%M'))
    print('Global files has been created for lambda '+lambdaName)
    print('########################################################')
    #Closes the bash file for execution 
    name = args.link+'_'+lambdaName+'_'+Dates[0].strftime('%Y%m%d%H%M')+'.csv'
    fl.Evento.CreateBashFile(status = 'close', name = name, lam = lambdaName)




