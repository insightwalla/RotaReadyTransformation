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

class TransformationFourth:
    def __init__(self, df):
        self.df = df

    def cleaning(self):
        #pass
        # rename columns 
        '''
        change employee number to ID
        '''
        self.df = self.df.rename(columns={'Employee Number': 'ID'})
        # craete a new columns calle HR ID
        self.df['HR ID'] = self.df['ID']
        # craete a new columns calle Payroll ID
        self.df['Payroll ID'] = self.df['ID']
        self.df = self.df.rename(columns={'First Name': 'First name'})
        self.df = self.df.rename(columns={'Surname': 'Last name'})
        # craete a event type column
        self.df['Event type'] = 'Shift'

        # change Paid/Actual StartTime1 to Start
        self.df = self.df.rename(columns={'ActualStartTime1': 'Start'})
        # change Paid/Actual StopTime1 to Finish
        self.df = self.df.rename(columns={'ActualStopTime1': 'Finish'})

        # remove forecast columns
        self.df = self.df.drop(columns=['Rota/Forecast StartTime1', 'Rota/Forecast StopTime1', 'Rota/Forecast StartTime2', 'Rota/Forecast StopTime2', 'Rota/Forecast Hours'])
        # delete paid/actual columns
        self.df = self.df.drop(columns=['Paid/Actual StartTime1', 'Paid/Actual StopTime1', 'Paid/Actual StartTime2', 'Paid/Actual StopTime2'])
        # rename 
        self.df = self.df.rename(columns={'Paid/Actual Hours': 'Paid hours'})

        # rename Home to Site (appointment)
        self.df = self.df.rename(columns={'Home': 'Site (appointment)'})

        # create department column from division
        self.df['Department (appointment)'] = self.df['Division']

        # site attribution is the same as site appointment
        self.df['Site (attribution)'] = self.df['Site (appointment)']

        # rename job title to shift type
        self.df = self.df.rename(columns={'Job Title': 'Shift type'})

        # department attribution is the same as department appointment
        self.df['Department (attribution)'] = self.df['Department (appointment)']

        self.df['Unpaid hours'] = 0
        self.df['Base pay'] = 0
        self.df['Accrued holiday'] = 0
        self.df['Taxes'] = 0
        self.df['Wage uplift'] = 0
        pay_rate = 10
        self.df['Total cost'] = self.df['Paid hours'] * pay_rate


        # order_colums
        ordered_cols = [
            'ID',
            'HR ID',
            'Payroll ID',
            'First name',
            'Last name',
            'Site (appointment)',
            'Department (appointment)',
            'Event type',
            'Shift type',
            'Site (attribution)',
            'Department (attribution)',
            'Start',
            'Finish',
            'Paid hours',
            'Unpaid hours',
            'Base pay',
            'Accrued holiday',
            'Taxes',
            'Wage uplift',
            'Total cost',
            'Shift date',
        ]
        self.df = self.df[ordered_cols]

    def transformation1(self):
        # change site appointment skipping the first word
        self.df['Site (appointment)'] = self.df['Site (appointment)'].str.split(' ').str[1:]
        # transform in string
        self.df['Site (appointment)'] = self.df['Site (appointment)'].astype(str).replace('\[|\]|\'', '', regex=True)
        # take off commas
        self.df['Site (appointment)'] = self.df['Site (appointment)'].str.replace(',', '')
        # site attribution is the same as site appointment
        self.df['Site (attribution)'] = self.df['Site (appointment)']
        return self.df
    
    def tranformation2(self):
        # now need to merge the date with the time
        # case 1 - if start_hour < than finish_hour
        # create a hour_start column
        # transform in string
        self.df['HourStart'] = self.df['Start'].str.split(':').str[0]
        # create a hour_end column
        self.df['HourEnd'] = self.df['Finish'].str.split(':').str[0]

        def lambda_for_start_date_time(x):
                return str(x['Shift date']) + ' ' + str(x['Start'])
        
        def lambda_for_end_date_time(x):
                if x['HourStart'] < x['HourEnd']:
                    return str(x['Shift date']) + ' ' + str(x['Finish'])
                else:
                    new_date = pd.to_datetime(x['Shift date'], dayfirst=True) + pd.DateOffset(days=1)
                    # day first is to make sure that the date is in the right format
                    return str(new_date) + ' ' + str(x['Finish'])

        self.df['Start'] = self.df.apply(lambda x: lambda_for_start_date_time(x), axis=1)
        self.df['Finish'] = self.df.apply(lambda x: lambda_for_end_date_time(x), axis=1)

        # filter out empty paid hours
        self.df = self.df[self.df['Paid hours'] > 0]
        return self.df
    
    def transformation3(self):
        # need to map Department (appointment) to the right department
        maps_deps = {
                'Servers' : 'Servers',
                'FOH Management' : 'Management',
                'BOH - Demi Chef De Partie' : 'BOH',
                'BOH Managers' : 'BOH Managers',
                'Expeditor' : 'Runners',
                'Hosts' : 'Hosts',
                'Bartenders' : 'Bartenders',
                'Food and drinks Runners' : 'Runners',
                'Bar Support' : 'Bartenders',
                'BOH - Senior Chef De Partie' : 'BOH',
                'BOH - Chef De Partie' : 'BOH' ,
                'Dishoom at Home - Bar' : 'Babu House',
                'FOH Dev Training ' : 'FOH Training',
                'Dishoom at Home' : 'Babu House' ,
                'Cocktail Servers' : 'Bartenders',
                'FOH training' : 'FOH Training' ,
                'BOH Training' : 'BOH Training',
        }
        self.df['Department (appointment)'] = self.df['Department (appointment)'].map(maps_deps)
        # add the site appintment between parenthesis in the department appointment
        self.df['Department (appointment)'] = self.df['Department (appointment)'] + ' (' + self.df['Site (appointment)'] + ')'
        # department attribution is the same as department appointment
        self.df['Department (attribution)'] = self.df['Department (appointment)']

        # take off the last 3 columns
        self.df = self.df.iloc[:, :-3]
        return self.df

    def transform(self):
        self.cleaning()
        self.df = self.transformation1()
        self.df = self.tranformation2()
        self.df = self.transformation3()

        return self.df

class TransformationRotaReady:
    def __init__(self, df, with_breaks=True):
        self.with_breaks = with_breaks
        self.df = df
        self.df = self.transform()

    def cleaning(self):
        '''
        1. Keep only event type = shift
        '''
        start_time = time.time()
        # keep only event type = shift
        self.df = self.df[self.df["Event type"] == "Shift"]
        # transform all in string
        self.df = self.df.astype(str)
        st.info('Cleaning done - %s seconds' % round((time.time() - start_time)))

    def transformation1(self):
        '''
        1. Tranform Start and finish to dates 
        2. Decompose the Start and End time to get minutes and hours
        3.
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
        self.max_hour = self.df["HourEnd"].max()
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
        st.info('Transformation 1/4 done - %s seconds' % round((time.time() - start_time)))
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

        st.info('Transformation 2/4 done - %s seconds' % round((time.time() - start_time)))
        st.write(self.df)
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
            'Dishoom Shoreditch': 'D2',
            'Dishoom Covent Garden': 'D1',
            'Dishoom Kensington': 'D6',
            'Dishoom Kings Cross': 'D3',
            'Dishoom Carnaby': 'D4',
            'Dishoom Manchester': 'D7',
            'Dishoom Edinburgh': 'D5',
            'Dishoom Birmingham': 'D8',
            'Dishoom Canary Wharf': 'D9',

            'Dishoom Brighton Permit Room': 'PR1',
            'Dishoom Cambridge Permit Room' : 'PR2',
            'Dishoom Oxford Permit Room': 'PR3',
            'Dishoom Battersea': 'D10',
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
        st.info('Transformation 3/4 done - %s seconds' % round((time.time() - start_time)))
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
        st.info('Transformation 4/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df
    
    def transform(self):
        self.cleaning()
        self.df = self.transformation1()
        self.df = self.transformation2()
        self.df = self.transformation3()
        self.df = self.transformation4()
        return self.df

class TransformationFourtDOUBLE:
    def __init__(self, df):
        self.df = df
        self.df = self.transform()

    def cleaning(self):
        # take off if all the row is nan
        self.df = self.df[self.df['Home'].notna()]

    def transformation1(self):

        '''
        1. Divide the single shifts from the double shifts
        2.
        
        '''
        # if actualstartime2 is not null then it is a double shift
        double_shifts_df = self.df[self.df['ActualStartTime2'].notna()]

        am_shifts = double_shifts_df.copy()

        
        st.write("AM Shifts before transformation")   
        st.write(am_shifts)     

        pm_shifts = double_shifts_df.copy()
        def adjust_am_shift(am_shifts):
            # set the second part to to np.nan
            am_shifts['ActualStartTime2'] = np.nan
            am_shifts['ActualStopTime2'] = np.nan
            return am_shifts
        #st.write('AM Shifts after transformation')
        am_shifts = adjust_am_shift(am_shifts)
        #st.write(am_shifts)
        #st.write(len(am_shifts))

        def adjust_pm_shifts(pm_shifts):
            # assign the actual start time 2 to the actual start time 1
            pm_shifts['ActualStartTime1'] = pm_shifts['ActualStartTime2']
            # assign the actual stop time 2 to the actual stop time 1
            pm_shifts['ActualStopTime1'] = pm_shifts['ActualStopTime2']

            # set the actual start time 2 to null
            pm_shifts['ActualStartTime2'] = np.nan
            # set the actual stop time 2 to null
            pm_shifts['ActualStopTime2'] = np.nan
            return pm_shifts
        
        
        pm_shifts = adjust_pm_shifts(pm_shifts)
        all_shifts = pd.concat([am_shifts, pm_shifts])
        self.df = all_shifts
        # add date from start
        self.df = all_shifts

        return self.df
    
    def transform(self):
        self.cleaning()
        self.df = self.transformation1()
        return self.df
