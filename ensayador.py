#!/usr/bin/env python
import time
import os
import glob
import fileinput
from ifis_tools import auxiliar as aux
from ifis_tools import asynch_manager as am
import pandas as pd
from string import Template

#Funtion to read the base global file 
def readFile(path):
    f = open(path, 'r')
    L = f.readlines()
    f.close()
    return L
#Read global file 
GlobalBase = readFile('190BaseGlobal.gbl')


Tem = Template(''.join(GlobalBase))
G = Tem.substitute(
    date1 = 'a',
    date2 = 'a',
    Parameters = '1',
    linkID = 'a',
    initialflag = '0',
    initial = 'path2initial',
    unix1 = 'u1',
    unix2 = 'u2',
    output = 'salida.dat',
    peakflow = 'peaks.sav',
    snapflag = '3',
    snaptime = '',
    snapshot = 'file.h5'
    )


#Idea of a dictionary with the data required for global construction
# 1. Fill the dictionary with the global data.
#D = {}
#for c,l in enumerate(GlobalBase):
#    D.update({str(c): 'line': l,}})
# 2. Stablish a second dictionary with the references to the editable lines 
#R = {
#    'date1': {'line': '4', 'edit': '%s\n'},
#    'date2': {'line': '5', 'edit': '%s\n'},
#    'link': {'line': '27', 'edit': '1 %s /Dedicated/IFC/model_eval/topo51.dbc\n'},
#    'param': {'line': '19', 'edit': '%d %.2f %.2f %.1f %.1f %.1f %s\n'},
#    'initial':{'line':'33', 'edit': '%d %s\n'},
#    'rain':{'line':'40', 'edit': '10 60 %d %d\n'},
#    'evp':{'line':'44', 'edit': '%d %d\n'},
#    'datfile':{'line':'55','edit':'%d %.1f %s\n'},
#    'links2save':{'line':'63','edit':'%d %s\n'},
#    'snapshot':{'line':'67','edit':'3 %s\n'},
#    }
#
#Global = GlobalBase.copy()
#def EditGlobal(param, tuple_text):
#    #Get the line
#    line = int(R[param]['line'])
#    #Get the text 
#    Text = R[param]['edit'] % tuple_text
#    #Update Global 
#    Global[line] = Text






