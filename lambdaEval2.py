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
    default = 0.1,
    type=str,
    help="List with the Lambda values to iterate", )
parser.add_argument("-t","--dt",default='3h', type=str,
    help="The time delta used to test the changes of RC and Lambda in the experiment")
parser.add_argument("-g","--globalfile", default='190BaseGlobal.gbl')
parser.add_argument("-u","--umbral", default = 50, type = int, 
    help="threshold to determine the magnitude of the peak values")
args=parser.parse_args()

################################################################################################################
#DEPLOYS FOLDERS
###############################################################################################################
fullPath = 'Links/'+args.link

#Test if there is a folder for that link if not, makes it
fl.Files_makeFolder(fullPath)
#Read the streamflow data and find the peaks.
fl.Files_Read_Qo_Q190(args.link, True, umbral = args.umbral)
#ASk for the event to be evaluated
numEvent = input('Put the number of the event to eval: \n')
numEvent = int(numEvent)
fl.Evento.numEvent = numEvent
fl.Evento.dateStartEvent = fl.Evento.pos1[numEvent]
fl.Evento.dateEndEvent = fl.Evento.pos2[numEvent]
#Create the folder for the selected event
dateText = fl.Evento.dateStartEvent.strftime('%Y%m%d-%H%M')
fl.Evento.path = fullPath+'/'+dateText
fl.Evento.SetupBashHeader()
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
#First initial condition 
Initial = fl.Evento.path+'/ForRun/initial.dbc'
initFlag = '3'
#Creates the initial file of the dbc in order to avoid multiprocessing errror
d_initial = Dates[0].strftime('%Y-%m-%d %H:%M')
fl.Evento.CreateInitialDBC(
        fl.Evento.path+'/ForRun/initial.dbc',
        fl.Evento.path+'/ForRun/',
        fl.Evento.path+'/Results/',
        'noname',
        d_initial,
        args.link)

#Starts to write the bash file for the overall exec
fl.Evento.CreateBashFile(status = 'start', path = './Run_'+dateText+'.sh')

#Creates the gbl files for each epoc
first = 'si'
for d1, d2 in zip(Dates[:-1], Dates[1:]):
    #Dates in string format
    d_initial = d1.strftime('%Y-%m-%d %H:%M')
    d_end = d2.strftime('%Y-%m-%d %H:%M')
    #Creates the list for execution
    unix1 = str(aux.__datetime2unix__(d_initial)+12*3600)
    unix2 = str(aux.__datetime2unix__(d_end)+12*3600)
    #Iterates 
    Lista = []
    for c,rc in enumerate(args.rc):
        #Name of the project
        name = d1.strftime('%Y%m%d%H%M')+'_'+str(c)
        #Parameters
        params = '6 0.75 %s -0.2 %s 0.1 2.2917e-05' % (args.lam, str(rc))
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
    Initial = fl.Evento.path+'/ForRun/Initial.h5'
    initFlag = '4'
    #Closes one epoc at the exec file
    fl.Evento.CreateBashFile(status = 'cepoc',
        linkID = args.link, 
        d1 = d1.strftime('%Y-%m-%d-%H%M'),
        d2 = d2.strftime('%Y-%m-%d-%H%M'),
        rcs = args.rc,
        lam = str(args.lam),
        first = first)
    first = 'no'
    print('Write gbl files for '+d1.strftime('%Y%m%d%H%M'))
print('Global files has been created')
#Closes the bash file for execution 
name = args.link+'_'+args.lam+'_'+Dates[0].strftime('%Y%m%d%H%M')+'.csv'
fl.Evento.CreateBashFile(status = 'close', name = name)

#Writes python file that updates Streamflows and conditions.


