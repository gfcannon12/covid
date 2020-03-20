import pandas as pd
import numpy as np
from datetime import datetime
from datetime import timedelta
from s3_ops import write_csv_to_s3

class DailyData:
    def __init__(self, creds):
        self.creds = creds
        self.today_utc = datetime.utcnow()
        self.date_range = pd.date_range(start='2020-01-22', end=self.today_utc)
        self.data_days =[]
        self.day_dfs = []
        self.world_confirmed = []
        self.country_rows = []
        self.locale_rows = []
        self.create_data_sets()

    def get_and_write_base(self):
        base = pd.concat(self.day_dfs, sort=False)
        base = base.drop(columns=['Latitude', 'Longitude'])
        base.loc[base['Country/Region'] == 'Mainland China', 'Country/Region'] = 'China'
        base = base.sort_values('day')
        write_csv_to_s3(base, 'base.csv', self.creds)
        return base

    def make_row(self, df, idx):
        df = df.copy()
        confirmed = {}
        if idx == 'World':
            confirmed['peak_new'] = self.world_peak_new
            confirmed['since_peak_new'] = self.days_since_world_peak
        else:
            df['new'] = df['Confirmed'].diff()
            confirmed['peak_new'] = df['new'].max()
            confirmed['since_peak_new'] = np.nan
            peak_days = df.loc[df['new'] == df['new'].max(), 'day'].values
            if len(peak_days) == 0:
                confirmed['since_peak_new'] = np.nan
            else:
                peak_day = peak_days[0]
                confirmed['since_peak_new'] = (self.focus_days['current_day'] - peak_day).days
        for key in self.focus_days.keys():
            confirmed[key] = df.loc[df['day'] == self.focus_days[key], 'Confirmed'].sum()
        confirmed_df = pd.DataFrame(confirmed, index=[idx])
        return confirmed_df

    def calculate_table(self, rows, idx_name):
        table = pd.concat(rows)
        table.index = table.index.rename(idx_name)
        table = table.reset_index()
        table['new'] = table['current_day'] - table['previous_day']
        table['new_prev'] = table['previous_day'] - table['two_days_ago']
        table['new_prev_prev'] = table['two_days_ago'] - table['three_days_ago']
        table['new_5'] = table['current_day'] - table['five_days_ago']
        table['new_5_prev'] = table['five_days_ago'] - table['ten_days_ago']
        table['new_5_prev_prev'] = table['ten_days_ago'] - table['fifteen_days_ago']
        table['growth_rate'] = (table['new'] - table['new_prev']) / table['new_prev']
        table['growth_rate_prev'] = (table['new_prev'] - table['new_prev_prev']) / table['new_prev_prev']
        table['growth_factor'] = table['growth_rate'] / table['growth_rate_prev']
        table['growth_rate_5'] = (table['new_5'] - table['new_5_prev']) / table['new_5_prev']
        table['growth_rate_5_prev'] = (table['new_5_prev'] - table['new_5_prev_prev']) / table['new_5_prev_prev']
        table['growth_factor_5'] = table['growth_rate_5'] / table['growth_rate_5_prev']
        table = table.sort_values('new', ascending=False)
        return table

    def get_country_rows(self, base):
        self.country_rows.append(self.make_row(base, 'World'))
        countries = base.groupby(by=['Country/Region', 'day']).sum().reset_index()
        for country in countries['Country/Region'].unique():
            country_df = countries.loc[countries['Country/Region']  == country]
            self.country_rows.append(self.make_row(country_df, country))

    def get_locale_rows(self, base):
        locales = base.groupby(by=['Province/State', 'day']).sum().reset_index()
        for locale in locales['Province/State'].unique():
            locale_df = locales.loc[locales['Province/State']  == locale]
            self.locale_rows.append(self.make_row(locale_df, locale))

    def set_focus_days(self):
        self.focus_days = {
                    "current_day": self.data_days[-1],
                    "previous_day": self.data_days[-2],
                    "two_days_ago": self.data_days[-3],
                    "three_days_ago": self.data_days[-4],
                    "five_days_ago": self.data_days[-6],
                    "ten_days_ago": self.data_days[-11],
                    "fifteen_days_ago": self.data_days[-16]
        }

    def create_data_sets(self):
        for day in self.date_range:
            date = day.strftime('%m-%d-%Y')
            try:
                filename = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{date}.csv'
                day_df = pd.read_csv(filename)
                day_df['day'] = day
                day_confirmed = day_df['Confirmed'].sum()
                self.day_dfs.append(day_df)
                self.data_days.append(day)
                self.world_confirmed.append(day_confirmed)
            except Exception:
                pass
        self.set_focus_days()
        world_confirmed_by_day = pd.Series(dict(zip(self.data_days, self.world_confirmed)))
        world_new_by_day = world_confirmed_by_day.diff()
        self.world_peak_new = world_new_by_day.max()
        world_peak_day = world_new_by_day[world_new_by_day == self.world_peak_new].index[0]
        self.days_since_world_peak = (self.focus_days['current_day'] - world_peak_day).days
        base = self.get_and_write_base()
        self.get_country_rows(base)
        self.get_locale_rows(base)
        country_table = self.calculate_table(self.country_rows, 'country_region')
        write_csv_to_s3(country_table, 'country_table.csv', self.creds)
        locale_table = self.calculate_table(self.locale_rows, 'locale')
        locale_table = locale_table.drop(index=locale_table.loc[locale_table['locale'].isin(['France', 'Netherlands', 'United Kingdom', 'Denmark'])].index)
        write_csv_to_s3(locale_table, 'locale_table.csv', self.creds)
