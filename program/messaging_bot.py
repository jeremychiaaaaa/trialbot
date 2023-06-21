import requests
from decouple import config
from datetime import datetime, timedelta
import pandas as pd

# function to send message
def send_messages(message):
    bot_token = config("TELEGRAM_TOKEN")
    chat_id = config("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    res = requests.get(url)
    if res.status_code == 200:
        return "sent"
    else:
        return "failed"

# function to send file
def send_file(file):
    send_messages("Generating weekly report...")
    date_now = datetime.now()
    date_one_week_before = (date_now - timedelta(weeks=1))
    file = pd.DataFrame(file)
    file.to_csv(f'weekly report from {date_one_week_before} to {date_now}.csv')
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
    send_messages(f"Overall pnl for the week from {date_one_week_before} to {date_now}: {round(sum(file['overall_pnl']), 2)}")
    return r.json()