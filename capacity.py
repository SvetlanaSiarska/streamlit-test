import streamlit as st
import pandas as pd
import plotly.express as px

# Specify the path to the CSV file
csvFilePath = 'capacity.csv'
skip_r = 2


def calculate_start(row):
    start = None
    for key, value in row.to_dict().items():
        if 'Sprint' in key and start is None:
            if value is not None and value > 0:
                start = edited_df.loc[0][key]
    return start


def calculate_finish(row):
    end = None
    counter = 0
    estimated = 0
    start = None
    for key, value in row.to_dict().items():
        if 'Estimated' in key:
            estimated = value
        if 'Sprint' in key and counter < estimated:
            if value is not None:
                counter = counter + value
                start = edited_df.loc[0][key]
                end = pd.to_datetime(start) + \
                    pd.to_timedelta(13, unit='D')
    return end


def show_tasks():
    tasks_cols = [col for col in edited_df.columns if 'Task' in col or
                  'All' in col or 'Estimated' in col or 'Sprint' in col]

    # Add new column to the DataFrame
    starts = []
    finishes = []
    tasks_df = edited_df.iloc[2:][tasks_cols]
    sprint_cols = [col for col in tasks_df.columns if 'Sprint' in col]
    start_index = tasks_df.columns.get_loc(sprint_cols[0])

    for index, row in tasks_df.iterrows():
        starts.append(calculate_start(row))
        finishes.append(calculate_finish(row))
    tasks_df.insert(start_index, "Start", starts)
    tasks_df.insert(start_index+1, "Finish", finishes)

    st.experimental_data_editor(tasks_df)
    fig = px.timeline(tasks_df, x_start="Start", x_end="Finish", y="Task")

    # Display the Gantt chart using Streamlit
    st.plotly_chart(fig)


def add_row():
    new_row = ['New task']
    columns_count = edited_df.shape[1]
    for i in range(columns_count-1):
        new_row.append(0.0)
    edited_df.loc[len(edited_df)] = new_row


def save_data_to_csv():
    # Save the DataFrame to a CSV file
    edited_df.to_csv(csvFilePath, index=False)


def recalculate():
    rows_count = len(edited_df.index)
    columns_count = edited_df.shape[1]

    # Get all sprint columns
    sprint_cols = [col for col in edited_df.columns if 'Sprint' in col]
    first_sprint_col_index = edited_df.columns.get_loc(sprint_cols[0])
    sprint_cols_indexex = []

    for index, sprint_col in enumerate(sprint_cols):
        sprint_col_index = edited_df.columns.get_loc(sprint_col)
        sprint_col_next = edited_df.columns.get_loc(
            sprint_cols[index+1]) if (index+1 < len(sprint_cols)) else columns_count
        sprint_cols_indexex.append(sprint_col_index)

        # calculate the capacity for all tasks (PT) in current sprint -> Sprint column
        pt = edited_df.iloc[skip_r:rows_count, sprint_col_index+1:sprint_col_next].multiply(
            edited_df.iloc[0][:]).sum(axis=1)

        for index, row in edited_df.iterrows():
            if index > (skip_r-1):
                edited_df.iloc[index, sprint_col_index] = round(pt[index], 1)

    # calculate the capacity for all tasks over all sprints -> Start column
    pt = edited_df.iloc[skip_r:rows_count, sprint_cols_indexex].sum(axis=1)
    for index, row in edited_df.iterrows():
        if index > (skip_r-1):
            edited_df.iloc[index, first_sprint_col_index -
                           1] = round(pt[index], 1)

    # calculate the Booked row
    sum = edited_df.iloc[skip_r:rows_count, 1:].sum()
    for column in edited_df.columns[1:]:
        edited_df.loc[1, column] = round(sum[column], 1)

    show_tasks()


print('read from file')
df = pd.read_csv(csvFilePath)
selectbox_options = [col for col in df.columns if 'Sprint' in col]
selectbox_options.insert(0, 'All')

# option = st.selectbox(' ', selectbox_options)
# if option and option != 'All':
#   sprint_col = df.columns.get_loc(option)
#  df.style.hide([0, 1], axis="columns")

edited_df = st.experimental_data_editor(df, key="capacity")


# Read the CSV file using pandas
if "df_value" not in st.session_state:
    st.session_state.df_value = edited_df

# add_button = st.button('Add Task')
# if add_button and edited_df is not None:
#   add_row()
#  save_data_to_csv()

refresh_button = st.button('Recalculate')
if refresh_button and edited_df is not None:
    recalculate()
    save_data_to_csv()


if edited_df is not None and not edited_df.equals(st.session_state["df_value"]):
    # This will only run if
    # 1. Some widget has been changed (including the dataframe editor), triggering a
    # script rerun, and
    # 2. The new dataframe value is different from the old value

    edited_df.to_csv(csvFilePath, index=False)
    # st.success('Data saved to ' + csvFilePath)
    st.session_state["df_value"] = edited_df

print('****************')
