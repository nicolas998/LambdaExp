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
args=parser.parse_args()

################################################################################################################
#DEPLOYS FOLDERS
###############################################################################################################
fullPath = 'Links/'+args.link

#Test if there is a folder for that link if not, makes it
fl.Files_makeFolder(fullPath)
#Read the streamflow data and find the peaks.
fl.Files_Read_Qo_Q190(args.link, True)
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
def WarpFunc(Lista): 
    #Write the project
    fl.Evento.Setups_Write(
        fl.Evento.path+'/ForRun/',
        fl.Evento.path+'/Results/',
        Lista[0],
        d_initial,
        d_end,
        args.link,
        str(args.lam), Lista[1],
        path2gbl = fl.Evento.path+'/ForRun/',
        Initial = Initial,
        Snapshots = fl.Evento.path+'/Initial/'+Lista[0]+'.h5'
    )

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
for d1, d2 in zip(Dates[:-1], Dates[1:]):
    #Dates in string format
    d_initial = d1.strftime('%Y-%m-%d %H:%M')
    #d2t = d2 - pd.Timedelta('1min')
    d_end = d2.strftime('%Y-%m-%d %H:%M')
    #Creates the list for execution
    Lista = []
    for c,rc in enumerate(args.rc):
        #Name of the project
        name = d1.strftime('%Y%m%d%H%M')+'_'+str(c)
        Lista.append([name,str(rc),c]) 
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
    #Closes one epoc at the exec file
    fl.Evento.CreateBashFile(status = 'cepoc',
        linkID = args.link, 
        d1 = d1.strftime('%Y-%m-%d-%H%M'),
        d2 = d2.strftime('%Y-%m-%d-%H%M'),
        rcs = args.rc,
        lam = str(args.lam))
    print('Write gbl files for '+d1.strftime('%Y%m%d%H%M'))
print('Global files has been created')
#Closes the bash file for execution 
fl.Evento.CreateBashFile(status = 'close')

#Writes python file that updates Streamflows and conditions.

