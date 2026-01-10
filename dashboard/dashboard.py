import logging
import os

import dash
import mysql.connector
import pandas as pd
import plotly.express as px
from dash import dcc, html
from plotly.graph_objects import Figure, Heatmap

DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "myuser")
DB_PASS = os.environ.get("DB_PASSWORD", "mypassword")
DB_NAME = os.environ.get("DB_NAME", "laundry_data")
LOCAL_TIMEZONE = "Europe/Amsterdam"

logging.basicConfig(
    format="[%(levelname)s] %(asctime)s %(message)s", level=logging.INFO
)
logger = logging.getLogger("laundry-dashboard.service")


def run_query(query):
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
        )
        cursor = conn.cursor()
        cursor.execute(query)
        data = cursor.fetchall()
        column_names = [i[0] for i in cursor.description]
        cursor.close()
        conn.close()
        df = pd.DataFrame(data, columns=column_names)
        conn.close()
        return df
    except Exception as e:
        logger.info(f"Database error: {e}")
        if conn and conn.is_connected():
            conn.close()
        return pd.DataFrame()


def serve_layout():
    last_washing = last_dryer = 0
    query = "select washing, dryer, TIME_FORMAT(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam'), '%H:%i') \"ts\" from scrape order by scrape.id desc LIMIT 1;"
    frame = run_query(query)
    if frame.empty:
        return html.Div(
            [
                html.H1("Machine Availability Dashboard"),
                html.P("Could not connect to database or data is empty."),
            ]
        )

    last_washing = frame.loc[0]["washing"]
    last_dryer = frame.loc[0]["dryer"]
    last_timestamp = frame.loc[0]["ts"]

    days = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    graphs = []

    start_hour = 8
    end_hour = 22
    subquery = f"select scrape_ts, washing, dryer, hour(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam')) \"hour\" from scrape having hour >= {start_hour} and hour <= {end_hour}"
    # start the week on Monday: give 7 as parameter to week()
    query = (
        f"select day(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam')) \"day\", week(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam'), 7) \"week\", "
        'weekday(CONVERT_TZ(scrape_ts, \'UTC\', \'Europe/Amsterdam\')) "weekday", avg(washing) "washing", avg(dryer) "dryer"'
        f"from ({subquery}) s group by week, day, weekday;"
    )
    data = run_query(query)

    ar_washing = [[None for j in range(0, 52)] for i in range(0, 8)]
    for i in range(data.shape[0]):
        ar_washing[data.iloc[i]["weekday"]][
            (data.iloc[i]["week"] if data.iloc[i]["week"] <= 51 else 0)
        ] = round(data.iloc[i]["washing"], 1)
    fig_washing = Figure(
        data=Heatmap(
            z=ar_washing,
            x=[f"Week {i}" for i in range(1, 53)],
            y=days,
            colorscale="Viridis",
            zmid=4,
            hoverongaps=False,
            showscale=False,
        ),
    )
    fig_washing.update_layout(
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        title=dict(
            text=f"Number of washing machines available over the day between {start_hour}:00 and {end_hour}:00"
        ),
    )
    graphs.append(html.Div(dcc.Graph(figure=fig_washing)))

    ar_dryer = [[None for j in range(0, 52)] for i in range(0, 8)]
    for i in range(data.shape[0]):
        ar_dryer[data.iloc[i]["weekday"]][
            (data.iloc[i]["week"] if data.iloc[i]["week"] <= 51 else 0)
        ] = round(data.iloc[i]["dryer"], 1)
    fig_dryer = Figure(
        data=Heatmap(
            z=ar_dryer,
            x=[f"Week {i}" for i in range(1, 53)],
            y=days,
            colorscale="Viridis",
            zmid=3.5,
            hoverongaps=False,
            showscale=False,
        ),
    )
    fig_dryer.update_layout(
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        title=dict(
            text=f"Number of dryers available over the day between {start_hour}:00 and {end_hour}:00"
        ),
    )

    graphs.append(html.Div(dcc.Graph(figure=fig_dryer)))

    for i, day in enumerate(days):
        query = (
            f"select weekday(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam')) \"day\", hour(CONVERT_TZ(scrape_ts, 'UTC', 'Europe/Amsterdam')) \"hour\", "
            f'round(avg(washing), 1) "washing", round(avg(dryer), 1) "dryer" from scrape group by hour, day having day={i};'
        )
        data = run_query(query)
        data_long = pd.melt(
            data,
            id_vars=["hour", "day"],
            value_vars=["washing", "dryer"],
            var_name="Machine_Type",
            value_name="Average_Usage",
        )
        fig = px.bar(
            data_long,
            x="hour",
            y="Average_Usage",
            color="Machine_Type",
            barmode="group",
            title=f"Average Usage for {day}",
            orientation="v",
            labels={
                "Machine_Type": "Washer/Dryer",
                "hour": "Hour of Day",
                "Average_Usage": "Free to use",
            },
        )
        fig.update_layout(yaxis_range=[0, 9], xaxis={"dtick": 1})
        graphs.append(
            html.Div(
                [
                    html.P(day, style="text-align: center;"),
                    dcc.Graph(
                        id=f"{day.lower()}-usage-graph",
                        figure=fig,
                        style={"marginBottom": "20px"},
                    ),
                ]
            )
        )

    return html.Div(
        [
            html.H1("Laundry Room Status Dashboard"),
            html.H3(
                f"Available: {last_washing} washing machines and {last_dryer} dryers at {last_timestamp} (updates every 10 minutes)"
            ),
            *graphs,
        ],
    )


app = dash.Dash(__name__)
app.title = "Laundry availability"
app.layout = serve_layout
server = app.server
# if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=8050)
