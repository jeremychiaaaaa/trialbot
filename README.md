# Trialbot

### Trialbot is a cryptocurrency pairs trading bot developed with python and deployed on AWS EC2. The bot is currently trading on the Georli TestNet on the DyDx trading platform.

## Features

Using Cron Job,

- Generate Weekly Report on the pairs traded and the PNL for the week
- Attain a list of cointegration results with the help of statsmodels api
- Using the cointegration results, filter the pairs by backtesting with the last 5 years of data to obtain the best 30 pairs based on overall PnL
- Integrated in a messaging bot to send the weekly report and prompts to my telegram account directly
