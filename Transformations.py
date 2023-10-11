# 'dataset' holds the input data for this script
import pandas as pd
import streamlit as st
import time
import numpy as np

class TransformationRotaReady:
    def __init__(self, df):
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
        '''
        start_time = time.time()
        # add HourStart and HourEnd columns after transforming the date columns dayfirst=True
        # change the date format to datetime
        self.df["Start"] = pd.to_datetime(self.df["Start"], format='mixed', dayfirst=True)
        self.df["Finish"] = pd.to_datetime(self.df["Finish"], format = 'mixed', dayfirst=True)
                                               # create a column for paid hours
        
        self.df["HourStart"] = self.df["Start"].dt.hour
        self.df["HourEnd"] = self.df["Finish"].dt.hour 
        # new colum total hours (summing paid and unpaid hours)
        # as float
        self.df["Paid hours"] = self.df["Paid hours"].astype(float)
        self.df["Unpaid hours"] = self.df["Unpaid hours"].astype(float)
        self.df["TotalHours"] = self.df["Paid hours"] + self.df["Unpaid hours"]
        # keep only more than 0.5 hours and less than 15 hours
        self.df = self.df[(self.df["TotalHours"] > 0.5) & (self.df["TotalHours"] < 15)]

        # get min hour from start
        self.min_hour = 4
        # modify end time if end time is less than start time
        #self.df["HourEnd"] = self.df["HourEnd"].apply(lambda x: x+24 if x < self.min_hour else x)
        self.df["HourEnd"] = np.where(self.df["HourEnd"] < self.min_hour, self.df["HourEnd"] + 24, self.df["HourEnd"])
        # get max hour from end
        self.max_hour = self.df["HourEnd"].max()

        # create a minute_end column taking only the minute from the end time
        self.df["EndMinutes"] = pd.to_datetime(self.df["Finish"],format = 'mixed', dayfirst=True).dt.minute
        # round the end minutes to 0 - 15 - 30 - 45 minutes
        # self.df["EndMinutes"] = self.df["EndMinutes"].apply(lambda x: 
        #                                                     0 if x <= 8 
        #                                                     else 15 if x > 8 and x <= 23 
        #                                                     else 30 if x > 23 and x <= 38 
        #                                                     else 45) 
        
        # import numpy as np

        conditions = [
            self.df["EndMinutes"] <= 8,
            (self.df["EndMinutes"] > 8) & (self.df["EndMinutes"] <= 23),
            (self.df["EndMinutes"] > 23) & (self.df["EndMinutes"] <= 38)
        ]
        choices = [0, 15, 30]
        self.df["EndMinutes"] = np.select(conditions, choices, default=45)
        # create a minute_start column taking only the minute from the start time
        self.df["StartMinutes"] = pd.to_datetime(self.df["Start"],format = 'mixed', dayfirst=True).dt.minute
        # round the start minutes to 0 - 15 - 30 - 45 minutes
        # self.df["StartMinutes"] = self.df["StartMinutes"].apply(lambda x:
        #                                                         0 if x <= 8
        #                                                         else 15 if x > 8 and x <= 23
        #                                                         else 30 if x > 23 and x <= 38
        #                                                         else 45)
        
        conditions = [
            self.df["StartMinutes"] <= 8,
            (self.df["StartMinutes"] > 8) & (self.df["StartMinutes"] <= 23),
            (self.df["StartMinutes"] > 23) & (self.df["StartMinutes"] <= 38)
        ]
        choices = [0, 15, 30]
        self.df["StartMinutes"] = np.select(conditions, choices, default=45)
        st.info('Transformation 1/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df

    def transformation2(self):
        start_time = time.time()
        # now need to create a column for each hour and each 15 minutes
        # create a list of hours
        hours = list(range(self.min_hour,self.max_hour+1))
        # create a list of minutes
        minutes = ['00','15','30','45']
        # create a list of hours and minutes
        hours_minutes = [str(hour)+":"+str(minute) for hour in hours for minute in minutes]
        # create a column for each hour and each 15 minutes
        self.df = pd.concat([self.df, pd.DataFrame(0, index=self.df.index, columns=hours_minutes)], axis=1)
        # or simply
        #self.df[hours_minutes] = 0
        # populate the columns with 1 if the shift is in that hour and minute
        for index, row in self.df.iterrows():
            #get start hour and end hour
            start_hour = row["HourStart"]
            end_hour = row["HourEnd"]
            min_end = row["EndMinutes"]
            for hour_minute in hours_minutes:
                # check if the hour is between start and end
                hour_to_populate = int(hour_minute.split(":")[0])
                minute_to_populate = int(hour_minute.split(":")[1])
                if start_hour < end_hour:
                    if hour_to_populate >= start_hour and hour_to_populate < end_hour:
                        self.df.loc[index, hour_minute] = 1
                    elif hour_to_populate == end_hour and minute_to_populate <= min_end:
                        self.df.loc[index, hour_minute] = 1 

        st.info('Transformation 2/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df

    def new_transformation2(self):
        start_time = time.time()
        # create a 2D grid of hours and minutes
        hours = np.arange(self.min_hour, self.max_hour+1)
        minutes = np.array([0, 15, 30, 45])
        # reshape the grid into a 1D array of strings
        hours_minutes = [f"{hour:02d}:{minute:02d}" for hour in hours for minute in minutes]        # create a column for each hour and each 15 minutes
        self.df[hours_minutes] = 0
        # populate the columns with 1 if the shift is in that hour and minute
        for index, row in self.df.iterrows():
            #get start hour and end hour
            start_hour = row["HourStart"]
            end_hour = row["HourEnd"]
            min_end = row["EndMinutes"]
            for hour_minute in hours_minutes:
                # check if the hour is between start and end
                hour_to_populate = int(hour_minute.split(":")[0])
                minute_to_populate = int(hour_minute.split(":")[1])
                if start_hour < end_hour:
                    if hour_to_populate >= start_hour and hour_to_populate < end_hour:
                        self.df.loc[index, hour_minute] = 1
                    elif hour_to_populate == end_hour and minute_to_populate <= min_end:
                        self.df.loc[index, hour_minute] = 1 

        st.info('Transformation 2/4 done - %s seconds' % round((time.time() - start_time)))
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
            'Dishoom Canary Wharf': 'D9'
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
                return ((x['HourEnd'] - x['Closing time'])*60) + x['EndMinutes']
            # case 3
            elif x['HourEnd'] < x['Closing time']:
                return 0
            
        self.df['TotalMinutesAfterClosingTime'] = self.df.apply(lambda_for_time_after_closing, axis=1)
        st.info('Transformation 4/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df
    
    def transform(self):
        self.cleaning()
        self.df = self.transformation1()
        self.df = self.new_transformation2()
        self.df = self.transformation3()
        self.df = self.transformation4()
        return self.df


