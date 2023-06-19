from constants import ZSCORE_THRESH, USD_MIN_COLLATERAL, USD_PER_TRADE, TOKEN_FACTOR_10, ZSC0RE_EXIT_THRESHOLD
from public import get_prices
import matplotlib.pyplot as plt
from private import check_if_any_open_positions
from utils import format_number
from bot_agent import Bot
from cointegration import calculate_zscore,calculate_cointegration
from pandas_datareader import data as pdr
import yfinance as yf
import pandas as pd
import numpy as np 
import pprint as pprint
import json
import statsmodels.api as sm
import seaborn as sns
import os
#the coint library here most importantl\y has a p-val;ue for the hypothesis test where the null hypothesis is that the 2 variables are not cointegrated
from statsmodels.regression.rolling import RollingOLS
from datetime import datetime, timedelta

yf.pdr_override()

def get_data_backtest(client):
    # will test the pair of XTZ-USD AND BTC-USD PAIR first 
    #subsequently once code written, will run for all cointegrated pairs in the excel file
    
   
    cointegrated_pairs_df = pd.read_csv("cointegrated_pairs.csv")
    #will use yfinance to get financial data for each coin in the cointegrated excel file
    #pandas-datareader allows us to import in the data as a pandas dataframe


    returns_files = []
    
    overall_arr = []
    for index, row in (cointegrated_pairs_df.iterrows()):
        coin_1 = row["series_1"]
        coin_2 = row["series_2"]
        
        #create dataframe for each coin with date,price,
        #use 5 years of data to backtest
        ini_time_for_now = datetime.now()
        print(coin_1)

    
    # Calculating past dates
    # for two years
        past_date_before_2yrs = ini_time_for_now - \
                        timedelta(days = 1825)
        end_time = datetime.now()
        
        coin_1_df =  pdr.get_data_yahoo(coin_1, start=past_date_before_2yrs.strftime('%Y-%m-%d'), end=end_time.strftime('%Y-%m-%d'))

        #coin_1_df['Date'] = pd.to_datetime(coin_1_df['Date'], format='%Y-%m-%d')
        #coin_1_df['Date'] = pd.to_datetime(coin_1_df['Date'].dt.strftime('%Y-%m-%d'))


        coin_2_df = pdr.get_data_yahoo(coin_2, start=past_date_before_2yrs.strftime('%Y-%m-%d'), end=end_time.strftime('%Y-%m-%d'))
        #coin_2_df['Date'] = pd.to_datetime(coin_2_df['Date'], format='%Y-%m-%d')
        #coin_2_df['Date'] = pd.to_datetime(coin_2_df['Date'].dt.strftime('%Y-%m-%d'))

        #combine the 2 dataframes together
        combined_prices_df = pd.DataFrame(index=coin_1_df.index)
        combined_prices_df['coin_1_prices'] = coin_1_df['Close'].astype(float)
        combined_prices_df['coin_2_prices'] = coin_2_df['Close'].astype(float)
        combined_prices_df = combined_prices_df.dropna()

        #add the hedge_ratio to the combined_prices_df
        model = sm.OLS(
            combined_prices_df['coin_1_prices'],
            sm.add_constant(combined_prices_df['coin_2_prices']),
        
        )
        rres = model.fit()
        params = rres.params.copy()
       
        
        # Construct the hedge ratio and eliminate the first 
        # lookback-length empty/NaN period
        combined_prices_df['hedge_ratio'] = params[0]
        combined_prices_df['spread'] = (
            combined_prices_df['coin_1_prices'] - (combined_prices_df['hedge_ratio'] * combined_prices_df['coin_2_prices'])
        )
        combined_prices_df['zscore'] = calculate_zscore(combined_prices_df['spread'])
        combined_prices_df.dropna(inplace=True)
  

        #creating the trading strategy need to create when to enter exit / long and short 

        #generating when to be enter and when to exit
        combined_prices_df['longs'] = ((combined_prices_df['zscore']) <= -ZSCORE_THRESH)*1.0
        combined_prices_df['shorts'] = ((combined_prices_df['zscore']) >= ZSCORE_THRESH)*1.0
        combined_prices_df['exit'] = (np.abs(combined_prices_df['zscore']) <= ZSC0RE_EXIT_THRESHOLD)*1.0
        
        #for each row, generate either a long / short / exit 
        combined_prices_df['long_pos'] = 0.0
        combined_prices_df['short_pos'] = 0.0
        long_signal = 0.0
        short_signal = 0.0
        for index, rows in enumerate(combined_prices_df.iterrows()):
            
            longs = rows[1]['longs']
            shorts = rows[1]['shorts']
            exit_signal = rows[1]['exit']
            if longs == 1.0:
                long_signal = 1.0
            if shorts == 1.0:
                short_signal = 1.0
            if exit_signal == 1.0:
                long_signal = 0.0
                short_signal = 0.0
            combined_prices_df.iloc[index]['long_pos'] = long_signal
            combined_prices_df.iloc[index]['short_pos'] = short_signal


        
        #generate portfolio returns
        #need to create the market value for each row combining the respective positions and the market value of each coin
        portfolio = pd.DataFrame(index=combined_prices_df.index)
        #-1,0,1
        portfolio['Date'] = portfolio.index
        portfolio['positions'] = combined_prices_df['long_pos'] - combined_prices_df['short_pos']
        portfolio['coin_1'] = -1.0 * combined_prices_df['coin_1_prices'] * portfolio['positions']
        portfolio['coin_2'] = combined_prices_df['coin_2_prices'] * portfolio['positions']
        portfolio['total'] = portfolio['coin_1'] + portfolio['coin_2']
        #from day to day
        portfolio['returns'] = portfolio['total'].pct_change()
        portfolio['returns'].fillna(0.0, inplace=True)
        portfolio['returns'].replace([np.inf, -np.inf], 0.0, inplace=True)
        portfolio['returns'].replace(-1.0, 0.0, inplace=True)

        # Calculate the full equity curve
        portfolio['returns'] = (portfolio['returns'] + 1.0).cumprod()
        portfolio['trading_pair'] = f"{coin_1}-{coin_2}"
        portfolio['trading_pair'] = portfolio['trading_pair'].astype('string')
        print(type(portfolio['returns'].iloc[-1]  - portfolio['returns'].iloc[0]))
        overall_arr.append({
            'date':f"{portfolio['Date']}",
            'trading_pair' : f"{coin_1}-{coin_2}",
            'net_returns':  portfolio['returns'].iloc[-1]  - portfolio['returns'].iloc[0],
        })
        portfolio.to_csv(f"portfolio for pair {coin_1} and {coin_2}.csv")
        returns_files.append(f"portfolio for pair {coin_1} and {coin_2}.csv")
        res = []

        #portfolio['returns'].plot()
        
        #plt.show()
    #use groupBy() 
    
    portfolio = pd.concat(map(pd.read_csv, returns_files))
    x = map(os.remove, returns_files)
    
    
    overall = pd.DataFrame(overall_arr)
    # use the overall and then take the first 10 and then plot the portfolio of the first 10 using the previous block of code
    # sort the overall by net return
    # add trading pair to an array
    # use only these pairs in the final excel sheet when looking for trading pairs
    # as evidence, plot the returns graph for these 10 
    
    # taking the first 10 here
    overall.sort_values(by=['net_returns'], inplace=True, ascending=False)
    filtered_df = overall.iloc[0:5]
    filtered_df['trading_pair'] = filtered_df['trading_pair'].astype('string')
    filtered_names = [] 
    for index, row in (filtered_df.iterrows()):
        filtered_names.append(row['trading_pair'])
    print(filtered_names)
    print('portfolio before....')
    print(portfolio)
    print(portfolio['trading_pair'])
    #use isin to exract rows where a column values is in a list 
    new_filtered_portfolio = portfolio[portfolio['trading_pair'].isin(filtered_names)]
    
    #merge the filtered coins with the original cointegerated csv file
    new_cointegrated_data = cointegrated_pairs_df[cointegrated_pairs_df['trading_pair'].isin(filtered_names)]

    new_cointegrated_data.to_csv('filtered_cointegrated_pairs.csv')
    #new_filtered_portfolio.groupby('trading_pair')['returns'].plot(legend=True, y='Returns')
    #plt.show()
    #plt.close()
    print(filtered_df.info())
    print(portfolio.info())
    print(new_cointegrated_data)
    
    return "saved"