
import streamlit as st
import yfinance as yf
import pandas as pd
import os

st.markdown("# Research Factory")
st.sidebar.markdown("# Menu")
st.markdown("## Stocks")

# Check if CSV exists; if not, create a default one
csv_file = 'old_code/stocks_lists.csv'
if not os.path.exists(csv_file):
    # Multiple static stock lists
    stocks_lists = {
        'Semiconductors': ['AMD', 'INTC', 'NVDA', 'AVGO', 'ASML', 'TSM'],
        'Observability': ['NEWR','DDOG','SUMO','SPLK','ESTC','DT','MFGP'],
        'Cloud': ['IBM', 'AMZN', 'MSFT', 'NET', 'GOOG','BABA'],
    }
    pd.DataFrame.from_dict(stocks_lists, orient='index').T.to_csv(csv_file)
else:
    stocks_lists = pd.read_csv(csv_file, index_col=0).to_dict(orient='list')
    for key in stocks_lists:
        stocks_lists[key] = [x for x in stocks_lists[key] if isinstance(x, str)]

# Dropdown widget for stock list selection
selected_stock_list = st.selectbox('Select stock category', list(stocks_lists.keys()))

# Let user add a new category
st.sidebar.markdown("### Add New Category")
new_category = st.sidebar.text_input("Add a new stock category")
new_stocks = st.sidebar.text_area("Add stocks (comma-separated)").split(',')
if st.sidebar.button('Add Category') and new_category and new_stocks:
    stocks_lists[new_category] = [stock.strip() for stock in new_stocks if stock]
    # Save updated stocks_lists to CSV
    pd.DataFrame.from_dict(stocks_lists, orient='index').T.to_csv(csv_file)

# Let user edit or delete an existing category
st.sidebar.markdown("### Edit/Delete Category")
edit_category = st.sidebar.selectbox("Select a category to edit or delete", list(stocks_lists.keys()), key='edit_category')
edit_new_category = st.sidebar.text_input("Edit category name", edit_category)
edit_new_stocks = st.sidebar.text_area("Edit stocks", ', '.join(stocks_lists[edit_category]))

if st.sidebar.button('Update Category'):
    # Delete old category and add updated one
    del stocks_lists[edit_category]
    stocks_lists[edit_new_category] = [stock.strip() for stock in edit_new_stocks.split(',') if stock]
    pd.DataFrame.from_dict(stocks_lists, orient='index').T.to_csv(csv_file)
    # Sync the main dropdown after an update
    selected_stock_list = edit_new_category

if st.sidebar.button('Delete Category'):
    del stocks_lists[edit_category]
    pd.DataFrame.from_dict(stocks_lists, orient='index').T.to_csv(csv_file)
    # If the deleted category was the one being displayed, switch to another one
    if edit_category == selected_stock_list:
        selected_stock_list = next(iter(stocks_lists))

# Get the selected stock list
selected_stocks = stocks_lists.get(selected_stock_list, [])

# Set the default date range to Jan 1, 2023 to today
start_date, end_date = st.date_input('Select time range', value=[pd.to_datetime('2023-01-01'), pd.to_datetime('today')], min_value=pd.to_datetime('2000-01-01'), max_value=pd.to_datetime('today'))

# Convert start_date and end_date to string format
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

# Function to fetch stock data from Yahoo Finance
def get_stocks_data(stock, start_date, end_date):
    data = yf.download(stock, start=start_date, end=end_date)
    data.reset_index(inplace=True)
    data = data[['Date', 'Adj Close']].rename(columns={'Adj Close': stock})
    if not data.empty:  # Check if the DataFrame is not empty
        data[stock] = (data[stock] / data[stock].iloc[0] - 1.0) * 100.0  # Calculate percentage change
    return data

# Get the data and plot the line chart for each stock in the selected category
if selected_stocks:
    data = pd.DataFrame()
    for stock in selected_stocks:
        if stock:  # Ensure the stock ticker is not empty or None
            stock_data = get_stocks_data(stock, start_date_str, end_date_str)
            if not stock_data.empty:
                if data.empty:
                    data = stock_data
                else:
                    data = pd.merge(data, stock_data, on='Date', how='inner')

    if not data.empty:  # Check if the DataFrame is not empty
        #st.line_chart(data.set_index('Date'), use_container_width=True)
        st.line_chart(data.set_index('Date'), use_container_width=True, height=600)
