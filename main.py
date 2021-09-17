import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash(__name__)

app.layout = html.Div(children=[html.H1('Dash Tutorials'),
                                dcc.Graph(id='example',
                                          figure={
                                              'data': [{'x': [1, 2, 3, 4, 5], 'y': [5, 6, 7, 2, 1], 'type': 'line',
                                                        'name': 'ex1'},
                                                       {'x': [1, 2, 3, 4, 5], 'y': [8, 9, 6, 5, 1], 'type': 'bar',
                                                        'name': 'ex2'}],
                                              'layout': {
                                                  'title': 'Basic Dash Plot'
                                              }
                                          })
                                ])

if __name__ == '__main__':
    app.run_server(host='localhost', debug=True)
