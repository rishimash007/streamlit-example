from google.oauth2 import service_account
from gspread_pandas import Spread,Client
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px

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

    for col in ["Premium","Strike","Total Credit","Cost Avg","Effective Sell Price", "Effective Buy", "Current Price","Total $ Return","Income"]:
        df[col] = df[col].apply(lambda x : float(x.replace("$", "")))

    for col in ["Annualized Return","Effective Return","Premium Return","Margin of error","Margin of error after exercise"]:
        df[col] = df[col].apply(lambda x : float(x.replace("%", "")))
    return df.sort_values(by='Expirary')

st.header(':chart_with_upwards_trend: Cloner Portfolio Tracker')


# Check whether the sheets exists
# what_sheets = worksheet_names()
# #st.sidebar.write(what_sheets)
# ws_choice = st.sidebar.radio('Available worksheets',what_sheets)

# Load data from worksheets
df = load_the_spreadsheet("main")

df = clean(df)

df['Income_TS'] = df["Income"].cumsum()

df = df[df["Consideration"]=='A']

realized_income = df[(df["Exercised?"]=="FALSE")&(df["Days Away"]<=0)]
income = realized_income["Total Credit"].sum()
avg_pct_return = realized_income["Total Credit"].sum()/realized_income["Cost Avg"].sum()/100

realized_income["f_tot"] = realized_income["Cost Avg"]/realized_income["Cost Avg"].sum()
realized_income["f_tot_ret"] = realized_income["Annualized Return"]*realized_income["f_tot"]

avg_annualized_pct_return = realized_income["f_tot_ret"].sum()/100

fig = px.line(df, x='Expirary', y='Income_TS')

fig.update_xaxes(
    rangeslider_visible=True,
    rangeselector=dict(
        buttons=list([
            dict(count=1, label="1m", step="month", stepmode="backward"),
            dict(count=3, label="3m", step="month", stepmode="backward"),
            dict(count=6, label="6m", step="year", stepmode="todate"),
            dict(count=1, label="YTD", step="year", stepmode="todate"),
            dict(step="all")
        ])
    )
)



fig.update_layout(template='plotly_dark',
                  xaxis_rangeselector_font_color='black',
                  xaxis_rangeselector_activecolor='white',
                  xaxis_rangeselector_bgcolor='grey',
                  font_family=st.config.get_option("theme.font"),
                  font_size=24,
                  width=800, height=600,
                  #title=dict(text='Accumulated Income', font=dict(size=24),  automargin=True),

   # font_family="Courier New",
    # font_color="blue",
    # title_font_family="Times New Roman",
    # title_font_color="red",
    xaxis_title="Expiry",
    yaxis_title="Income $",
    legend_title_font_color="white"
)

today = datetime.today().date()

# Add a dotted vertical line for today's date
fig.add_vline(x=today, line_width=5, line_dash="dash", line_color="grey")

fig.update_yaxes(tickformat="$,.0f")


fig.update_traces(
    line_color='#0000ff', line_width=5,
    hoverlabel=dict(font=dict(size=14, family=st.config.get_option("theme.font")))
    
    )






col0, col1= st.columns([3,1])
col0.plotly_chart(fig, use_container_width=True)
col1.metric("Days Since Inception", (realized_income["Expirary"].max().date() - realized_income["Sold"].min().date()).days ,365)
col1.markdown("---")
col1.metric("Realized Total Income", "${:.1f}".format(income), "$1000")
col1.markdown("---")
col1.metric("Realized Avg. Return (ITD)", "{:.2%}".format(avg_pct_return), "{:.2%} (Annualized)".format(avg_annualized_pct_return))

cmap = plt.cm.get_cmap('RdYlGn')

st.dataframe(df.style.background_gradient(cmap=cmap,axis=0))