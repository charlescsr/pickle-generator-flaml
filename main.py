import base64
import io

import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash import dash_table
from dash.html.Label import Label
from flaml import AutoML
from sklearn.model_selection import train_test_split 

import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
automl = AutoML()

app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([
    html.H1(children='ML Using FLAML', style={'text-align': 'center'}), html.Br(),
    html.H3(children='Upload your dataset and select the target', style={'text-align': 'center'}),

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
    html.Div(id='output')
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
                5: '5%',
                25: '25%',
                50: '50%',
                75: '75%',
                100: '100%',
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

@app.callback(Output('output-plot', 'children'),
                Input('target', 'value'), Input('training-set-size', 'value'),
                Input('algorithm', 'value'), 
                Input('secret-df', 'children'))
def return_plot(target, training_set_size, dataset, algorithm):
    if training_set_size is not None:
        df = pd.read_json(dataset, orient='split')

        X = df.drop([target], axis=1)
        y = df[target]

        test_size = 1 - training_set_size / 100

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
        automl_settings = {
            "time_budget": 60,
            "metric": 'accuracy',
            "task": algorithm,
            "log_file_name": 'logs/train_log.log',
        }
        automl.fit(X_train, y_train, **automl_settings)

if __name__ == '__main__':
    app.run_server(debug=True)