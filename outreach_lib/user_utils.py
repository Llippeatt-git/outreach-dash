'''Functions for loading and preprocessing the data, specific to
the user's data. If you are adapting the dashboard as your own,
you likely need to alter these functions.
'''
import os
import glob
import numpy as np
import pandas as pd
import datetime

from outreach_lib import utils


def load_data(data, config):
    '''Modify this!
    
    This is the main function for loading the data
    (but save cleaning and preprocessing for later).
    
    For compatibility with the existing
    dashboard, this function should accept a pandas DataFrame and a
    config dictionary and return the same.

    Args:
        config (dict): The configuration dictionary, loaded from a YAML file.

    Returns:
        raw_df (pandas.DataFrame): The data to be used in the dashboard.
        config (dict): The configuration dictionary, loaded from a YAML file.
    '''

    ##########################################################################
    # Filepaths
    if data is None:
        input_dir = os.path.join(config['data_dir'], config['input_dirname'])

        def get_fp_of_most_recent_file(pattern):
            '''Get the filepath of the most-recently created file matching
            the pattern. We just define this here because we use it twice.

            Args:
                pattern (str): The pattern to match.

            Returns:
                fp (str): The filepath of the most-recently created file
                    matching the pattern.
            '''
            fps = glob.glob(pattern)
            ind_selected = np.argmax([os.path.getctime(_) for _ in fps])
            return fps[ind_selected]

        data_pattern = os.path.join(input_dir, config['website_data_file_pattern'])
        data_fp = get_fp_of_most_recent_file(data_pattern)
    else:
        data_fp = data

    ### outreach specific
    if data is None:
        head_col = 0
    else:
        head_col = 1

    website_df = pd.read_csv(data_fp, header=head_col, encoding_errors='ignore')
    
    #website_df['id'] = website_df.index
    website_df.set_index(np.arange(len(website_df)), inplace=True)
    #website_df.set_index('Calendar Group', inplace=True)

    #testing
    
    # website_df = pd.read_csv(data_fp, parse_dates=['Date',])
    # website_df.set_index('id', inplace=True)
    
    # # Load press data
    # press_df = pd.read_excel(press_office_data_fp)
    # press_df.set_index('id', inplace=True)

    # # Combine the data
    # raw_df = website_df.join(press_df)
    return website_df, config


def clean_data(raw_df: pd.DataFrame, config):
    '''Modify this!
    
    This is the main function for cleaning the data,
    i.e. getting rid of NaNs, dropping glitches, etc.
    
    For compatibility with the existing
    dashboard, this function should accept a pandas DataFrame and a
    config dictionary and return the same.

    Args:
        raw_df (pandas.DataFrame): The raw data to be used in the dashboard.
        config (dict): The configuration dictionary, loaded from a YAML file.

    Returns:
        cleaned_df (pandas.DataFrame): The cleaned data.
        config (dict): The (possibly altered) configuration dictionary.
    '''

    #for str_columns in ['Start Date', 'End Date']:
    #    raw_df[str_columns] = pd.to_datetime(raw_df[str_columns], errors='coerce')
    
    # Drop rows where 'Date' year is 1970

    cleaned_df = raw_df[raw_df['Date'] != 0]
    ## specific naming conventions

    cleaned_df = cleaned_df.rename(columns={'Event/Activity Title ':'Event Title',
                       'Type of Event':'Event Type',
                       'Grad Students (if none, enter "None")': 'Grad Students',
                       'Postdocs  (if none, enter "None")': 'Postdocs',
                       'Faculty  (if none, enter "None")':'Faculty',
                       'Staff (if none, enter "None")':'Staff',
                       'Total # of Attendees (approximate)': 'Total Attendees',
                       'Funding Source (please list all funding sources for the event, including CIERA, and/or specific grants if you know them)': 'Funding Source'
                        })
    
    # Drop weird articles---ancient ones w/o a title or year
    # Timestamp,Event/Activity Title ,Type of Event,Short description,Date,"Location (Venue, City, State, as applicable)","Funding Source (please list all funding sources for the event, including CIERA, and/or specific grants if you know them)","Grad Students (if none, enter ""None"")","Postdocs  (if none, enter ""None"")","Faculty  (if none, enter ""None"")","Staff (if none, enter ""None"")",Primary Audience Type,Is this event focused on an underrepresented group in STEM? ,Total # of Attendees (approximate),Additional description of audience,Feedback from Audience,"Contact Info (e.g. name of organization, name of contact person, email address, etc.)",Notes/Comments on partners,Final Thoughts
    cleaned_df.dropna(
        axis='rows',
        how='any',
        subset=['Event Title', 'Event Type', 'Date',],  
        inplace=True,
    )
    # # Drop drafts
    # cleaned_df = raw_df.drop(
    #     raw_df.index[raw_df['Date'].dt.year == 1970],
    #     axis='rows',
    # 
    
    
    # Get rid of HTML ampersands
    for str_column in ['Funding Source',]:
        cleaned_df[str_column] = cleaned_df[str_column].str.replace('&amp;', '&')


    AVERAGE_NUM_ATTENDEES = 10
    def resolve_numerical(entry):
        try:
            entry = int(entry)
        except:
            entry = AVERAGE_NUM_ATTENDEES
        
        return entry
        
    cleaned_df['Total Attendees'] = cleaned_df['Total Attendees'].apply(resolve_numerical)
    # Handle NaNs, rounding, and other numerical errors
    #cleaned_df[columns_to_fill] = cleaned_df[columns_to_fill].apply(round)
    cleaned_df.fillna(value='N/A', inplace=True)

    return cleaned_df, config


def preprocess_data(cleaned_df, config):
    '''Modify this!
    
    This is the main function for doing preprocessing, e.g. 
    adding new columns, renaming them, etc.
    
    For compatibility with the existing
    dashboard, this function should accept a pandas DataFrame and a
    config dictionary and return the same.

    Args:
        cleaned_df (pandas.DataFrame): The raw data to be used in the dashboard.
        config (dict): The configuration dictionary, loaded from a YAML file.

    Returns:
        processed_df (pandas.DataFrame): The processed data.
        config (dict): The (possibly altered) configuration dictionary.
    '''

    preprocessed_df = cleaned_df.copy()

    # Get the year, according to the config start date
    #preprocessed_df['Fiscal Year'] = utils.get_year(
    #    preprocessed_df['Date'], config['start_of_year']
    #)

    # Tweaks to the press data
    #if 'Title (optional)' in preprocessed_df.columns:
    #    preprocessed_df.drop('Title (optional)', axis='columns', inplace=True)
    #for column in ['Date']:
    #    preprocessed_df[column] = preprocessed_df[column].astype('Int64')    



    #Now explode the data
    '''
    groupings = config['groupings'] + config['metrics_options']
    for group_by_i in groupings:
        preprocessed_df[group_by_i] = preprocessed_df[group_by_i].str.split(',')
        preprocessed_df = preprocessed_df.explode(group_by_i)
        preprocessed_df[group_by_i] = preprocessed_df[group_by_i].str.strip()
    '''
    
    # Exploding the data results in duplicate IDs,
    # so let's set up some new, unique IDs.
    preprocessed_df['id'] = preprocessed_df.index
    preprocessed_df.set_index(np.arange(len(preprocessed_df)), inplace=True)

    preprocessed_df['Date'] = pd.to_datetime(preprocessed_df['Date'], errors='coerce')


    
    def legacy(date):
        if date.year < 2014:
            return "LEGACY"
        else:
            return "CURRENT"
    
    preprocessed_df['Legacy'] = preprocessed_df['Date'].apply(legacy)

    # This flag exists just to demonstrate you can modify the config
    # during the user functions
    config['data_preprocessed'] = True

    return preprocessed_df, config
