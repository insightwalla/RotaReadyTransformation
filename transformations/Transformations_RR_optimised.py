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
        self.df = self.transform()

    def cleaning(self):
        '''
        1. Keep only event type = shift
        '''
        start_time = time.time()
        # Filter and convert to string in one step
        self.df = self.df[self.df["Event type"] == "Shift"].astype(str)
        st.info('Cleaning done - %s seconds' % round((time.time() - start_time)))

    def transformation1(self):
        '''
        Optimized version of transformation1
        '''
        start_time = time.time()
        
        # Batch datetime conversions
        self.df[["Start", "Finish"]] = self.df[["Start", "Finish"]].apply(pd.to_datetime, format='mixed', dayfirst=True)
        
        # Extract hours and minutes in vectorized operations
        self.df["HourStart"] = self.df["Start"].dt.hour
        self.df["HourEnd"] = self.df["Finish"].dt.hour
        self.df["StartMinutes"] = self.df["Start"].dt.minute
        self.df["EndMinutes"] = self.df["Finish"].dt.minute
        
        # Convert numeric columns in one step
        numeric_cols = ["Paid hours", "Unpaid hours"]
        self.df[numeric_cols] = self.df[numeric_cols].astype(float)
        
        # Calculate total hours
        self.df["TotalHours"] = self.df["Paid hours"] + self.df["Unpaid hours"]
        
        # Filter hours
        self.df = self.df[(self.df["TotalHours"] > 0.5) & (self.df["TotalHours"] < 15)]
        
        self.min_hour = 4
        self.max_hour = 27
        
        # Adjust end hours in one operation
        self.df.loc[self.df["HourEnd"] < self.min_hour, "HourEnd"] += 24
        
        # Vectorized minute rounding
        def round_minutes(minutes):
            conditions = [
                minutes <= 8,
                (minutes > 8) & (minutes <= 23),
                (minutes > 23) & (minutes <= 38)
            ]
            choices = [0, 15, 30]
            return np.select(conditions, choices, default=45)
            
        self.df["EndMinutes"] = round_minutes(self.df["EndMinutes"])
        self.df["StartMinutes"] = round_minutes(self.df["StartMinutes"])
        
        st.info('Transformation 1/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df

    def transformation2(self):
        start_time = time.time()
        
        # Pre-generate time columns
        hours = list(range(self.min_hour, self.max_hour + 1))
        minutes = ['00','15','30','45']
        hours_minutes = [f"{hour}:{minute}" for hour in hours for minute in minutes]
        
        # Initialize DataFrame with correct dimensions first
        time_df = pd.DataFrame(0, index=range(len(self.df)), columns=hours_minutes)
        self.df = pd.concat([self.df.reset_index(drop=True), time_df], axis=1)
        
        # Vectorized operations for shift marking
        for idx, row in self.df.iterrows():
            start_col = f"{int(row['HourStart'])}:{str(int(row['StartMinutes'])).zfill(2)}"
            end_col = f"{int(row['HourEnd'])}:{str(int(row['EndMinutes'])).zfill(2)}"
            
            try:
                start_idx = hours_minutes.index(start_col)
                end_idx = hours_minutes.index(end_col)
                if start_idx < end_idx:  # Only set values if valid range
                    self.df.iloc[idx, self.df.columns.get_loc(start_col):self.df.columns.get_loc(end_col)] = 1
                
                # Handle breaks
                if row['Unpaid hours'] > 0 and (row['HourEnd'] - row['HourStart']) >= 6:
                    allowed_break_hours = [9,10,11,14,15,22,23]
                    half_shift = (row['HourEnd'] - row['HourStart'])//2
                    median_hour = row['HourStart'] + half_shift
                    
                    if median_hour in allowed_break_hours:
                        break_col = f"{int(median_hour)}:00"
                        if break_col in self.df.columns:
                            self.df.at[idx, break_col] = 0
                    else:
                        closest_break = min(allowed_break_hours, key=lambda x: abs(x-median_hour))
                        break_col = f"{closest_break}:00"
                        if break_col in self.df.columns:
                            self.df.at[idx, break_col] = 0
                        
            except (ValueError, KeyError):
                continue

        st.info('Transformation 2/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df

    def transformation3(self):
        start_time = time.time()
        
        # Use mapping dictionaries for efficient replacements
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
            'Dishoom Battersea': 'D10',
            'Dishoom Brighton Permit Room': 'PR1',
            'Dishoom Cambridge Permit Room': 'PR2',
            'Dishoom Oxford Permit Room': 'PR3',
        }
        
        # Vectorized operations
        self.df["Site (appointment)"] = "Dishoom " + self.df["Site (appointment)"]
        self.df["Site (appointment)"] = self.df["Site (appointment)"].replace(res_to_rename)
        self.df = self.df[self.df["Site (appointment)"].isin(res_to_rename.values())]
        
        self.df['Day of the week'] = self.df["Start"].dt.day_name()
        
        # Simplified closing time logic using lookup dictionaries
        closing_schemas = {
            'group1': {'Sunday': 23, 'Monday': 23, 'Tuesday': 23, 'Wednesday': 23, 'Thursday': 23, 'Friday': 24, 'Saturday': 24},
            'group2': {'Sunday': 23, 'Monday': 23, 'Tuesday': 23, 'Wednesday': 23, 'Thursday': 24, 'Friday': 24, 'Saturday': 24},
            'group3': dict.fromkeys(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], 23)
        }
        
        restaurant_groups = {
            'D1': 'group1', 'D2': 'group2', 'D3': 'group2', 'D4': 'group1', 'D5': 'group1',
            'D6': 'group3', 'D7': 'group1', 'D8': 'group1', 'D9': 'group1', 'D10': 'group1',
            'PR1': 'group1', 'PR2': 'group1', 'PR3': 'group1'
        }
        
        self.df['Closing time'] = self.df.apply(lambda x: closing_schemas[restaurant_groups[x['Site (appointment)']]][x['Day of the week']], axis=1)
        
        st.info('Transformation 3/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df
    
    def transformation4(self):
        start_time = time.time()
        
        # Vectorized calculation of minutes after closing
        conditions = [
            (self.df['HourEnd'] == self.df['Closing time']),
            (self.df['HourEnd'] > self.df['Closing time']),
            (self.df['HourEnd'] < self.df['Closing time'])
        ]
        
        choices = [
            self.df['EndMinutes'],
            ((self.df['HourEnd'] - self.df['Closing time'])*60 + self.df['EndMinutes']),
            0
        ]
        
        self.df['TotalMinutesAfterClosingTime'] = np.select(conditions, choices, default=0)
        
        st.info('Transformation 4/4 done - %s seconds' % round((time.time() - start_time)))
        return self.df
    
    def transform(self):
        self.cleaning()
        self.df = self.transformation1()
        self.df = self.transformation2()
        self.df = self.transformation3()
        self.df = self.transformation4()
        return self.df