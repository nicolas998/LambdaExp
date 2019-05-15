import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import glob
from ifis_tools import database_tools as db
import numpy as np
import pandas as pd
import json
import os
import plotly.graph_objs as go
import hydroeval as heval 

##############################################################################################
#Auxiliary functions

def FindBestLambda():  
    #Void list with best
    ListBest = {'kg':[],'qpeak':[],'time':[]}
    ValBest = {'kg':[],'qpeak':[],'time':[]}
    
    Areas = []
    LinksAreas = pd.read_msgpack('LinksAreas.msg')
    
    #Reads the list of evaluated lambdas
    L = glob.glob('Summary/*.json')
    
    for l in L:
        
        #Get link name
        link = l.split('_')[0].split('/')[1]
        
        #Get the area o the link
        Areas.append(LinksAreas[link])
        
        #Read the json file 
        f = open(l,"r")
        D1 = json.load(f)
        f.close()
        
        #Convert that lambda into a pandas thing        
        for key,minmax in zip(['kg','qpeak','time'],['max','min','min']):
            C, Mv, D = ObtainBest(key, D1, minmax)
            ListBest[key].append(C)
            ValBest[key].append(Mv)
    for k in ['kg','qpeak','time']:
        ListBest[k] = np.array(ListBest[k])
        ValBest[k] = np.array(ValBest[k])
    return ListBest, ValBest, np.array(Areas)


def ObtainBest(key, D1, MaxMin = 'min'):
    #Obtains the dictionary in function of the objective function
    D = {}
    for k in D1.keys():
        D.update({k:D1[k][key]})
    D = pd.DataFrame.from_dict(D).T

    #Obtain the best lambda for each case and the corresponding value
    if MaxMin == 'min':
        Lambda = D.idxmin(axis = 1).values
        Value = D.min(axis = 1).values
    elif MaxMin == 'max':
        Lambda = D.idxmax(axis = 1).values
        Value = D.max(axis = 1).values

    Count = []
    MeanValue = []
    for l in ['005','01','015','02','025']:
        Count.append(Lambda[Lambda == l].size)
        MeanValue.append(np.median(Value[Lambda == l]))
    return Count, MeanValue, D


##############################################################################################
#List the links 
usgs = db.SQL_USGS_at_IFIS()
Results = glob.glob('Results/*')
Links = np.unique(np.array([int(i.split('_')[0].split('/')[1]) for i in Results])).tolist()

#Conver them into a list of dictionaries
LinkOptions = []
for i in Links:
    for k in usgs.keys():
        if usgs[k] == i:
            us = k
    LinkOptions.append({'label':'USGS: %s, link: %d' % (us,i), 'value':i})
EventosOptions = []
#Loads the basic information of the links
LinksData = pd.read_msgpack('LinkData.msg')
#List with the oprtions to select event by different indicators 
objetive_functions = ['Lower Qpeak difference', 
    'Lower timming at the Qpeak',
    'Best KG']

obj_func = [['Lower Qpeak difference','qpeak'], 
    ['Lower timming at the Qpeak','time'],
    ['Best KG','kg']]

Performance = {'QpDiff': {}, 'TpDiff': {}, 'Kling-Gupta': {}}
for k in Performance.keys():
    for lambdas in ['005','01','015','02','025']:
        Performance[k].update({lambdas: 0})
Performance = pd.DataFrame.from_dict(Performance)
columns = [{"name":"Lambda1", "id": "Lambda1"}]
columns.extend([{"name": i, "id": i} for i in Performance.columns])
Performance = Performance.round(2).to_dict('records', )
for c,k in enumerate(['005','01','015','02','025']):
    Performance[c].update({'Lambda1':k})
# General performance vectors
Lb,Vb, Areas = FindBestLambda()

##############################################################################################
# Show on the web
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
    dcc.Markdown('''# General results'''),
    
    #Event plot
    html.Div([
        html.Label('General Bars'),
        dcc.Dropdown(
            id='general-ofunc',
            options = [{'label': i[0], 'value': i[1]} for i in obj_func],
            value='qpeak'
        ),
        dcc.Graph(
            id = 'general_bars',
        ),
    ],
    style={'width': '70%', 'display': 'inline-block'}),
    
    html.Div([
        html.Br(),
        dcc.Dropdown(
            id='general-ofunc2',
            options = [{'label': i[0], 'value': i[1]} for i in obj_func],
            value='qpeak'
        ),
        dcc.Graph(
            id = 'overall_bars',
        ),
    ],
    style={'width': '27%','float': 'right', 'display': 'inline-block'}),
    
    dcc.Markdown('''---'''),
    
    dcc.Markdown('''# Link analyzer'''),
    
    #Link description
    html.Div(id = 'my-div',
        style={'textAlign': 'left'}
    ),
    
    #Select link options
    html.Div([
        html.Label('Select Link to plot'),
        dcc.Dropdown(
            id='link-select',
            options = LinkOptions,
            value='226574'
        )
    ],
    style={'width': '48%', 'display': 'inline-block'}),
    
    html.Div([
        #Select date options
        html.Label('Select the date to plot'),
        dcc.Dropdown(
            id='event-select',
            value = '201609230500'
        )
    ],
    style={'width': '48%','float': 'right', 'display': 'inline-block'}),
    
    html.Div([

        #Select objetive function
        html.Label('Objective funtion to select best lambda 1'),
        dcc.Dropdown(
            id='objetive-function',
            options=[{'label': i, 'value': i} for i in objetive_functions],
            value='Lower Qpeak difference'
        ),

        #Event plot
        dcc.Graph(
            id = 'event-plot',
        )
    ],
    style={'width': '70%', 'display': 'inline-block'}),
    
    html.Div([
        html.Label('Summary event table'),
        dash_table.DataTable(
            id='table',
            columns = columns,
            data=Performance,
            row_selectable=False,
            style_as_list_view=True,
            style_cell={'padding': '5px'},
            style_header={
                'backgroundColor': 'white',
                'fontWeight': 'bold'
            },
        ),
                
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),        
        dcc.Markdown('''---'''),
        
        #Select objetive function
        html.Label('Obj func 1 for hist2d'),
        dcc.Dropdown(
            id='obj-func-hist1',
            options=[{'label': i[0], 'value': i[1]} for i in obj_func],
            value='time'
        ),
               
        #Select objetive function
        html.Label('Obj func 2 for hist2d'),
        dcc.Dropdown(
            id='obj-func-hist2',
            options=[{'label': i[0], 'value': i[1]} for i in obj_func],
            value='qpeak'
        ),
    ],
    style={'width': '28%','float': 'right', 'display': 'inline-block'}),
    
    html.Div([
        #Event plot
        dcc.Graph(
            id = 'bars-plot',
        )
    ], 
    style = {'width': '66%', 'display': 'inline-block'}),
    
    
    html.Div([
        
        dcc.Graph(
            id = 'hist2d'
        )
    ],
    style={'width': '28%','float': 'right', 'display': 'inline-block'}),
    
], style={'columnCount': 1})




##############################################################################################
#FUNCTIONS
# Function to show the 
@app.callback(
    Output(component_id = 'event-select', component_property = 'options'),
    [Input(component_id = 'link-select', component_property = 'value')]
)
def ListEventsOfLink(input_value):
    #Obtains the list of events
    L = glob.glob('Results/'+str(input_value)+'*.csv')
    Eventos = np.array([int(i.split('_')[2].split('.')[0]) for i in L])
    EventosUnicos = np.unique(Eventos).tolist()
    #Generates the list of options
    Options = []
    for i in EventosUnicos:
        Options.append({'label':str(i), 'value':str(i)})
    #Return the options
    return Options

@app.callback(
    Output(component_id = 'my-div', component_property = 'children'),
    [Input(component_id = 'link-select', component_property = 'value')]
)
def Show(input_value):
    #Obtains data from the link
    Area = LinksData['Area'][LinksData['Link'] == int(input_value)].values[0]
    USGSID = LinksData.index[LinksData['Link'] == int(input_value)].values[0]
    texto1 = ' USGS station: %s, ' % USGSID
    texto2 = 'Area: %.1f' % Area
    return texto1 + texto2

@app.callback(
    Output(component_id = 'event-plot', component_property = 'figure'),
    [Input(component_id = 'link-select', component_property = 'value'),
    Input(component_id = 'event-select', component_property = 'value'),
    Input(component_id = 'objetive-function', component_property = 'value')]
)
def Plot_event(link, Event, obj_func):
    #Read the observed data   
    Qo = pd.read_msgpack('BaseData/USGS/'+str(link)+'.msg')

    Qsim = {}
    Performance = {'qpeak': {}, 'time': {}, 'kg':{}}
    for lambdas in ['005','01','015','02','025']:
        #try:
        #Read the data
        path = 'Results/'+str(link)+'_'+lambdas+'_'+str(Event)+'.csv'
        Qs = pd.read_csv(path, index_col = 0, skiprows=0, parse_dates=True)
        Qsim.update({lambdas : Qs['Qsim'].resample('30min').mean()})
        Qo = Qo[Qs.resample('30min').mean().index]
        #Obtains best lambda in terms of the peak mag and timming
        Performance['qpeak'].update({lambdas: np.abs(Qs['Qsim'].max() - Qo.max())})
        Td = Qs['Qsim'].idxmax() - Qo.idxmax()
        Performance['time'].update({lambdas: np.abs(Td.total_seconds()) / 3600.})
        pos = np.where((np.isfinite(Qsim[lambdas].values)) & (np.isfinite(Qo.values)))[0]
        Performance['kg'].update({lambdas: heval.evaluator(heval.kge, Qsim[lambdas].values[pos], Qo.values[pos])[0][0]})
        #except:
        #    pass
    Performance = pd.DataFrame.from_dict(Performance)

    #Select wich to plot in function of the objetive 
    if obj_func == 'Lower Qpeak difference':
        Best = Performance['qpeak'].idxmin()
    elif obj_func == 'Lower timming at the Qpeak':
        Best = Performance['time'].idxmin()
    elif obj_func == 'Best KG':
        Best = Performance['kg'].idxmax()
    #Plot the events
    data = []
    for k in ['005','01','015','02','025']:
        if k != Best:
            trace = go.Scatter(
                x = Qsim[k].index,
                y = Qsim[k].values,
                name = k,
                line = dict(
                    width = 4,
                    color = 'rgb(192,192,192)'
                )
            )
            data.append(trace)

    #Plot the best event
    trace = go.Scatter(
       x = Qsim[Best].index,
       y = Qsim[Best].values,
       name = Best,
       line = dict(
           width = 5,
           color = 'rgb(0,102,204)'
       )
    )
    data.append(trace)

    #Plot the observed data
    trace = go.Scatter(
        x = Qo.index,
        y = Qo.values,
        name = 'Observed',
        mode = 'markers',
        marker = dict(
            color = 'rgb(0,0,0)',
        )
    )
    data.append(trace)

    #The set up of the figure
    layout = dict(
        xaxis = dict(
            title = 'Time [30min]',
            titlefont = dict(
                size = 18
            ),
            tickfont = dict(
                size = 16
            )
        ),
        yaxis = dict(
            title = 'Streamflow [m3s-1]',
            titlefont = dict(
                size = 18
            ),
            tickfont = dict(
                size = 16
            )
        ),
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=20,
            pad=4
        ),
    )

    return {
        'data': data,
        'layout': layout
    }

@app.callback(
    Output(component_id = 'table', component_property = 'data'),
    [Input(component_id = 'link-select', component_property = 'value'),
    Input(component_id = 'event-select', component_property = 'value')]
)
def Update_performance_table(link, Event):
    #Read the observed data   
    Qo = pd.read_msgpack('BaseData/USGS/'+str(link)+'.msg')

    Qsim = {}
    Performance = {'QpDiff': {}, 'TpDiff': {}, 'Kling-Gupta':{}}
    for lambdas in ['005','01','015','02','025']:
        #try:
        #Read the data
        path = 'Results/'+str(link)+'_'+lambdas+'_'+str(Event)+'.csv'
        Qs = pd.read_csv(path, index_col = 0, skiprows=0, parse_dates=True)
        Qsim.update({lambdas : Qs['Qsim'].resample('30min').mean()})
        Qo = Qo[Qs.resample('30min').mean().index]
        #Obtains best lambda in terms of the peak mag and timming
        Performance['QpDiff'].update({lambdas: np.abs(Qs['Qsim'].max() - Qo.max())})
        Td = Qs['Qsim'].idxmax() - Qo.idxmax()
        Performance['TpDiff'].update({lambdas: np.abs(Td.total_seconds()) / 3600.})
        pos = np.where((np.isfinite(Qsim[lambdas].values)) & (np.isfinite(Qo.values)))[0]
        Performance['Kling-Gupta'].update({lambdas: heval.evaluator(heval.kge, Qsim[lambdas].values[pos], Qo.values[pos])[0][0]})
        #except:
        #    pass
    Performance = pd.DataFrame.from_dict(Performance)
    D = Performance.round(2).to_dict('records', )
    for c,k in enumerate(['005','01','015','02','025']):
        D[c].update({'Lambda1':k})
    return D

@app.callback(
    Output(component_id = 'bars-plot', component_property = 'figure'),
    [Input(component_id = 'link-select', component_property = 'value')]
)
def Plot_bars(link):
    
    try:
        #Read the summary data
        f = open("Summary/"+str(link)+"_summary.json","r")
        D1 = json.load(f)
        f.close()
    except:
        os.system('python linkEventSummary.py '+link)
        f = open("Summary/"+str(link)+"_summary.json","r")
        D1 = json.load(f)
        f.close()
    
    #Make the plot
    Count, MeanValue,D = ObtainBest('kg',D1,'max')
    trace1 = go.Bar(
        x = np.arange(5),
        y=Count,
        text = ['P50 = %.2f' % i for i in MeanValue],
        textposition = 'auto',
        textfont=dict(
            size=14,
        ),
        xaxis = 'x1',
        yaxis = 'y1',
        marker=dict(
            color='rgb(192,192,192)',)
    )
    Count, MeanValue,D = ObtainBest('time',D1,'min')
    trace2 = go.Bar(
        x = np.arange(5),
        y=Count,
        text = ['P50 = %.2f' % i for i in MeanValue],
        textposition = 'auto',
        textfont=dict(
            size=14,
        ),
        xaxis = 'x2',
        yaxis = 'y1',
        marker=dict(
            color='rgb(192,192,192)',)
    )
    Count, MeanValue,D = ObtainBest('qpeak',D1,'min')
    trace3 = go.Bar(
        x = np.arange(5),
        y=Count,
        text = ['P50 = %.2f' % i for i in MeanValue],
        textposition = 'auto',
        textfont=dict(
            size=14,
        ),
        xaxis = 'x3',
        yaxis = 'y1',
        marker=dict(
            color='rgb(192,192,192)',)
    )


    data = [trace1, trace2,  trace3]

    layout = go.Layout(    
        xaxis = dict(
            title = 'Lambda 1 from KG',
            titlefont = dict(
                 size = 18
             ),
            tickfont = dict(
                size = 16
            ),
            ticktext=['0.05','0.1','0.15','0.2','0.25'],
            tickvals=np.arange(5),
            domain = [0, 0.3],
        ),
        xaxis2 = dict(
            title = 'Lambda 1 from Time dif',
            titlefont = dict(
                 size = 18
             ),
            tickfont = dict(
                size = 16
            ),
            ticktext=['0.05','0.1','0.15','0.2','0.25'],
            tickvals=np.arange(5),
            domain = [0.33, 0.63],
        ),
        xaxis3 = dict(
            title = 'Lambda 1 from Peak dif',
            titlefont = dict(
                 size = 18
             ),
            tickfont = dict(
                size = 16
            ),
            ticktext=['0.05','0.1','0.15','0.2','0.25'],
            tickvals=np.arange(5),
            domain = [0.66, 1.0],
        ),
        yaxis = dict(
            title = 'Count',
            titlefont = dict(
                 size = 18
             ),
            tickfont = dict(
                size = 16
            ),
        ),
        margin=go.layout.Margin(
                l=50,
                r=50,
                b=100,
                t=20,
                pad=4
        ), 
        showlegend = False
    )
    return {
        'data': data,
        'layout': layout
    }
    
@app.callback(
    Output(component_id = 'hist2d', component_property = 'figure'),
    [Input(component_id = 'link-select', component_property = 'value'),
    Input(component_id = 'obj-func-hist1', component_property = 'value'),
    Input(component_id = 'obj-func-hist2', component_property = 'value')]
)
def Hist2D(link,key1, key2):
        
    f = open("Summary/"+str(link)+"_summary.json","r")
    D1 = json.load(f)
    f.close()
    
    minmax1 = 'min'
    if key1 == 'kg': minmax1 = 'max'
    minmax2 = 'min'
    if key2 == 'kg': minmax2 = 'max'
    
    Count1, MeanValue1, B1 = ObtainBest(key1,D1,minmax1)
    Count2, MeanValue2, B2 = ObtainBest(key2,D1,minmax1)

    if minmax1 == 'min':
        Best1 = B1.idxmin(axis=1).values
    else:
        Best1 = B1.idxmax(axis=1).values
    if minmax2 == 'min':
        Best2 = B2.idxmin(axis=1).values
    else:
        Best2 = B2.idxmax(axis=1).values

    BestN1 = np.zeros(Best1.size)
    BestN2 = np.zeros(Best2.size)
    for c,l in enumerate(['005','01','015','02','025']):
        pos = np.where(Best1 == l)[0]
        BestN1[pos] = c

        pos = np.where(Best2 == l)[0]
        BestN2[pos] = c

    H= np.histogram2d(BestN1, BestN2, bins=np.arange(6))
    
    #Obtains the plot
    trace = go.Heatmap(z=H[0],
         colorscale = 'Viridis'
    )

    data=[trace]

    layout = go.Layout(    
        xaxis = dict(
            title = key2,
            titlefont = dict(
                 size = 18
             ),
            tickfont = dict(
                size = 16
            ),
            ticktext=['0.05','0.1','0.15','0.2','0.25'],
            tickvals=np.arange(5),
        ),
        yaxis = dict(
            title = key1,
            titlefont = dict(
                 size = 18
             ),
            tickfont = dict(
                size = 16
            ),
            ticktext=['0.05','0.1','0.15','0.2','0.25'],
            tickvals=np.arange(5),
        ),
        width = 500, height = 450,
        margin=go.layout.Margin(
            l=70,
            r=50,
            b=70,
            t=30,
            pad=4
        ),
    )
    return {
        'data': data,
        'layout': layout
    }

@app.callback(
    Output(component_id = 'general_bars', component_property = 'figure'),
    [Input(component_id = 'general-ofunc', component_property = 'value')]
)
def GeneralBarPlot(key):
    
    colors = ['rgb(247, 239, 14)','rgb(164, 247, 76)','rgb(0,153,153)','rgb(0,76,153)','rgb(51,0,102)']

    binA = np.linspace(0, 1200, 5)
    
    if key == 'qpeak' or key == 'time':
        PosBest = Lb[key].argmax(axis = 1)
    else:
        PosBest = Lb[key].argmin(axis = 1)
    
    #ValBest = np.array([i[j] for i,j in zip(Vb['kg'], PosBest)])
    Bars = []
    Text = []
    for a,b in zip(binA[:-1], binA[1:]):
        pos = np.where((Areas>=a) & (Areas<b))[0]
        H,bins = np.histogram(PosBest[pos], bins=np.arange(6))
        Bars.append(H)
        Text.append('%d - %d' % (a,b))
    Bars = np.array(Bars)

    data = []
    for h, lam, color in zip(Bars.T, ['0.05','0.1','0.15','0.2','0.25'], colors):

        #Generates the trace
        trace = go.Bar(
            x = Text,
            y = h,
            name = lam,
            marker=dict(
            color=color,
            line=dict(
                color='rgb(8,48,107)',
                width=1.5,
                ),
            ),
        opacity=0.6
        )
        data.append(trace)
    layout = go.Layout(
        barmode='group',
        xaxis = dict(
            title = 'Watershed area range [km^2]',
            titlefont = dict(
                size = 18
            ),
            tickfont = dict(
                size = 16
            )
        ),
        yaxis = dict(
            title = 'Number of cases',
            titlefont = dict(
                size = 18
            ),
            tickfont = dict(
                size = 16
            )
        ),
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=20,
            pad=4
        ),
    )
    return {
        'data': data,
        'layout': layout
    }
    
@app.callback(
    Output(component_id = 'overall_bars', component_property = 'figure'),
    [Input(component_id = 'general-ofunc2', component_property = 'value')]
)
def OverallBarPlot(key):
    
    colors = ['rgb(247, 239, 14)','rgb(164, 247, 76)','rgb(0,153,153)','rgb(0,76,153)','rgb(51,0,102)']
    
    if key == 'qpeak' or key == 'time':
        PosBest = Lb[key].argmax(axis = 1)
    else:
        PosBest = Lb[key].argmin(axis = 1)
    H,bins = np.histogram(PosBest, bins=np.arange(6))
    
    trace = go.Bar(
        x = ['0.05','0.1','0.15','0.2','0.25'],
        y = H,
        marker=dict(
            color=colors,
            line=dict(
                color='rgb(8,48,107)',
                width=1.5,
            ),
        ),
        opacity=0.6
    )
    
    data = [trace]
    
    layout = go.Layout(
        #barmode='group',
        xaxis = dict(
            title = 'Lambda 1',
            titlefont = dict(
                size = 18
            ),
            tickfont = dict(
                size = 16
            )
        ),
        yaxis = dict(
            title = 'Number of cases',
            titlefont = dict(
                size = 18
            ),
            tickfont = dict(
                size = 16
            )
        ),
        margin=go.layout.Margin(
            l=50,
            r=50,
            b=100,
            t=20,
            pad=4
        ),
    )
    
    return {
        'data': data,
        'layout': layout
    }
    
    
##############################################################################################
#Run the code
if __name__ == '__main__':
    app.run_server(debug=True,
        port = '8887',
        host = '127.0.0.1'
        )
