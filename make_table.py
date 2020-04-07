import os
from os.path import dirname, join
import pandas as pd
from bokeh.layouts import layout
from bokeh.models import (Button, ColumnDataSource, CustomJS, DataTable,
                          NumberFormatter, RangeSlider, TableColumn, HTMLTemplateFormatter, AutocompleteInput)
from bokeh.plotting import output_file, save, show
from s3_ops import write_html_to_s3

def run_make_table(creds):
    if creds.get('env') == 'dev':
        csvs_file_location = './dev_csv'
    else:
        csvs_file_location = 's3://graycannon.com/csvs'

    df = pd.read_csv('{}/country_table.csv'.format(csvs_file_location))
    df2 = pd.read_csv('{}/locale_table.csv'.format(csvs_file_location))
    base = pd.read_csv('{}/base.csv'.format(csvs_file_location))

    df['charts_page'] = './chart_pages/country_' + df['country_region'] + '.html'
    df2['charts_page'] = './chart_pages/locale_' + df2['locale'] + '.html'

    original_source1 = ColumnDataSource(data=df)
    source1 = ColumnDataSource(data=df)
    original_source2 = ColumnDataSource(data=df2)
    source2 = ColumnDataSource(data=df2)

    button = Button(label="Download", button_type="success", width_policy="max")
    button.js_on_click(CustomJS(args=dict(source=source1),
                                code=open(join(dirname(__file__), "download.js")).read()))

    button2 = Button(label="Download", button_type="success", width_policy="max")
    button2.js_on_click(CustomJS(args=dict(source=source2),
                                code=open(join(dirname(__file__), "download.js")).read()))

    columns = [
        TableColumn(field="country_region", title="Country/Region"),
        TableColumn(field="current_day", title="Confirmed Cases To {}".format(base['day'].max()), formatter=NumberFormatter(format="0,0")),
        TableColumn(field="new_cases", title="New Cases Current Day", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="peak_new", title="Peak New Cases", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="since_peak_new", title="Days Since Peak", formatter=NumberFormatter(format="0,0")),
        TableColumn(field="growth_rate", title="Daily Growth Rate", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="growth_factor", title="Daily Growth Factor", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="growth_rate_week", title="Weekly Growth Rate", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="growth_factor_week", title="Weekly Growth Factor", formatter=NumberFormatter(format="0,0.00")),
        TableColumn(field="charts_page", title="Link to Charts", formatter=HTMLTemplateFormatter(template='<a href="<%= charts_page%>" target="_blank"><%= country_region %> Charts</a>'))
    ]

    columns2 = columns.copy()
    columns2[0] = TableColumn(field="locale", title="Province/State")
    columns2[9] = TableColumn(field="charts_page", title="Link to Charts", formatter=HTMLTemplateFormatter(template='<a href="<%= charts_page%>" target="_blank"><%= locale %> Charts</a>'))

    data_table = DataTable(source=source1, columns=columns, width=1700, index_position=None)
    data_table2 = DataTable(source=source2, columns=columns2, width=1700, index_position=None)
    reset_button = Button(label="Reset Table", button_type="success", width_policy="min", height_policy="max")
    reset_button2 = Button(label="Reset Table", button_type="success", width_policy="min", height_policy="max")

    country_list = df['country_region'].unique().tolist()
    country_list_lower = [x.lower() for x in country_list]
    country_options = country_list + country_list_lower
    country_search = AutocompleteInput(title="Country:", completions=country_options)

    locale_list = df2['locale'].unique().tolist()
    locale_list_lower = [x.lower() for x in locale_list]
    locale_options = locale_list + locale_list_lower
    locale_search = AutocompleteInput(title="Province/State:", completions=locale_options)

    search_js = """
        var data = source.data;
        var originalData = orig.data;
        var f = cb_obj.value;
        for (var key in data) {
            data[key] = [];
            for (var i = 0; i < originalData[breakdown].length; ++i) {
                if (originalData[breakdown][i].toLowerCase() === f.toLowerCase()) {
                    data[key].push(originalData[key][i]);
                }
            }
        }
        console.log('originalData', originalData);
        console.log('data', data);
        source.change.emit();
    """

    reset_js = """
        console.log('click');
        search.value = '';
        source.data = JSON.parse(JSON.stringify(orig.data));
        source.change.emit();
    """

    callback = CustomJS(args=dict(source=source1, orig=original_source1, breakdown='country_region', target_object=data_table), code=search_js)
    reset_callback = CustomJS(args=dict(source=source1, orig=original_source1, search=country_search, target_object=data_table), code=reset_js)
    country_search.js_on_change('value', callback)
    reset_button.js_on_click(reset_callback)

    callback2 = CustomJS(args=dict(source=source2, orig=original_source2, breakdown='locale', target_object=data_table), code=search_js)
    reset_callback2 = CustomJS(args=dict(source=source2, orig=original_source2, search=locale_search, target_object=data_table), code=reset_js)
    locale_search.js_on_change('value', callback2)
    reset_button2.js_on_click(reset_callback2)

    page_layout = layout(
        [country_search, reset_button],
        [data_table],
        [button],
        [locale_search, reset_button2],
        [data_table2],
        [button2]
    )

    object_key = 'covid_tables.html'
    filename = '/tmp/{}'.format(object_key)
    output_file(filename, title='Covid Data Tables')

    save(page_layout)
    write_html_to_s3(filename, object_key, creds)
    os.remove(filename)
