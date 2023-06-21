import json
from connections import connect_dydx
import pandas as pd
from datetime import datetime, timedelta
from messaging_bot import send_file, send_messages
import requests
from decouple import config

def generate_report(client):
    weekly_report_list = []
    try:
        positions_json = open("bot_agents.json")
        positions_dict = json.load(positions_json)
    except Exception as e:
        return "Empty"


    if len(positions_dict) == 0:
        return "Empty"
    


    platform_data = client.private.get_positions(status="OPEN")
    platform_data_closed = client.private.get_positions(status="CLOSED")
    platform_data_positions = platform_data.data["positions"]
    platform_data_closed_positions = platform_data_closed.data["positions"]
    
    for position in positions_dict:
        position_status = position['pair_status']
        date_open = position['coin_1_orderTime']
        data_closed = position['date_closed']

        #find pnl for each coin 
        coin_1 = position['coin_1']
        coin_2 = position['coin_2']

        coin_1_realized_pnl = (float(position['coin_1_realized_pnl'])) if position['coin_1_realized_pnl'] != '' else 0
        #print(float(position['coin_1_realized_pnl']))
        coin_2_realized_pnl = (float(position['coin_2_realized_pnl'])) if position['coin_2_realized_pnl'] != '' else 0
        coin_1_pnl = 0
        coin_2_pnl = 0
        for m in platform_data_positions:
        # user positions that are open on dydx
            if(coin_1 == m["market"]):
                coin_1_pnl = m['unrealizedPnl']
            if(coin_2 == m["market"]):
                coin_2_pnl = m['unrealizedPnl']
        
        overall_pnl = (float(coin_1_pnl)) + (float(coin_2_pnl))
        weekly_report_list.append({
            'date_open': date_open,
            'date_closed' : position['date_closed'],
            'coin_1':coin_1,
            'coin_1_pnl':coin_1_pnl if coin_1_realized_pnl == 0 else coin_1_realized_pnl,
            'coin_2':coin_2,
            'coin_2_pnl':coin_2_pnl if coin_2_realized_pnl == 0 else coin_2_realized_pnl,
            'overall_pnl':overall_pnl if coin_1_realized_pnl == 0 else (coin_1_realized_pnl + coin_2_realized_pnl),
            'position_status':position_status
        })
            

    
    weekly_report_df = pd.DataFrame(weekly_report_list)
    print(weekly_report_df)
    send_messages("Generating weekly report...")
    date_now = datetime.now()
    date_one_week_before = (date_now - timedelta(weeks=1))
    weekly_report_df.to_csv(f'weekly report from {date_one_week_before} to {date_now}.csv')
    bot_token = config("TELEGRAM_TOKEN")
    chat_id = config("TELEGRAM_CHAT_ID")
    send_document = 'https://api.telegram.org/bot' + bot_token +'/sendDocument?'
    data = {
     'chat_id': chat_id,
     'parse_mode':'HTML',
     'caption':'Weekly report'
    }
    r = requests.post(send_document, data=data, 
    files={'document': open(f'weekly report from {date_one_week_before} to {date_now}.csv','rb')}, stream=True)
    send_messages(f"Overall pnl for the week from {date_one_week_before} to {date_now}: {round(sum(weekly_report_df['overall_pnl']), 2)}")
    return weekly_report_df

if __name__ == '__main__':
    client = connect_dydx()
    report = generate_report(client)
    