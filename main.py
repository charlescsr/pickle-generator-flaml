import base64
import io
import os

import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash import dash_table
from flask import Flask, send_file
from flaml import AutoML
import pickle
import hashlib
from sklearn.model_selection import train_test_split 

import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

server = Flask(__name__)
app = dash.Dash(server=server, external_stylesheets=external_stylesheets)
ID = os.environ.get('ID')

app.config['suppress_callback_exceptions'] = True

@server.route("/download_pkl/<id>")
def download(id):
    """Serve the pickle file"""
    passwd = hashlib.sha256(ID.encode()).hexdigest()
    if id == passwd:
        return send_file("model.pickle", as_attachment=True)

app.layout = html.Div([
    html.H1(children='Pickle File generator using AutoML', style={'text-align': 'center'}), html.Br(),
    html.H3(children='Upload your dataset and select target and training set size and you get your pickle file', style={'text-align': 'center'}),

    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')
        ]),
        style={
            'width': '99%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'solid',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
    ),
    html.Div(id='output-data-upload'),
    html.Div(id='output-model')
])


def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            
            if any(df.columns.str.contains('^Unnamed')):
                df = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')), index_col=0)

        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename), 

        dash_table.DataTable(
            data=df.head().to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns], id='dataset',
        ),
        html.Div(id='secret-df', hidden=True, children=df.to_json(orient='split')),

        html.Hr(),  # horizontal line
        html.Label('Algorithm to perform'),
        dcc.Dropdown(
            id='algorithm',
            options=[
                {'label': 'Regression', 'value': 'regression'},
                {'label': 'Classification', 'value': 'classification'}
            ],
            clearable=False,
        ),
        html.Hr(),  # horizontal line
        html.Label('Target column'),
        dcc.Dropdown(
        id='target',
        options=[
            {'label': i, 'value': i} for i in df.columns
        ],
        clearable=False,
        ),
        html.Hr(),  # horizontal line
        html.Label('Select size of training set'),
        dcc.Slider(
            id='training-set-size',
            min=5,
            max=100,
            step=None,
            marks={
                5: {'label': '5 %', 'style': {'color': '#77b0b'}},
                25: {'label': '25 %', 'style': {'color': '#28fad3'}},
                50: {'label': '50 %', 'style': {'color': '#46fa28'}},
                75: {'label': '75 % ', 'style': {'color': '#f6fa28'}},
                100: {'label': '100 %', 'style': {'color': '#f50'}},
            }
        )
    ], id='train-div')


@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'))
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        children = [parse_contents(list_of_contents, list_of_names)]
        return children

@app.callback(Output('output-model', 'children'),
                Input('target', 'value'), Input('training-set-size', 'value'),
                Input('algorithm', 'value'), 
                Input('secret-df', 'children'))
def return_pickle_file(target, training_set_size, algorithm, dataset):
    if training_set_size is not None:
        df = pd.read_json(dataset, orient='split')

        X = df.drop([target], axis=1)
        y = df[target]

        test_size = 1 - training_set_size / 100

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
        automl = AutoML()
        automl_settings = {
            "time_budget": 20,
            "metric": 'accuracy',
            "task": algorithm,
            "log_file_name": './train_log.log',
        }
        automl.fit(X_train, y_train, **automl_settings)
        
        with open("model.pickle", 'wb') as model:
            pickle.dump(automl, model, pickle.HIGHEST_PROTOCOL)

        return html.Div([
            html.Hr(),
            html.H5('Here is your pickle file...'),
            html.A("Model File", href="/download_pkl/"+ str(hashlib.sha256(ID.encode()).hexdigest()))
        ], id='model_file')

if __name__ == '__main__':
    app.run_server()