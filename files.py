import os
import pandas as pd
from ifis_tools import series_tools as ser
import numpy as np
import evento as events
import glob

Warnings = {
    'FolderExist': 'Warning: The folder already exist, i will not create a new one'
}

Evento = events.Event()

def Files_makeFolder(path):
    if os.path.exists(path) is False:
        os.mkdir(path)
        print('Folder created at: '+path)
    else:
        print(Warnings['FolderExist'])

def Files_Read_Qo_Q190(link, listEvents = False, umbral = 50):
    #Read observed
    Qo = pd.read_msgpack('/Users/nicolas/LambdaExp/BaseData/USGS/'+link+'.msg')
    Qo = Qo.resample('H').mean()
    #Read simulated
    Qs = pd.read_msgpack('/Users/nicolas/LambdaExp/BaseData/HLM190/'+link+'.msg')
    Qs = Qs.resample('H').mean()
    #Find events
    pos1, pos2 = ser.Runoff_FindEvents(Qo, Qs, umbral = umbral)
    #List the events
    if listEvents:
        c = 0
        for p1, p2 in zip(pos1, pos2):
            qp = '%.2f ' % np.nanmax(Qo[p1:p2])
            print(c, qp, p1)
            c+=1
    #Updates the class Evento 
    Evento.Qobs = Qo
    Evento.Qsim = Qs
    Evento.pos1 = pos1
    Evento.pos2 = pos2

def WriteControlSav(path, link):
    f = open(path, 'w')
    f.write('%s\n' % link)
    f.close()

def WriteGlobal(d1str, d2str, params, link, init_flag,
    init_path, unix1, unix2, dat_path, sav_path,
    h5_path, snap_flag = '3', snap_time=''):
    #Edit the global file
    Global = Evento.template.substitute(
        date1 = d1str,
        date2 = d2str,
        Parameters = params,
        linkID = link,
        initialflag = init_flag,
        initial = init_path,
        unix1 = unix1,
        unix2 = unix2,
        output = dat_path,
        peakflow = sav_path,
        snapflag = '3',
        snaptime = '',
        snapshot = h5_path
        )
    return Global

def GetSize(path):
    size = os.path.getsize(path)
    if size > 1000:
        return True
    else:
        return False


def CheckRun(SetsStates, epoch_date):
    flag = True
    while flag:
        #check the end of each job
        flag = False
        for s in SetsStates.keys():
           #Only check sets that didnt run yet
           if SetsStates[s]['run'] is False:
                flag = True
                #Check if the file with the job report was created
                if SetsStates[s]['name'] == '':
                    l = glob.glob('r'+s+'.*')
                    if len(l) > 0:
                        SetsStates[s]['name'] = l[0]
                #Check the size of the file with the report
                if SetsStates[s]['name'] != '':
                    if GetSize(SetsStates[s]['name']):
                        SetsStates[s]['run'] = True
                        os.system('rm '+SetsStates[s]['name'])
    #Return the states to no run.
    for s in SetsStates.keys():
        SetsStates[s]['run'] = False
    print('End of '+epoch_date)

#def CheckRun2(SetsStates, path, epoch_date):
#    flag = True
#    while flag:
#        









def CopyBestStream(path_in, path_out):
    os.system('cp '+path_in+' '+path_out)

def WriteBestLambdaRC(pathParam, first = True, date =None,
    lamb = None, rc = None):
    f = open(pathParam,'a')
    if first:
        f.write('date, lambda, RC\n')
    else:
        f.write('%s, %.2f, %.2f \n' % (date, lamb, rc))

