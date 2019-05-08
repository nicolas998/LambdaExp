import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_table
import glob
from ifis_tools import database_tools as db
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import hydroeval as heval 

##############################################################################################
#List the links 
Results = glob.glob('Results/*')
Links = np.unique(np.array([int(i.split('_')[0].split('/')[1]) for i in Results])).tolist()

#Conver them into a list of dictionaries
LinkOptions = []
for i in Links:
    LinkOptions.append({'label':str(i), 'value':i})
EventosOptions = []
#Loads the basic information of the links
LinksData = pd.read_msgpack('LinkData.msg')
#List with the oprtions to select event by different indicators 
objetive_functions = ['Lower Qpeak difference', 
    'Lower timming at the Qpeak',
    'Best KG']

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

##############################################################################################
# Show on the web
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    
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
    L = glob.glob('Results/'+str(input_value)+'*')
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
        )

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

    
    

##############################################################################################
#Run the code
if __name__ == '__main__':
    app.run_server(debug=True,
        port = '8887',
        host = '127.0.0.1'
        )
