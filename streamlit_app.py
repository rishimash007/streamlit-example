from google.oauth2 import service_account
from gspread_pandas import Spread,Client
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

# Create a Google Authentication connection object
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes = scope)
client = Client(scope=scope,creds=credentials)
spreadsheetname = "Option Tracker"
spread = Spread(spreadsheetname,client = client)

sh = client.open(spreadsheetname)
#worksheet_list = sh.worksheets()


# Get the sheet as dataframe
def load_the_spreadsheet(spreadsheetname):
    worksheet = sh.worksheet(spreadsheetname)
    df = pd.DataFrame(worksheet.get_all_records())
    return df

def convert_to_date(date_integer):
    year = 2000 + date_integer // 10000     # Convert "15" to 2015
    month = (date_integer // 100) % 100  # Extract the month, which is "08"
    day = (date_integer % 100) # Extract the day, which is "23"

    # Create a datetime object
    date_datetime = datetime(year, month, day)
    return date_datetime

def clean(df):
    df["Expirary"] = df["Expirary"].apply(lambda x : convert_to_date(x))
    df["Sold"] = df["Sold"].apply(lambda x : pd.to_datetime(x))

    for col in ["Premium","Strike","Total Credit","Cost Avg"]:
        df[col] = df[col].apply(lambda x : float(x.replace("$", "")))

    for col in ["Annualized Return"]:
        df[col] = df[col].apply(lambda x : float(x.replace("%", "")))
    return df

st.header(':chart_with_upwards_trend: Cloner Portfolio Tracker')

# Check whether the sheets exists
# what_sheets = worksheet_names()
# #st.sidebar.write(what_sheets)
# ws_choice = st.sidebar.radio('Available worksheets',what_sheets)

# Load data from worksheets
df = load_the_spreadsheet("main")

df = clean(df)

df = df[df["Consideration"]=='A']

realized_income = df[(df["Exercised?"]=="FALSE")&(df["Days Away"]<=0)]
income = realized_income["Total Credit"].sum()
avg_pct_return = realized_income["Total Credit"].sum()/realized_income["Cost Avg"].sum()/100

realized_income["f_tot"] = realized_income["Cost Avg"]/realized_income["Cost Avg"].sum()
realized_income["f_tot_ret"] = realized_income["Annualized Return"]*realized_income["f_tot"]

avg_annualized_pct_return = realized_income["f_tot_ret"].sum()/100


col0, col1, col2= st.columns(3)
col0.metric("Days Since Inception", (realized_income["Expirary"].max().date() - realized_income["Sold"].min().date()).days ,365)
col1.metric("Realized Total Income", "${:.1f}".format(income), "$1000")
col2.metric("Realized Avg. Return (ITD)", "{:.2%}".format(avg_pct_return), "{:.2%} (Annualized)".format(avg_annualized_pct_return))


st.table(df)