import pandas as pd
import numpy as np
from connections import connect_dydx
import statsmodels.api as sm
from public import get_data
#the coint library here most importantl\y has a p-val;ue for the hypothesis test where the null hypothesis is that the 2 variables are not cointegrated
from statsmodels.tsa.stattools import coint
from constants import MAX_HALF_LIFE, WINDOW

#idea to calculate half life is to using calculate the linear regression between the spread returns and the lagged version of the spread and using that beta value pass it to a formula to calculate the half-life

def calculate_half_life(spread):
    df_spread = pd.DataFrame(spread, columns=["spread"])
    spread_lag = df_spread.spread.shift(1)
    spread_lag.iloc[0] = spread_lag.iloc[1]
    spread_ret = df_spread.spread - spread_lag
    spread_ret.iloc[0] = spread_ret.iloc[1]
    spread_lag2 = sm.add_constant(spread_lag)
    model = sm.OLS(spread_ret, spread_lag2)
    res = model.fit()
    halflife = round(-np.log(2) / res.params[1], 0)
    return halflife



#calculate zscore using spread
def calculate_zscore(spread_series):
    #need the mean, median, current of the spread
    spread_series = pd.Series(spread_series)
    mean = spread_series.rolling(center=False, window=WINDOW).mean()
    std = spread_series.rolling(center=False, window=WINDOW).std()
    x = spread_series.rolling(center=False, window=1).mean()
    zscore = (x - mean) / std
    #this here will be a dataframe with zscore values for each entry
    return zscore

#calculate Cointegration, spread = series_1 - (hedge_ratio * series_2)

def calculate_cointegration(series_1, series_2):
    #series 1 amd series 2 will be the price data of 2 coins
    series_1 = np.array(series_1).astype(np.float)
    series_2 = np.array(series_2).astype(np.float)
    coint_indicator = 0
    #coint() is a hypothsis test
    coint_test_result = coint(series_1, series_2)
    coint_t = coint_test_result[0]
    p_value = coint_test_result[1]
    critical_value = coint_test_result[2][1]
    #in general, if the t_value > critical_value --> reject the null hypothesis
    #use the model here to calculate hedge ratio to get the spread using hedge ratio
    model = sm.OLS(series_1, series_2).fit()
    hedge_ratio = model.params[0]
    #this spread formula can try and change and check results
    spread = series_1 - (hedge_ratio * series_2)
    half_life = calculate_half_life(spread)
    #only for this library
    t_check = coint_t < critical_value
    coint_indicator = 1 if p_value < 0.05 and t_check  else 0
    return coint_indicator, hedge_ratio, half_life


#store cointegration results in a pd dataframe 
def store_cointegration_results(data):
    #data here is the market data where we previously gathered for each available market
    markets = data.columns.tolist()
    pairs_that_met_criteria_list = []
    counter = 1
    for market in markets:
        for market_2 in markets[counter:]:
            series_1 = data[market].values.astype(float).tolist()
            series_2 = data[market_2].values.astype(float).tolist()
            coint_score, hedge_ratio, half_life = calculate_cointegration(series_1, series_2)
            if coint_score == 1 and half_life <= MAX_HALF_LIFE and half_life > 0:
               pairs_that_met_criteria_list.append({
                "series_1": market,
                "series_2": market_2,
                "hedge_ratio":hedge_ratio,
                "half_life": half_life,
                'trading_pair':f"{market}-{market_2}"
               })
            
            
        counter = counter + 1
    
    #creating a dataframe for storing cointegrated pairs
    df_cointegrated_pairs = pd.DataFrame(pairs_that_met_criteria_list)
    df_cointegrated_pairs.to_csv("cointegrated_pairs.csv")

    return "saved"

if __name__ == '__main__':
    client = connect_dydx()
    try:
        print("GETTING MARKET DATA")
        data = get_data(client)
    except Exception as e:
        print("Error getting orders: ", e)
        #send_messages(f"Error getting market data to find cointegrated pairs, {e}")
        exit(1)
    try:
        print("Storing cointegration data")
        #cointegrated pairs data
        res = store_cointegration_results(data)
        if res != "saved":
            print("Error saving cointegrated results: ")
    except Exception as e:
        print("Error saving cointegrated results: ", e)
        #send_messages(f"Error saving cointegrated results {e}")
        exit(1)
    