# FxStock Bot

It is a telegram bot for monitoring stock price, exchange rate and index.

## How to use it

### 0. Prerequisite

Python external library Beautiful Soup 4 and requests
```
pip install beautifulsoup4
pip install requests
```

Talk to BotFather in telegram and create a bot.
You will receive an authorization token.
https://core.telegram.org/bots


### 1. Clone it
```
git clone https://github.com/simonlaw101/tg_bot.git
```

### 2. Fill in the token
Fill in the token in service.py
```
TOKEN = 'YOUR_TOKEN'
```

### 3. Run the script
```
python3 main.py
```
To stop the script, press Ctrl+C

### 4. Deploy to AWS EC2 (Optional)
steps: https://medium.com/@simonlaw_9918/stock-tracking-telegram-bot-21be907c70ef
<br/><br/><br/><br/>


Reference:
1. Python bot script<br/>
https://www.youtube.com/watch?v=h1QGky22b-k
https://github.com/magnitopic/YouTubeCode/blob/master/Python/TelegramBots/TelegramBot.py

2. Python sched module<br/>
https://neven.me/python/2017/04/25/Python%E5%AE%9E%E7%8E%B0%E4%B8%80%E4%B8%AA%E7%AE%80%E5%8D%95%E7%9A%84%E5%AE%9A%E6%97%B6%E4%BB%BB%E5%8A%A1(sched%E5%AE%9E%E7%8E%B0%E5%88%86%E6%9E%90)/
https://blog.csdn.net/Leonard_wang/article/details/54017537

3. Send email<br/>
https://www.youtube.com/watch?v=JRCJ6RtE3xU
https://github.com/CoreyMSchafer/code_snippets/blob/master/Python/Emails/mail-demo.py
https://www.youtube.com/watch?v=XE-DS5pRFUo&list=LL105Q5fXzB9d9EAEDwMF04g

4. Finance information<br/>
https://finance.yahoo.com/quote/0001.HK/
https://finance.yahoo.com/quote/%5EHSI/history?p=%5EHSI
https://www.x-rates.com/calculator/?from=HKD&to=JPY&amount=1
https://finance.now.com/stock/?s=00001
https://finance.yahoo.com/quote/0001.HK/history?p=0001.HK

5. RSI calculation<br/>
https://www.youtube.com/watch?v=4gGztYfp3ck

6. Random pic<br/>
https://www.freecodecamp.org/news/learn-to-build-your-first-bot-in-telegram-with-python-4c99526765e4/

