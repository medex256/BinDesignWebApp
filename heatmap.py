import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

date_format = "%Y-%m-%d"

def streak(data: list[datetime]):

    recycling_last_month, recycling_last_month_start, recycling_last_month_end = 0, None, None
    longest_streak, longest_streak_start, longest_streak_end = 0, None, None
    current_streak, current_streak_start, current_streak_end, current_streak_ago = 0, None, None, 0
    
    last_date = None
    today = datetime.today()

    def parse_date(item):
        if isinstance(item, str):
            return datetime.strptime(item, date_format)
        return item
    
    
    dates = sorted((parse_date(item) for item in data))

    for date in dates:

        # recycling_last_month
        if date.month == today.month:
            recycling_last_month += 1
            if recycling_last_month_start == None: recycling_last_month_start = date
            recycling_last_month_end = date
    
        if isinstance(last_date,datetime) and last_date.date() == date.date():
            continue

        # current_streak
        if last_date is None or isinstance(last_date,datetime) and (date-last_date).days > 1:
            current_streak_start = date
            current_streak_end = date
            current_streak = 1
        
        if isinstance(last_date,datetime) and (date-last_date).days == 1:
            current_streak_end = date
            current_streak += 1
        
        # longest_streak
        if current_streak > longest_streak:
            longest_streak = current_streak
            longest_streak_start = current_streak_start
            longest_streak_end = current_streak_end
        
        last_date = date
    
    if isinstance(current_streak_end,datetime) and current_streak_end.date() != today.date():
        current_streak = 0
        current_streak_ago = (today-current_streak_end).days

    return recycling_last_month, recycling_last_month_start, recycling_last_month_end, \
    longest_streak, longest_streak_start, longest_streak_end, \
    current_streak, current_streak_start, current_streak_end, current_streak_ago

def heatmap(data : list[datetime], weeks : int = 32, width = 800, height = 300) -> go.Figure:

    base_day = datetime.today()

    weekday = base_day + timedelta(days=(6-base_day.weekday()))

    z = np.zeros(7*weeks, dtype=int)

    zmax = 1

    for item in data:
        date = datetime.strptime(item,date_format) if isinstance(item, str) else item
        if weekday - timedelta(days=7*weeks) <= date and date <= weekday:
            z[-(weekday-date).days] += 1
            if z > zmax: zmax = z
    
    z = np.reshape(z,(-1 , 7)).transpose(1,0)

    def get_date(x,y):
        return (weekday + timedelta(days=(x*7+y-7*weeks))).strftime(date_format)
    
    hovertext = [ [f'{z[y][x]} recycling on {get_date(x,y)}'
                for x in range(0,weeks) ]
                for y in range(0,7)]
    
    ytickvals, yticktext = list() , list()
    for i in range(0,weeks):
        month = (weekday + timedelta(days=(i*7-7*weeks+7))).strftime("%B")[:3] # +7 if bottom
        if len(yticktext) == 0 or yticktext[-1] != month:
            ytickvals.append(i)
            yticktext.append(month)
    
    transparent = 'rgba(255,255,255,0)'
    white = 'rgba(250,250,250,1)'

    fig = go.Figure(

        data = go.Heatmap(
            z = z,
            xgap = 2,
            ygap = 2,
            zmin = 0,
            zmax = zmax,
            showscale = False,
            colorscale = [[0, 'rgba(32,44,37,1)'], [1, 'rgba(57,211,83,1)']],
            hoverinfo = 'text',
            hovertext = hovertext,
            # hovertemplate = '%{z} rubbish on %{x}<extra></extra>',
        ),

        layout = go.Layout(
            margin=dict(l=0, r=0, t=0, b=0),
            autosize = False,
            width=width,
            height=height,
            plot_bgcolor = transparent,
            paper_bgcolor = transparent,
            
            yaxis_scaleanchor="x",
            xaxis = dict(
                side = "bottom",
                scaleanchor="y", constrain="domain",
                fixedrange = True,
                tickvals = ytickvals,
                ticktext = yticktext,
                tickangle = 0,
                gridcolor = transparent,
                zerolinecolor = transparent,
                color = white,

            ),
            yaxis = dict(
                scaleanchor="x", constrain="domain",
                autorange ='reversed',
                fixedrange = True,
                tickvals = [1,3,5],
                ticktext = ['Mon','Wed','Fri'],
                gridcolor = transparent,
                zerolinecolor = transparent,
                color = white,
            ),
        ),
    )

    return fig

if __name__ == '__main__':
    fig = heatmap(
        [
            '2024-11-8',
            '2024-11-8',
            '2024-11-8',
            '2024-11-4',
            '2024-11-4',
            '2024-11-5',
            '2024-11-5',
            '2024-11-1',
        ]
    )
    fig.show(config={'displayModeBar': False})