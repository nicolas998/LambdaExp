#!/usr/bin/env python

################################################################################################################
#PAKAGES IMPORT
################################################################################################################
# Import packages 

import datetime as dt 
import hydroeval as heval
import json
import argparse
import glob
import textwrap
import pandas as pd 
import numpy as np 

################################################################################################################
#PARAMETERS PARSE
################################################################################################################
#Parametros de entrada del trazador

parser=argparse.ArgumentParser(
    prog='linkEventSummary',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description=textwrap.dedent('''\
            Generates a json with the summary of the events for a link'''))
#Parametros obligatorios
################################################################################################################
#CODE STARTS
parser.add_argument("link",help="Link of Iowa to be analyzed ", type = str)
args=parser.parse_args()


################################################################################################################
#Run
###############################################################################################################

ListRes = glob.glob('Results/'+args.link+'*')
ListRes.sort()
#Function to convert
def String2Date(l):
    return pd.Timestamp(dt.datetime.strptime(l.split('_')[-1].split('.')[0], '%Y%m%d%H%M'))
#Fechas
Tstamps = np.unique(np.array(list(map(String2Date, ListRes))))
#Function to convert again to text
def Date2Str(l):
    return l.to_pydatetime().strftime('%Y%m%d%H%M')
#String dates
Events = list(map(Date2Str, Tstamps))

Qobs = pd.read_msgpack('BaseData/USGS/'+args.link+'.msg')

BigPerf = {}

for Event in Events:

    Qsim = {}
    Performance = {'qpeak': {}, 'time': {}, 'kg':{}}
    for lambdas in ['005','01','015','02','025']:
        try:
            #Read the data
            path = 'Results/'+args.link+'_'+lambdas+'_'+str(Event)+'.csv'
            Qs = pd.read_csv(path, index_col = 0, skiprows=0, parse_dates=True)
            Qsim.update({lambdas : Qs['Qsim'].resample('30min').mean()})
            Qo = Qobs[Qs.resample('30min').mean().index]
            #Obtains best lambda in terms of the peak mag and timming
            Performance['qpeak'].update({lambdas: np.abs(Qs['Qsim'].max() - Qo.max())})
            Td = Qs['Qsim'].idxmax() - Qo.idxmax()
            Performance['time'].update({lambdas: np.abs(Td.total_seconds()) / 3600.})
            pos = np.where((np.isfinite(Qsim[lambdas].values)) & (np.isfinite(Qo.values)))[0]
            Performance['kg'].update({lambdas: heval.evaluator(heval.kge, Qsim[lambdas].values[pos], Qo.values[pos])[0][0]})
        except:
            Performance['qpeak'].update({lambdas: np.nan})
            Performance['time'].update({lambdas: np.nan})
            Performance['kg'].update({lambdas: np.nan})
    
    BigPerf.update({str(Event): Performance})

#Saves the json of that link
j = json.dumps(BigPerf)
f = open("Summary/"+args.link+'_summary.json',"w")
f.write(j)
f.close()