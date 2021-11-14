import dash
from dash import html
from dash import dcc
from datetime import datetime as dt
from datetime import date, timedelta
from dash.dcc import Input
from dash.development.base_component import Component
from dash.dependencies import Input,Output,State
from dash.exceptions import PreventUpdate
import yfinance as yt
import plotly.graph_objs as go
import plotly.express as px
import lxml
from model import train_model
from sklearn.model_selection import train_test_split

# data = None
app = dash.Dash(__name__)
server = app.server

"""*********************************************************************************************************"""
"""--------------------------------------------------DESIGN LAYOUT------------------------------------------"""
"""*********************************************************************************************************"""

item1 = html.Div(
          [
            html.P("Welcome to the Stock Dash App!", className="start",style={"color":"white"}),
            html.Div([
              # stock code input
              html.P("Input stock code:",style={"align-items" : "center","color":"white"}),
              dcc.Input(id = "stock_input_field"),
              html.Button('Submit',id = "btn_stock_input_submit",n_clicks=0)
            ]),
            html.Br(),
            html.Div([
              # Date range picker input
                  dcc.DatePickerRange(id = 'datepicker'
                      ,end_date=dt.today(),
                      display_format='MM/DD/YYYY',
                      start_date_placeholder_text='Start date',
                      max_date_allowed=dt.today().strftime('%Y-%m-%d'),
                      reopen_calendar_on_clear=True
                  )
            ],
            style={
                "display" : "flex"
            }),
            html.Br(),
            html.Div([
                html.Div([
                    # Stock price button
                    html.Button('Stock price',id = 'btn_stock_price'),
                    # Indicators button
                    html.Button('Indicators',id = 'btn_indicators',style={"position":"relative","left":"83px"})
                    ],style = {"display":"flex"}),
                    
                    html.Br(),
                    html.Div([
                        # Number of days of forecast input
                        dcc.Input(id = 'no_of_days_input',placeholder='number of days',type = 'number'),
                        # Forecast button
                        html.Button('Forecast',id = 'btn_forecast')
                    ],style = {"display": "flex"}),
                    html.Br()
            ]),
            html.Div([
              html.P("""Note: Here, number of days includes today's date 
                      as well, so please enter number of days plus 1. For
                       example, you want prediction for next day, enter 
                       number of days as 2 and click forecast button.""",style={"color":"white"}),
              html.P("""Stocks listed on US Stock exchange will show the results.""",style={"color":"white"})
            ])
          ],
        className="nav",
        style={
            "display" : "flex",
            "flex-direction" : "column",
            "align-items" : "center",
            "width" : "25vw",
            "justify-content": "flex-start",
            "background-color": "rgb(5, 100, 106)",
            "padding":"5px",
            "position":"inital",
            "min-width":"25%"
        })

item2 = html.Div(
          [
            html.Div(
                  [  # Logo
                    html.Img(id = 'company_logo',style={"height":"80px","width":"auto","position":"relative"}),
                    # Company Name
                    html.H1(id = "company_name",style = {"position":"relative","padding":"5px 5px"})
                  ],
                className="header",style={"display":"flex"}),
            html.Div( 
                    #Description
                    html.P(id = "descrp"),
                    id="description", className="decription_ticker"),
            html.Div([
                # Stock price plot
                dcc.Graph(id = 'stock_price_plot')
            ], id="graphs-content"),
            html.Div([
                # Indicator plot
                dcc.Graph(id = 'indicator_plot')
            ], id="main-content"),
            html.Div([
                # Forecast plot
                dcc.Graph(id = 'forecast_plot')
            ], id="forecast-content")
          ],
        className="content",
        style={
            "padding":"20px",
            "position":"relative"
        })


item3 = html.Div([
    html.H2("STOCK-DASH", id = "title",style={"text-align" : "center"})
])

app.layout = html.Div([item3,html.Div([item1,html.Br(),item2],style={"display":"flex"})])

"""*********************************************************************************************************"""
"""----------------------------------------------------CALLBACKS--------------------------------------------"""
"""*********************************************************************************************************"""

# Callback to update company logo, name, description
@app.callback(Output(component_id="company_name",component_property="children"),
              Output(component_id="descrp",component_property="children"),
              Output(component_id="company_logo",component_property="src"),
              Input(component_id="btn_stock_input_submit",component_property="n_clicks"),
              State(component_id="stock_input_field",component_property="value"))
def get_stock_data(n_clicks,stock_code):
  cmpy_name = 'Company Name'
  cmpy_summary = 'Hey there! Please enter legitimate stock code to get the details.'
  src = app.get_asset_url('../assets/stock-default-image.jpeg')
  if n_clicks > 0 and stock_code != None:
    # global data
    data = yt.Ticker(stock_code)
    info = data.info
    # print(info)
    if 'shortName' not in info.keys():
      raise PreventUpdate("Please enter a valid stock!!")
    cmpy_name = info['shortName']
    cmpy_summary = info['longBusinessSummary']
    src = info['logo_url']
    print(src)
    return cmpy_name,cmpy_summary,src
  print(src)
  return cmpy_name,cmpy_summary,src

# callback to display, update the stock graph (close, open)
@app.callback(Output(component_id="stock_price_plot",component_property="figure"),
              Input(component_id="btn_stock_price",component_property="n_clicks"),
              Input(component_id="datepicker",component_property="start_date"),
              Input(component_id="datepicker",component_property="end_date"),
              State(component_id="stock_input_field",component_property="value")
              )
def display_stock_graph(n_clicks,start_date,end_date,stock_code):
  if n_clicks == None or stock_code == None:
    raise PreventUpdate()
  date = dt.today().strftime('%Y-%m-%d')
  if n_clicks > 0 and stock_code != "":
    # global data
    data = yt.Ticker(stock_code)
    if end_date is not None:
      date = end_date[:10]
    if start_date is not None:
      start_date = start_date[:10]
    if data is not None:
      df = data.history(start = start_date,end = date,period = "max").reset_index()
      df = df[['Date','Close','Open']]
      fig = px.line(data_frame=df,
                    x = 'Date',
                    y = df.columns[1:])
      return fig
    else:
      raise PreventUpdate("Enter stock first!!")

# callback to display, update the ewm graph
@app.callback(Output(component_id="indicator_plot",component_property="figure"),
              Input(component_id="btn_indicators",component_property="n_clicks"),
              Input(component_id="datepicker",component_property="start_date"),
              Input(component_id="datepicker",component_property="end_date"),
              State(component_id="stock_input_field",component_property="value"))
def display_ewm_graph(n_clicks,start_date,end_date,stock_code):
  if n_clicks == None or stock_code == None:
    raise PreventUpdate()
  date = dt.today().strftime('%Y-%m-%d')
  if n_clicks > 0 and stock_code != "":
    # global data
    data = yt.Ticker(stock_code)
    if end_date is not None:
      date = end_date[:10]
    if start_date is not None:
      start_date = start_date[:10]
    if data is not None:
      df = data.history(start = start_date,end = date,period = "max").ewm(span=20,adjust = False).mean().reset_index()
      fig = px.line(data_frame=df,
                    x = 'Date',
                    y = 'Close',
                    labels={'Close':'EWM-Span-20'})
      return fig
    else:
      raise PreventUpdate("Enter stock first!!")
  

@app.callback(Output(component_id="forecast_plot", component_property="figure"),
              Input(component_id="btn_forecast",component_property="n_clicks"),
              State(component_id="stock_input_field",component_property="value"),
              # Input(component_id="btn_forecast",component_property="n_clicks"),
              State(component_id="no_of_days_input",component_property="value"))
def display_forecast_graph(n_clicks, stock, n_days):
  print(n_clicks,stock,n_days)
  if n_clicks is not None and n_days is not None and stock != None:
    if n_days == 1:
      raise PreventUpdate("Sorry predict today's forcast!! Please give input more than 1.")
    # download past 60 days data.
    df = yt.download(stock,period='60d')
    df.reset_index(inplace=True)
    df['Day'] = df.index

    days = []
    for day in range(len(df.Day)):
      days.append([day])
    
    x = days
    y = df[['Close']]

    x_train, x_test, y_train, y_test = train_test_split(x,
                                                      y,
                                                      test_size=0.1,
                                                      shuffle=False)
    model = train_model(X=x_train, Y = y_train)

    model.fit(x_train,y_train)

    output_days = []
    for day in range(1,n_days):
      output_days.append([day + x_test[-1][0]])
    
    dates = []
    current = date.today()
    for day in range(n_days):
      current += timedelta(days = 1)
      dates.append(current)

    predictions = model.predict(output_days)

    fig = go.Figure()
    fig.add_trace(
      go.Scatter(
        x = dates,
        y = predictions,
        mode = 'lines+markers',
        name = 'data'
      )
    )

    if n_days > 2:
      TITLE = "Predicted Close Price for next " + str(n_days-1) + " days"
    elif n_days == 2:
      TITLE = "Predicted Close Price for next day"
    fig.update_layout(
      title = TITLE,
      xaxis_title = "Date",
      yaxis_title = "Closed Price"
    )

    return fig
  else:
    raise PreventUpdate(msg = "No Stock is Entered!!")

"""*********************************************************************************************************"""
"""------------------------------------------------------SERVER---------------------------------------------"""
"""*********************************************************************************************************"""

if __name__ == '__main__':
    app.run_server(debug=True)