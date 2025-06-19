import requests
import pandas as pd
from datetime import datetime
from minio import Minio
from io import BytesIO

from dotenv import load_dotenv
from datetime import datetime
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
import os

import dash
from dash import Dash, html, dcc, Input, Output, State, callback, Patch
import dash_bootstrap_components as dbc
#import dash_ag_grid as dag

# Load from .env file
load_dotenv()

# Access credentials
MINIO_USER = os.getenv("MINIO_ROOT_USER")
MINIO_PASS = os.getenv("MINIO_ROOT_PASSWORD")
WEATHER_API = os.getenv("WEATHERSTACK_API_KEY")

print(f"Connecting with user: {MINIO_USER}")

from minio import Minio

client = Minio(
    "localhost:9000",
    access_key=MINIO_USER,
    secret_key=MINIO_PASS,
    secure=False
)
BUCKET_NAME = "minio1"
OBJECT_NAME = "weather_csv_2022_25.csv"

# Fetch object as a stream
response = client.get_object(bucket_name=BUCKET_NAME, object_name=OBJECT_NAME)

# Read into pandas DataFrame
df = pd.read_csv(BytesIO(response.read()))

#df=pd.read_csv(r"C:\Users\Arnab Basak\Downloads\weather_csv_2022_25.csv")

df['date']=pd.to_datetime(df['date'])
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year
df['day'] = df['date'].dt.day
df['week'] = df['date'].dt.isocalendar().week

heading = html.H1("Weather Analysis Dashboard")

year_dropdown = html.Div(
    [
        dbc.Label("Select Year", html_for="year_dropdown"),
        dcc.Dropdown(
            id="year-dropdown",
            options=sorted(df['year'].unique()),
            value=2023,
            clearable=False,
            maxHeight=600,
            optionHeight=50
        ),
    ],  className="mb-4",
)
month_dropdown = html.Div(
    [
        dbc.Label("Select Month", html_for="month_dropdown"),
        dcc.Dropdown(
            id="month-dropdown",
            options=sorted(df['month'].unique()),
            value=5,
            clearable=False,
            maxHeight=600,
            optionHeight=50
        ),
    ],  className="mb-4",
)

control_panel = dbc.Card(
    dbc.CardBody(
        [year_dropdown, month_dropdown ],
        className="bg-light",
    ),
    className="mb-4"
)

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container(
    [
        heading,
        dbc.Row([
            dbc.Col([control_panel,
                     dbc.Row([dbc.Col(html.Div(id="average-stats-card"), width=12)], className="mb-3"),
                    ],md=2),
            dbc.Col(
                [
                    dcc.Markdown(id="title"),
                    dbc.Row([dbc.Col(html.Div(id="highest-temp-card"), width=6),
                             dbc.Col( html.Div(id="highest-rain-card"), width=6)], className="mb-3"),
                    dbc.Row([dbc.Col(html.Div(id="temp-line-chart"), width=12)], className="mb-3"),
                    dbc.Row(
                        [dbc.Col(html.Div(id="calendar-heatmap"), width=6), 
                         dbc.Col(html.Div(id="rain-bar-chart"), width=6)]),
                ],  width=10
            ),
        ]),

    ],
    fluid=True,
)


@app.callback(
    Output('calendar-heatmap', 'children'),
    Output('temp-line-chart', 'children'),
     Output('rain-bar-chart', 'children'),
    [Input('year-dropdown', 'value'),
     Input('month-dropdown', 'value')]
)

def update_heatmap_plot(selected_year, selected_month):
    selected_df = df.loc[(df['month'] == selected_month) & (df['year'] == selected_year)]
    #if selected_df.empty:
    #    return px.imshow(np.zeros((5, 7)), text_auto=True, title="No data for selected month and year")
    

    monthly_df = selected_df.groupby(pd.Grouper(key='date', freq='D')).mean().reset_index()
    date_obj = datetime(selected_year,selected_month,1)
    weekday=date_obj.weekday()
    #print('weekday=====',weekday)
    monthly_temp=np.nan * np.zeros((6,7))
    #print(monthly_temp)
    dates=np.empty((6, 7), dtype='<U20')
    #print(dates)

    #start_day = date_obj.weekday()
    week_c=0
    for i, r in monthly_df.iterrows():
        #print(r['temperature_2m'])
        #print(int(i/7))
        #print(f"{i+1:02d}/{selected_month:02d}/{selected_year}")
        monthly_temp[week_c][weekday]=r['temperature_2m']
        #print('week_c=====',week_c)
        #print('weekday=====',weekday)
        #print(monthly_temp)
        dates[int(i/7)][weekday]=f"{i+1:02d}/{selected_month:02d}/{selected_year}"
        if(weekday==6):
            weekday=0
            week_c = week_c+1
        else:
            weekday = weekday+1
    #print(monthly_temp)
    #print(dates)
    heatmap = px.imshow(
    monthly_temp,
    labels=dict(x="Week Day", y="Week Number", color="Temperature"),
                x=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                y=['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6'],color_continuous_scale='rdylbu_r')
    heatmap.update_traces(
        customdata=dates,
        hovertemplate=
        "<b>Date</b>: %{customdata}<br>" +
        "<b>Temperature</b>: %{z}°C" +
        "<extra></extra>",
        xgap=1,
        ygap=1
        )
    
    '''heatmap = go.Figure(data=go.Heatmap(
                    z=monthly_temp,
                    x=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                    y=['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5','Week 6'],colorscale='rdylbu_r',
                    customdata=dates,
                    hoverongaps = False,
                    hovertemplate =
                    '<b>Date</b>: %{customdata}'+
                    '<br><b>Temperature</b>: %{z}<br>'+'<extra></extra>',
                    xgap=1,
                    ygap=1   ))
    heatmap.update_layout(
        autosize=True,
        #xaxis=dict(title='Month', side='top', tickangle=45),
        yaxis=dict(
            autorange='reversed',
            automargin=True,
        ),
        height=500,
        width=600,
        title=dict(text='Temperature Heatmap',x=0.5,y=0.1)
    )
    heatmap.update_yaxes(automargin=True)'''
    heatmap.update_layout(title=f"Temperature Calendar for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")

    line_chart = px.line(monthly_df, x=monthly_df['date'], y=monthly_df['temperature_2m'])
    line_chart.update_layout(title=f"Temperature Line Chart for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")

    bar_chart=px.bar(monthly_df, x=monthly_df['date'], y=monthly_df['rain'])
    bar_chart.update_layout(title=f"Rain Bar Chart for {datetime(selected_year, selected_month, 1).strftime('%B %Y')}")

    heatmap_card=dbc.Card([
        dbc.CardHeader(html.H2("Calendar Heatmap"), className="text-center"),
        dcc.Graph(figure=heatmap, style={"height":500}, config={'displayModeBar': False})
    ],style={"height": "100%", "padding": "0.5rem"})

    line_chart_card=dbc.Card([
        dbc.CardHeader(html.H2("Temperature line chart"), className="text-center"),
        dcc.Graph(figure=line_chart, style={"height":400}, config={'displayModeBar': False})
    ])

    bar_chart_card=dbc.Card([
        dbc.CardHeader(html.H2("Rain Bar chart"), className="text-center"),
        dcc.Graph(figure=bar_chart, style={"height":500}, config={'displayModeBar': False})
    ])

    return heatmap_card,line_chart_card,bar_chart_card



@app.callback(
    Output('highest-temp-card', 'children'),
    Output('highest-rain-card', 'children'),
    Output('average-stats-card', 'children'),
    [Input('year-dropdown', 'value'),
     Input('month-dropdown', 'value')]
)
def update_cards(selected_year, selected_month):
    selected_df=df.loc[(df['month'] == selected_month) & (df['year'] == selected_year)]
    monthly_df = selected_df.groupby(pd.Grouper(key='date', freq='D')).mean().reset_index()
    max_temp=monthly_df['temperature_2m'].max()
    max_temp_day= monthly_df.loc[monthly_df['temperature_2m'] == max_temp, 'date'].dt.strftime('%d %b %Y').values[0]
    max_rain=monthly_df['rain'].max()
    max_rain_day= monthly_df.loc[monthly_df['temperature_2m'] == max_temp, 'date'].dt.strftime('%d %b %Y').values[0]
    avg_rain=monthly_df['rain'].mean()
    avg_temp=monthly_df['temperature_2m'].mean()
    avg_humidity=monthly_df['relative_humidity_2m'].mean()
    avg_windspeed=monthly_df['wind_speed_10m'].mean()
    


    max_temp_card =  dbc.Card([
        dbc.CardHeader(html.H2("Monthly Max Temp"), className="text-center"),
        dbc.CardBody([
            html.H4(f"{max_temp:.2f}°C"),
            html.Small(f"on {max_temp_day}")
        ])
    ])
    max_rain_card =  dbc.Card([
        dbc.CardHeader(html.H2("Monthly Max Rain"), className="text-center"),
        dbc.CardBody([
            html.H4(f"{max_rain:.2f} mm"),
            html.Small(f"on {max_rain_day}")
        ])
    ])

    avg_card =  dbc.Card([
        dbc.CardHeader(html.H2("Average Monthy Measures"), className="text-center"),
        dbc.CardBody([
                    html.H4(["Average Rain: ",
                    html.Span(f"{avg_rain:.2f} mm", style={"fontWeight": "normal"})]),
                    html.H4([
                        "Average Temp: ",
                        html.Span(f"{avg_temp:.2f} °C", style={"fontWeight": "normal"})
                    ]),
                    html.H4([
                        "Average Humidity: ",
                        html.Span(f"{avg_humidity:.2f} %", style={"fontWeight": "normal"})
                    ]),
                    html.H4([
                        "Average Windspeed: ",
                        html.Span(f"{avg_windspeed:.2f} m/s", style={"fontWeight": "normal"})
                    ]),

                ])
            ])

    return max_temp_card,max_rain_card,avg_card


if __name__ == '__main__':
    app.run(debug=True)
