from flask import Flask, render_template
import plotly.offline as pyo
from heatmap import heatmap, streak

app = Flask(__name__)

@app.route('/')
def chart():

    data = [
        '2024-11-3',
        '2024-11-3',
        '2024-11-3',
        '2024-11-4',
        '2024-11-4',
        '2024-11-5',
        '2024-11-5',
        '2024-11-1',
        '2024-11-7',
    ]

    plot_html = pyo.plot(
        figure_or_data = heatmap(data=data,weeks=32),
        output_type = 'div',
        config = {
            "displaylogo": False,
            'modeBarButtonsToRemove': ['pan2d','lasso2d','toImage'],
        },
    )

    date_format = "%Y-%m-%d"

    recycling_last_month, recycling_last_month_start, recycling_last_month_end, \
    longest_streak, longest_streak_start, longest_streak_end, \
    current_streak, current_streak_start, current_streak_end, current_streak_ago = streak(data)

    recycling_last_month_dates = "" if recycling_last_month == 0 else f"From: {recycling_last_month_start.strftime(date_format)} To: {recycling_last_month_end.strftime(date_format)}"
    longest_streak_dates = "" if longest_streak == 0 else f"From: {longest_streak_start.strftime(date_format)} To: {longest_streak_end.strftime(date_format)}"
    current_streak_dates = (f"Last recycled {current_streak_ago} days ago" if current_streak_ago > 0 else "") if current_streak == 0 else f"From: {current_streak_start.strftime(date_format)} To: {current_streak_end.strftime(date_format)}"

    return render_template(
        'chart.html', 
        plot=plot_html,
        recycling_last_month=f"{recycling_last_month} total",
        longest_streak=f"{longest_streak} days",
        current_streak=f"{current_streak} days",
        recycling_last_month_dates=recycling_last_month_dates,
        longest_streak_dates=longest_streak_dates,
        current_streak_dates=current_streak_dates,
    )

if __name__ == '__main__':
    app.run(debug=True)