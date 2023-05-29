
from connections import connect_dydx
from constants import ABORT_ALL_POSITIONS, FIND_COINTEGRATED, PLACE_TRADES, MANAGE_EXITS
from private import close_orders
from public import get_data
from cointegration import store_cointegration_results
from enter_pairs_trade import place_trades
from exit_pairs_trade import exit_trade
from messaging_bot import send_messages

if __name__ == '__main__':
  
    
    # send a message when bot starts
    send_messages("Launching Bot")
    try:
        client = connect_dydx()
    except Exception as e:
     
        print("Error connecting to client: ", e)
        exit(1)
    
    if ABORT_ALL_POSITIONS:
        try:
            print("Closing all orders")
            closed_orders = close_orders(client)
        except Exception as e:
            print("Error closing orders: ", e)
            send_messages(f"Error closing orders, {e}")
            exit(1)

    if FIND_COINTEGRATED:
        try:
            print("GETTING MARKET DATA")
            data = get_data(client)
        except Exception as e:
            print("Error getting orders: ", e)
            send_messages(f"Error getting market data to find cointegrated pairs, {e}")
            exit(1)
        try:
            print("Storing cointegration data")
            #cointegrated pairs data
            res = store_cointegration_results(data)
            if res != "saved":
                print("Error saving cointegrated results: ")
        except Exception as e:
            print("Error saving cointegrated results: ", e)
            send_messages(f"Error saving cointegrated results {e}")
            exit(1)

    #make sure that the bot is always on
    while True:
        if MANAGE_EXITS:
            try:
                print("Possibly Closing trades")
                exit_trade(client)
            except Exception as e:
                print("Error closing trading pairs: ", e)
                send_messages(f"Error closing trading pairs: {e}")
                exit(1)    
        if PLACE_TRADES:
            try:
                print("FINDING POSSIBLE TRADES")
                place_trades(client)
            except Exception as e:
                print("Error trading pairs: ", e)
                send_messages(f"Error trading pairs: {e}")
                exit(1)
