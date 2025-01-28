''' 
This script prepare the export from RotaReady to be ingested in the PowerBi Dataset Model on top of which
the PowerBi Dashboard is built.

There are 3 Different Classes that perform the same operations - receiveing different inputs.

1. Transforming Data from RotaReady
2. Transforming Data from Fourth (Single Shifts)
3. Transforming Data from Fourth (Double Shifts)
'''

import pandas as pd
import numpy as np
import streamlit as st
import random
import time

class TransformationRotaReady:
    def __init__(self, df, with_breaks=True):
        self.with_breaks = with_breaks
        self.df = df
        with st.expander("⚙️ Processing Data"):
            self.df = self.transform()

    def cleaning(self):
        '''
        1. Keep only event type = shift
        '''
        start_time = time.time()
        # keep only event type = shift
        self.df = self.df[self.df["Event type"] == "Shift"]
        self.df = self.df.astype(str)
        st.info(f'🧹 Cleaning done (only kept shift data, removed absence and salary data) - {len(self.df)} rows - {round((time.time() - start_time))} seconds')

    def transformation1(self):
        '''
        1. Tranform Start and finish to dates 
        2. Decompose the Start and End time to get minutes and hours
        3. Create a column for paid hours
        4. Get start hour and end hour
        5. Transform the values in float and calculate the paid hours
        6. Keep only more than 0.5 hours and less than 15 hours
        7. Create a column for paid hours
        '''
        start_time = time.time()
        #1. Transform start and finish
        self.df["Start"] = pd.to_datetime(self.df["Start"], format='mixed', dayfirst=True)
        self.df["Finish"] = pd.to_datetime(self.df["Finish"], format = 'mixed', dayfirst=True)
                                               # create a column for paid hours
        #2. Get start hour and end hour
        self.df["HourStart"] = self.df["Start"].dt.hour
        self.df["HourEnd"] = self.df["Finish"].dt.hour 
        #3. Transform the values in float and calculate the paid hours
        self.df["Paid hours"] = self.df["Paid hours"].astype(float)
        self.df["Unpaid hours"] = self.df["Unpaid hours"].astype(float)
        self.df["TotalHours"] = self.df["Paid hours"] + self.df["Unpaid hours"]
        #4. Keep only more than 0.5 hours and less than 15 hours
        self.df = self.df[(self.df["TotalHours"] > 0.5) & (self.df["TotalHours"] < 15)]
        self.min_hour = 4
        self.df["HourEnd"] = np.where(self.df["HourEnd"] < self.min_hour, self.df["HourEnd"] + 24, self.df["HourEnd"])
        #self.max_hour = self.df["HourEnd"].max()
        self.max_hour = 27
        choices = ['00', '15', '30']

        # create a minute_end column taking only the minute from the end time
        self.df["EndMinutes"] = pd.to_datetime(self.df["Finish"],format = 'mixed', dayfirst=True).dt.minute
        conditions_end = [
            self.df["EndMinutes"] <= 8,
            (self.df["EndMinutes"] > 8) & (self.df["EndMinutes"] <= 23),
            (self.df["EndMinutes"] > 23) & (self.df["EndMinutes"] <= 38)
        ]
        self.df["EndMinutes"] = np.select(conditions_end, choices, default='45')


        self.df["StartMinutes"] = pd.to_datetime(self.df["Start"],format = 'mixed', dayfirst=True).dt.minute
        conditions_start = [
            self.df["StartMinutes"] <= 8,
            (self.df["StartMinutes"] > 8) & (self.df["StartMinutes"] <= 23),
            (self.df["StartMinutes"] > 23) & (self.df["StartMinutes"] <= 38)
        ]
        choices = ['00','15','30']
        # as int
        choices = [int(i) for i in choices] 
        self.df["StartMinutes"] = np.select(conditions_start, choices, default=45)
        st.info('⚡ Transformation 1/4 done (Processing dates, calculating hours & minutes, filtering shifts between 0.5-15h) - %s seconds | Total rows: %s' % (round((time.time() - start_time)), len(self.df)))
        return self.df

    def transformation2(self):
        start_time = time.time()
        hours = list(range(self.min_hour,self.max_hour+1))
        minutes = ['00','15','30','45']
        columns = ['HourStart','StartMinutes','Start', 'HourEnd', 'EndMinutes', 'Finish']
        hours_minutes = [str(hour)+":"+str(minute) for hour in hours for minute in minutes]
        self.df = pd.concat([self.df, pd.DataFrame(0, index=self.df.index, columns=hours_minutes)], axis=1)
        for index, row in self.df.iterrows():
            #get start hour and end hour
            start_hour = row["HourStart"]
            min_start = row['StartMinutes']
            end_hour = row["HourEnd"]
            min_end = row["EndMinutes"]
            # transform to int 
            start_hour = int(start_hour)
            end_hour = int(end_hour)
            if start_hour < self.min_hour:
                start_hour += 24
            try:
                start_column_index = self.df.columns.get_loc(f"{start_hour}:{str(min_start).zfill(2)}")
            except: 
                st.write(row)
                continue
            end_column_index = self.df.columns.get_loc(f"{end_hour}:{str(min_end).zfill(2)}")

            columns = self.df.columns[start_column_index:end_column_index]
            self.df.loc[index, columns] = 1

            if self.df.loc[index,'Unpaid hours'] > 0 : 
                allowed_break_hours = [9,10,11,14,15,22,23]
                half_shift = (end_hour - start_hour)//2
                median_hour = start_hour + half_shift

                if median_hour in allowed_break_hours:
                    # set median hour and random 15 min interval to 0.33
                    self.df.loc[index, str(median_hour)+":00"] = 0

                else:
                    # if isn't in the allowed break hours then set the median hour to 0.5
                    # check the closest allowed break hour between the start and end hour
                    allowed_hours_in_this_case = [hour for hour in allowed_break_hours if hour > start_hour and hour < end_hour]
                    closest_allowed_break_hour = min(allowed_break_hours, key=lambda x:abs(x-median_hour))
                    # set the closest allowed break hour to 0.5
                    self.df.loc[index, str(closest_allowed_break_hour)+":00"] = 0

        st.info('⚡ Transformation 2/4 done (Creating 15 min intervals for breaks) - %s seconds | Total rows: %s' % (round((time.time() - start_time)), len(self.df)))
        return self.df
    
    def transformation2_(self):
        start_time = time.time()
        hours = list(range(self.min_hour,self.max_hour+1))
        minutes = ['00','15','30','45']
        columns = ['HourStart','StartMinutes','Start', 'HourEnd', 'EndMinutes', 'Finish']
        hours_minutes = [str(hour)+":"+str(minute) for hour in hours for minute in minutes]
        self.df = pd.concat([self.df, pd.DataFrame(0, index=self.df.index, columns=hours_minutes)], axis=1)
        for row in self.df.itertuples():
            #get start hour and end hour
            start_hour = getattr(row, "HourStart")
            min_start = getattr(row, 'StartMinutes')
            end_hour = getattr(row, "HourEnd")
            min_end = getattr(row, "EndMinutes")

            start_column_index = self.df.columns.get_loc(f"{start_hour}:{str(min_start).zfill(2)}")
            end_column_index = self.df.columns.get_loc(f"{end_hour}:{str(min_end).zfill(2)}")

            columns = self.df.columns[start_column_index:end_column_index]
            self.df.loc[row.Index, columns] = 1

            if end_hour - start_hour >=6:
                allowed_break_hours = [9,10,11,14,15,22,23]
                half_shift = (end_hour - start_hour)//2
                median_hour = start_hour + half_shift

                if median_hour in allowed_break_hours:
                    # set median hour and random 15 min interval to 0.33
                    self.df.loc[row.Index, str(median_hour)+":00"] = 0

                else:
                    # if isn't in the allowed break hours then set the median hour to 0.5
                    # check the closest allowed break hour between the start and end hour
                    allowed_hours_in_this_case = [hour for hour in allowed_break_hours if hour > start_hour and hour < end_hour]
                    closest_allowed_break_hour = min(allowed_break_hours, key=lambda x:abs(x-median_hour))
                    # set the closest allowed break hour to 0.5
                    self.df.loc[row.Index, str(closest_allowed_break_hour)+":00"] = 0

        st.info('Transformation 2/4 done - %s seconds' % round((time.time() - start_time)))
        st.write(self.df)
        return self.df
    
    def transformation3(self):
        start_time = time.time()
        # here we need to create a column called MinuteAfterClosing (each cafe has a different closing time - relative to day of the week)
        # add Dishoom to Site (appointment) column before the actual site
        self.df["Site (appointment)"] = "Dishoom " + self.df["Site (appointment)"]

        res_to_rename = {
            'Dishoom Covent Garden': 'D1',
            'Dishoom Shoreditch': 'D2',
            'Dishoom Kings Cross': 'D3',
            'Dishoom Carnaby': 'D4',
            'Dishoom Edinburgh': 'D5',
            'Dishoom Kensington': 'D6',
            'Dishoom Manchester': 'D7',
            'Dishoom Birmingham': 'D8',
            'Dishoom Canary Wharf': 'D9',
            'Dishoom Battersea': 'D10',

            'Dishoom Brighton Permit Room': 'PR1',
            'Dishoom Cambridge Permit Room' : 'PR2',
            'Dishoom Oxford Permit Room': 'PR3',
        }

        self.df["Site (appointment)"] = self.df["Site (appointment)"].replace(res_to_rename)
        # drop the rest of them
        res_val = res_to_rename.values()
        self.df = self.df[self.df["Site (appointment)"].isin(res_val)]

        self.df['Day of the week'] = pd.to_datetime(self.df["Start"],format = 'mixed', dayfirst=True).dt.day_name()
        # add correct closign time based on day of the week -> 23.00 for monday to thursday, 03.00 for friday to sunday
        group_1_closing_schema = {
            'Sunday': 23,
            'Monday': 23,
            'Tuesday': 23,
            'Wednesday': 23,
            'Thursday': 23,
            'Friday': 24,
            'Saturday': 24
        }
        group_2_closing_schema = {
            'Sunday': 23,
            'Monday': 23,
            'Tuesday': 23,
            'Wednesday': 23,
            'Thursday': 24,
            'Friday': 24,
            'Saturday': 24
        }
        group_3_closing_schema = {
            'Sunday': 23,
            'Monday': 23,
            'Tuesday': 23,
            'Wednesday': 23,
            'Thursday': 23,
            'Friday': 23,
            'Saturday': 23
        }

        # assign the closing time to the restaurant
        res_ = {
            'D1': group_1_closing_schema,
            'D2': group_2_closing_schema,
            'D3': group_2_closing_schema,
            'D4': group_1_closing_schema,
            'D5': group_1_closing_schema,
            'D6': group_3_closing_schema,
            'D7': group_1_closing_schema,
            'D8': group_1_closing_schema,
            'D9': group_1_closing_schema,
            'D10': group_1_closing_schema,
            'PR1': group_1_closing_schema,
            'PR2': group_1_closing_schema,
            'PR3': group_1_closing_schema
        }

        self.df['Closing time'] = self.df.apply(lambda x: res_[x['Site (appointment)']][x['Day of the week']], axis=1)
        #self.data['Closing time'] = self.data['Day of the week'].apply(lambda x: 23 if x in ['Sunday','Monday', 'Tuesday', 'Wednesday'] else 24)
        st.info('⚡ Transformation 3/4 done (Adding closing time for each restaurant) - %s seconds | Total rows: %s' % (round((time.time() - start_time)), len(self.df)))
        return self.df
    
    def transformation4(self):
        start_time = time.time()
        def lambda_for_time_after_closing(x):
            # case 1 
            if x['HourEnd'] == x['Closing time']:
                return x['EndMinutes']
            # case 2
            elif x['HourEnd'] > x['Closing time']:
                return ((x['HourEnd'] - x['Closing time'])*60) + int(x['EndMinutes'])
            # case 3
            elif x['HourEnd'] < x['Closing time']:
                return 0
            
        self.df['TotalMinutesAfterClosingTime'] = self.df.apply(lambda_for_time_after_closing, axis=1)
        st.info('⚡ Transformation 4/4 done (Calculating minutes after closing time) - %s seconds | Total rows: %s' % (round((time.time() - start_time)), len(self.df)))
        return self.df
    
    def transform(self):
        self.cleaning()
        self.df = self.transformation1()
        self.df = self.transformation2()
        self.df = self.transformation3()
        self.df = self.transformation4()
        return self.df