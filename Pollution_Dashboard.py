import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
from numerize.numerize import numerize


# Define the iframe code

# iframe_code = """
#         <iframe width="699" height="432" seamless frameborder="0" scrolling="no" src="https://docs.google.com/spreadsheets/d/e/2PACX-1vQUXkz36WAEe19Z3TvZh1JD-GnwmcatbbxTQ70nqb9_RxND9dWoCkWnoF_rwpUXJqh3hJqEqIQzkVBU/pubchart?oid=1038038571&amp;format=interactive"></iframe>
#     """

# # Embed the iframe in Streamlit using markdown
# st.markdown(iframe_code, unsafe_allow_html=True)


# Load your data

# st.set_page_config(page_title='Pollution_Dashboard', layout='centered')

months = {1: "Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}


with open ('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def load_data():
    #last 24 h
    return pd.read_csv('https://node-red.agile.ro/api/dorinel/csv')

def load_data_gsheet():
    SHEET_ID = '1s2wxow06Gxx5bOCk8bwcZD8Y7K-SFzm0fGv5woBb-C8'
    SHEET_NAME = 'farm1'
    url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'
    df = pd.read_csv(url)
    return df


def make_groups(data, size):
    """Helper function to generate aggregation groups."""
    n = len(data)
    return np.arange(n) // size


def show():
    with open ('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    data = load_data_gsheet()
    # data['datetime'] = pd.to_datetime(data['Time'])
    data['datetime'] = data['Time2'].apply(lambda x: datetime.utcfromtimestamp(x/1000))
    # data['datetime'] = pd.to_datetime(data['time_str'], format='%Y-%m-%d %H:%M:%S')
    data=data.drop(columns=["Time",'Time2'])
    data['datetime'] = data['datetime'].apply(lambda x: x+timedelta(days=365))
    data=data[data['datetime'] <= datetime.now()]

    data.columns = [ 'Battery', 'CO', 'Humidity', 'NH₃', 'PM 1', 'PM 10', 'PM 2.5', 'Pressure', 'Temperature','datetime']
    last_record_time=data['datetime'].iloc[-1]
    st.title("Pollution Dashboard")
    if last_record_time.minute<10:
        st.subheader(f"Last Updated :  {last_record_time.hour}:0{last_record_time.minute}, {last_record_time.day} {months[last_record_time.month]} {last_record_time.year} ")
    else:
        st.subheader(f"Last Updated :  {last_record_time.hour}:{last_record_time.minute}, {last_record_time.day} {months[last_record_time.month]} {last_record_time.year} ")
    container1=st.container()
    container2=st.container()

    col1, col2, col3, col4, col9 = container1.columns(5, gap='large')
    col5, col6, col7, col8 = container2.columns(4, gap='large')
    Dbattery= data['Battery'].iloc[-1]-data['Battery'].iloc[-2]
    DCO= data['CO'].iloc[-1]-data['CO'].iloc[-2]
    DHumidity=data['Humidity'].iloc[-1]-data['Humidity'].iloc[-2]
    DNH3=  data['NH₃'].iloc[-1]-data['NH₃'].iloc[-2]
    DPM1= data['PM 1'].iloc[-1]-data['PM 1'].iloc[-2]
    DPM2= data['PM 2.5'].iloc[-1]-data['PM 2.5'].iloc[-2]
    DPM10= data['PM 10'].iloc[-1]-data['PM 10'].iloc[-2]
    DPressure= data['Pressure'].iloc[-1]-data['Pressure'].iloc[-2]
    DTemperature= data['Temperature'].iloc[-1]-data['Temperature'].iloc[-2]

    color_CO = ":red[:rotating_light: **CO (ppm)**]" if data['CO'].iloc[-1] > 8.73 else ":green[:white_check_mark: **CO (ppm)**]"
    color_PM10 = ":red[:rotating_light: **PM 10 (µg/m³)**]" if data['CO'].iloc[-1] > 40 else ":green[:white_check_mark: **PM 10 (µg/m³)**]"
    color_PM2= ":red[:rotating_light: **PM 2.5 (µg/m³)**]:rotating_light:" if data['CO'].iloc[-1] > 20 else ":green[:white_check_mark: **PM 2.5 (µg/m³)**]"

    col1.metric("**Battery (%)**", "%.2f" % data['Battery'].iloc[-1], delta="Δt(-1h)= %.2f" % Dbattery )
    col2.metric (color_CO, "%.2f" % data['CO'].iloc[-1], delta="Δt(-1h)= %.2f" % DCO, delta_color="inverse" )
    col3.metric ("**Humidity (%)**", "%.2f" % data['Humidity'].iloc[-1], delta= "Δt(-1h)= %.2f" % DHumidity, delta_color="off")
    col4.metric ("**NH₃ (ppm)**", "%.2f" % data['NH₃'].iloc[-1], delta= "Δt(-1h)= %.2f" % DNH3, delta_color="inverse")
    col9.metric ("**PM 1 (µg/m³)**", "%.2f" % data['PM 1'].iloc[-1], delta= "Δt(-1h)= %.2f" % DPM1, delta_color="inverse" )
    col5.metric (color_PM10, "%.2f" % data['PM 10'].iloc[-1], delta= "Δt(-1h)= %.2f" % DPM10, delta_color="inverse")
    col6.metric (color_PM2, "%.2f" % data['PM 2.5'].iloc[-1], delta= "Δt(-1h)= %.2f" % DPM2, delta_color="inverse" )
    col7.metric ("**Pressure (Pa)**", numerize(data['Pressure'].iloc[-1]), delta= "Δt(-1h)= %.2f" % DPressure, delta_color="off")
    col8.metric ("**Temperature (°C)**", "%.2f" % data['Temperature'].iloc[-1], delta= "Δt(-1h)=  %.2f" % DTemperature, delta_color="off")

    # Sidebar for user inputs
    time_period = st.radio("Select Time Period", ["Last 24h", "Week", "Last 15 days", "Month", "Year"], horizontal=True, index=0)
    # sensor_type = st.radio("Select Sensor Type", ["BAT", "HUM", "LP", "LUX", "PRES", "TC", "US", "WF"], horizontal=True)

    sensors = ['Battery', 'CO', 'Humidity', 'NH₃', 'PM 1', 'PM 10', 'PM 2.5', 'Pressure', 'Temperature']
    # colorscale = [[0, "green"], [0.5, "yellow"], [1, "red"]]




    # Filter data based on selected time period
    if time_period == "Last 24h":
        filtered_df = data[-24:]

    elif time_period == "Week":
        filtered_df = data[-168:]
        filtered_df = filtered_df.groupby(make_groups(filtered_df, 4)).agg({
            'datetime': 'first',
            'Battery': 'mean',
            'CO': 'mean',
            'Humidity': 'mean',
            'NH₃': 'mean',
            'PM 1': 'mean',
            'PM 10': 'mean',
            'PM 2.5': 'mean',
            'Pressure': 'mean',
            'Temperature': 'mean'
        }).reset_index(drop=True)

    elif time_period == "Last 15 days":
        filtered_df = data[-360:]
        filtered_df = filtered_df.groupby(make_groups(filtered_df, 8)).agg({
            'datetime': 'first',
            'Battery': 'mean',
            'CO': 'mean',
            'Humidity': 'mean',
            'NH₃': 'mean',
            'PM 1': 'mean',
            'PM 10': 'mean',
            'PM 2.5': 'mean',
            'Pressure': 'mean',
            'Temperature': 'mean'
        }).reset_index(drop=True)

    elif time_period == "Month":
        filtered_df = data[-720:]
        filtered_df = filtered_df.groupby(make_groups(filtered_df, 12)).agg({
            'datetime': 'first',
            'Battery': 'mean',
            'CO': 'mean',
            'Humidity': 'mean',
            'NH₃': 'mean',
            'PM 1': 'mean',
            'PM 10': 'mean',
            'PM 2.5': 'mean',
            'Pressure': 'mean',
            'Temperature': 'mean'
        }).reset_index(drop=True)

    elif time_period == "Year":
        filtered_df = data[-8700:]
        filtered_df = filtered_df.groupby(make_groups(filtered_df, 72)).agg({
            'datetime': 'first',
            'Battery': 'mean',
            'CO': 'mean',
            'Humidity': 'mean',
            'NH₃': 'mean',
            'PM 1': 'mean',
            'PM 10': 'mean',
            'PM 2.5': 'mean',
            'Pressure': 'mean',
            'Temperature': 'mean'
        }).reset_index(drop=True)


    # Create a figure using Plotly Express
    fig = px.line(filtered_df, x='datetime', y=sensors, line_shape='spline')

    # Modify line width and marker

    marker_size = {
            'Last 24h': 10,
            'Week': 8,
            'Last 15 days': 6,
            'Month': 6,
            'Year' : 4
    }

    thresholds = {
        'CO':{
            'min':0,
            'max':8.73,
        },
        'PM 10':{
            'min':0,
            'max':40,
        },
        'PM 2.5':{
            'min':0,
            'max':20,
        },
        'Battery':{
            'min':100,
            'max':0,
        }
    }

    for trace in fig.data:
        trace.line.width = 3
        trace.line.color = 'royalblue'

        if trace.name in ['CO', 'PM 10', 'PM 2.5', 'Battery']:
            trace.mode = 'lines+markers'  # Display both lines and markers
            trace.marker.size = marker_size[time_period]  # adjust for desired marker size
            trace.marker.color = trace.y  # use y-values for coloring

            # Set color scaling bounds
            trace.marker.cmin = thresholds[trace.name]['min']
            trace.marker.cmax = thresholds[trace.name]['max']

            trace.marker.cauto = False  # don't let plotly decide the min/max for scaling
            trace.marker.colorscale = [[0, 'green'], [0.5, 'yellow'], [1.0, 'red']]  # green-yellow-red scale
        else:
            trace.mode = 'lines'


    # Add the buttons for each sensor
    buttons = []
    for i, sensor in enumerate(sensors):
        visible = [False] * len(sensors)
    # Add the buttons for each sensor
    buttons = []
    for i, sensor in enumerate(sensors):
        visible = [False] * len(sensors)
        visible[i] = True
        button_args = {
            'visible': visible
        }
        buttons.append(dict(
            label=sensor,
            method='update',
            args=[button_args, {"yaxis": {"title": sensor}, "xaxis": {"title": "Date & Time"}}]  # This line has been changed
        ))



    fig.update_layout(
        updatemenus=[
            {
                "buttons": buttons,
                "direction": "left",
                "pad": {"r": 25, "t": 25, "l": 25, "b": 25},
                "showactive": True,
                "x": 0.1,
                "xanchor": "auto",
                "y": 1.15,
                "yanchor": "top",
                "type": "buttons"
            }
        ],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=700,
        width = 1000,
        autosize=True



    )

    # Using Streamlit to display the chart
    st.plotly_chart(fig)







def show_b():
    with open ('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    data = load_data_gsheet()
    # data['datetime'] = pd.to_datetime(data['Time'])
    data['datetime'] = data['Time2'].apply(lambda x: datetime.utcfromtimestamp(x/1000).strftime('%Y-%m-%d %H:%M:%S'))

    # data['datetime'] = pd.to_datetime(data['time_str'], format='%Y-%m-%d %H:%M:%S')
    data=data.drop(columns=["Time"])
    st.write(data.head())
    data.columns = ['Time', 'BAT', 'HUM', 'LP', 'LUX', 'PRES', 'TC', 'US', 'WF', 'hi','datetime']

    last_record_time=data['datetime'].iloc[-1]
    st.title("Pollution Dashboard")
    if last_record_time.minute<10:
        st.subheader(f"Last Updated :  {last_record_time.hour}:0{last_record_time.minute}, {last_record_time.day} {months[last_record_time.month]} {last_record_time.year} ")
    else:
        st.subheader(f"Last Updated :  {last_record_time.hour}:{last_record_time.minute}, {last_record_time.day} {months[last_record_time.month]} {last_record_time.year} ")

    col1, col2, col3, col4 = st.columns(4, gap='large')
    col5, col6, col7, col8 = st.columns(4, gap='large')
    col1.metric("BAT", data['BAT'].iloc[-1])
    col2.metric ("HUM", data['HUM'].iloc[-1])
    col3.metric ("LP", data['LP'].iloc[-1])
    col4.metric ("LUX", data['LUX'].iloc[-1])
    col5.metric ("PRES", numerize(data['PRES'].iloc[-1]))
    col6.metric ("TC", data['TC'].iloc[-1])
    col7.metric ("US", data['US'].iloc[-1])
    col8.metric ("WF", data['WF'].iloc[-1])
    # Sidebar for user inputs
    time_period = st.radio("Select Time Period", ["Last 24h", "Week", "Last 15 days", "Month", "Year"], horizontal=True, index=0)
    # sensor_type = st.radio("Select Sensor Type", ["BAT", "HUM", "LP", "LUX", "PRES", "TC", "US", "WF"], horizontal=True)


    sensors = ['BAT', 'HUM', 'LP', 'LUX', 'PRES', 'TC', 'US', 'WF', 'hi']
    # colorscale = [[0, "green"], [0.5, "yellow"], [1, "red"]]


    # Filter data based on selected time period
    if time_period == "Last 24h":
        # filtered_df = data[data['datetime'] > (pd.Timestamp.now() - pd.Timedelta(days=1))]
        filtered_df = data[data['datetime']][-24:]

    # ... Implement filtering for other time periods similarly ...
    # Plot using plotly express


    # Create a figure using Plotly Express
    fig = px.line(filtered_df, x='datetime', y=sensors, line_shape='spline')

    # Modify line width and marker
    for trace in fig.data:
        trace.line.width = 3
        trace.line.color='royalblue'

        if trace.name in ["LUX", "HUM"]:
            trace.mode = 'lines+markers'  # Display both lines and markers
            trace.marker.size = 6  # adjust for desired marker size
            trace.marker.color = trace.y  # use y-values for coloring
            trace.marker.cauto = True  # let plotly decide the min/max for scaling
            trace.marker.colorscale = [[0, 'green'], [0.5, 'yellow'], [1.0, 'red']]  # green-yellow-red scale
        else:
            trace.mode = 'lines'


    # Add the buttons for each sensor
    buttons = []
    for i, sensor in enumerate(sensors):
        visible = [False] * len(sensors)
    # Add the buttons for each sensor
    buttons = []
    for i, sensor in enumerate(sensors):
        visible = [False] * len(sensors)
        visible[i] = True
        button_args = {
            'visible': visible
        }
        buttons.append(dict(
            label=sensor,
            method='update',
            args=[button_args, {"yaxis": {"title": sensor}, "xaxis": {"title": "Date & Time"}}]  # This line has been changed
        ))



    fig.update_layout(
        updatemenus=[
            {
                "buttons": buttons,
                "direction": "left",
                "pad": {"r": 25, "t": 25, "l": 25, "b": 25},
                "showactive": True,
                "x": 0.1,
                "xanchor": "auto",
                "y": 1.15,
                "yanchor": "top",
                "type": "buttons"
            }
        ],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=700,
        width = 1000,
        autosize=True



    )

    # Using Streamlit to display the chart
    st.plotly_chart(fig)
