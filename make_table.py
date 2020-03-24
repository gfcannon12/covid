import os
from os.path import dirname, join
import pandas as pd
from bokeh.layouts import column
from bokeh.models import (Button, ColumnDataSource, CustomJS, DataTable,
                          NumberFormatter, RangeSlider, TableColumn, HTMLTemplateFormatter)
from bokeh.plotting import output_file, save, show
from s3_ops import write_html_to_s3

def run_make_table(creds):
    if creds.get('env') == 'dev':
        df = pd.read_csv('./dev_csv/country_table.csv')
    else:
        df = pd.read_csv('s3://graycannon.com/csvs/country_table.csv')
    df['charts_page'] = './chart_pages/country_' + df['country_region'] + '.html'

    if creds.get('env') == 'dev':
        df2 = pd.read_csv('./dev_csv/locale_table.csv')
    else:
        df2 = pd.read_csv('s3://graycannon.com/csvs/locale_table.csv')
    df2['charts_page'] = './chart_pages/locale_' + df2['locale'] + '.html'

    base = pd.read_csv('s3://graycannon.com/csvs/base.csv')

    source1 = ColumnDataSource(data=df)
    source2 = ColumnDataSource(data=df2)

    button = Button(label="Download", button_type="success")
    button.js_on_click(CustomJS(args=dict(source=source1),
                                code=open(join(dirname(__file__), "download.js")).read()))

    button2 = Button(label="Download", button_type="success")
    button2.js_on_click(CustomJS(args=dict(source=source2),
                                code=open(join(dirname(__file__), "download.js")).read()))

    columns = [
        TableColumn(field="country_region", title="Country/Region"),
        TableColumn(field="current_day", title="Confirmed Cases To {}".format(base['day'].max()), formatter=NumberFormatter(format="0,0")),
        TableColumn(field="new", title="New Cases Current Day", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="peak_new", title="Peak New Cases", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="since_peak_new", title="Days Since Peak", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="growth_rate", title="Daily Growth Rate", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="growth_factor", title="Daily Growth Factor", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="growth_rate_5", title="Five Day Growth Rate", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="growth_factor_5", title="Five Day Growth Factor", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="charts_page", title="Link to Charts", formatter=HTMLTemplateFormatter(template='<a href="<%= charts_page%>" target="_blank"><%= country_region %> Charts</a>'))
    ]

    columns2 = columns.copy()
    columns2[0] = TableColumn(field="locale", title="Locale")
    columns2[9] =TableColumn(field="charts_page", title="Link to Charts", formatter=HTMLTemplateFormatter(template='<a href="<%= charts_page%>" target="_blank"><%= locale %> Charts</a>'))


    data_table = DataTable(source=source1, columns=columns, width=1700, index_position=None)
    data_table2 = DataTable(source=source2, columns=columns2, width=1700, index_position=None)

    page_layout = column(data_table, button, data_table2, button2)

    object_key = 'covid_tables.html'
    filename = '/tmp/{}'.format(object_key)
    output_file(filename, title='Covid Data Tables')

    # show(page_layout)
    save(page_layout)
    write_html_to_s3(filename, object_key, creds)
    os.remove(filename)
