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
