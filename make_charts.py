import os
import pandas as pd
from bokeh.layouts import layout
from bokeh.models import (Button, ColumnDataSource, CustomJS, DataTable,
                          NumberFormatter, RangeSlider, TableColumn, HoverTool)
from bokeh.plotting import figure, output_file, save, show
from collections import OrderedDict
from s3_ops import write_html_to_s3

base = pd.read_csv('s3://graycannon.com/csvs/base.csv')

titles = {
    'Confirmed': 'Confirmed Cases',
    'new': 'Daily New Cases',
    'growth_rate': 'Daily Growth Rate',
    'new_5': 'New Cases Last 5 Days',
    'growth_rate_5': 'Five Day Growth Rate'
}

breakdown_names = {'Country/Region': 'country', 'Province/State': 'locale'}

def make_plot(breakdown_df, metric):
    if metric == 'Confirmed':
        width = 1200
    else:
        width = 600
    b_source = ColumnDataSource(data=breakdown_df)
    plot = figure(title=titles[metric], x_axis_type='datetime', plot_height=300, plot_width=width)
    plot.left[0].formatter.use_scientific = False
    plot.line('dt', metric, source=b_source, line_width=3, line_alpha=0.6)
    plot.circle('dt', metric, source=b_source)
    hover = HoverTool()
    hover.tooltips = OrderedDict([('Date', '@day'), (metric, '@{}'.format(metric))])
    plot.add_tools(hover)
    return plot

def make_charts(breakdown, area, creds):
    if area == 'World':
        breakdown_df = base.groupby(by='day').sum().reset_index()
    else:
        breakdown_df = base.groupby(by=[breakdown, 'day']).sum().reset_index()
        breakdown_df = breakdown_df.loc[breakdown_df[breakdown] == area].copy()
    breakdown_df = breakdown_df.sort_values('day')
    breakdown_df['new'] = breakdown_df['Confirmed'].diff()
    breakdown_df['growth_rate'] =  (breakdown_df['new'] - breakdown_df['new'].shift()) / breakdown_df['new'].shift()
    breakdown_df['new_5'] = breakdown_df['Confirmed'].diff(5)
    breakdown_df['new_5_prev'] = breakdown_df['Confirmed'].shift(5) - breakdown_df['Confirmed'].shift(10)
    breakdown_df['growth_rate_5'] = (breakdown_df['new_5'] - breakdown_df['new_5_prev']) / breakdown_df['new_5_prev']
    breakdown_df['dt'] = pd.to_datetime(breakdown_df['day'])
    plot1 = make_plot(breakdown_df, 'Confirmed')
    plot2 = make_plot(breakdown_df, 'new')
    plot3 = make_plot(breakdown_df, 'growth_rate')
    plot4 = make_plot(breakdown_df, 'new_5')
    plot5 = make_plot(breakdown_df, 'growth_rate_5')
    chart_layout = layout(
        [plot1],
        [plot2, plot3],
        [plot4, plot5]
    )
    
    key = 'chart_pages/{}_{}.html'.format(breakdown_names[breakdown], area)
    filename = '/tmp/{}'.format(key)
    if 'chart_pages' not in os.listdir('/tmp'):
        os.mkdir('/tmp/chart_pages')
    output_file(filename, title='{} Charts'.format(area))
    # show(chart_layout)
    save(chart_layout)
    write_html_to_s3(filename, key, creds)
    os.remove(filename)

def run_make_charts(creds):
    for country in base['Country/Region'].unique():
        make_charts('Country/Region', country, creds)

    for locale in base['Province/State'].unique():
        make_charts('Province/State', locale, creds)

    make_charts('Country/Region', 'World', creds)

