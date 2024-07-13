import logging
import logging.handlers
import os

import requests
import pandas as pd
import time
from textblob import TextBlob
import sqlite3

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger_file_handler = logging.handlers.RotatingFileHandler(
#     "status.log",
#     maxBytes=1024 * 1024,
#     backupCount=1,
#     encoding="utf8",
# )
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger_file_handler.setFormatter(formatter)
# logger.addHandler(logger_file_handler)

try:
    API = os.environ["COINPANIC_API"]
except KeyError:
    SOME_SECRET = "Token not available!"


if __name__ == "__main__":
    conn = sqlite3.connect('streamlit/coinpanic/crypto_data.db')
    query = "SELECT * FROM crypto_news_sentiment"
    query_df = pd.read_sql_query(query, conn)
    conn.close()
    existing_ids = query_df['id'].values

    r = requests.get(f'https://cryptopanic.com/api/v1/posts/?auth_token={API}&page=1')
    results = r.json()
    df = pd.json_normalize(results['results'])
    for page in range(2, 11):
        time.sleep(0.5)
        r = requests.get(f'https://cryptopanic.com/api/v1/posts/?auth_token={API}&page={page}')
        results = r.json()
        df = pd.concat([df, pd.json_normalize(results['results'])], axis = 0)

    def get_coins(row):
        try:
            coins = []
            for i in row:
                coins.append(i['code'])
            return list(set(coins))
        except:
            return []
        
    def determine_sentiment(row):
        analysis = TextBlob(row)
        polarity = analysis.sentiment.polarity
        if polarity > 0:
            return 'Positive'
        elif polarity < 0:
            return 'Negative'
        else:
            return 'Neutral'
    
    df['coins'] = df['currencies'].apply(get_coins)
    df['coins'] = df['coins'].apply(lambda x: ','.join(x))
    df['sentiment'] = df['title'].apply(determine_sentiment)
    new_df = df[['id','domain', 'title', 'coins', 'published_at', 'url', 'sentiment']]
    new_df = new_df.reset_index()
    new_df = new_df[~new_df['id'].isin(existing_ids)]

    conn = sqlite3.connect('streamlit/coinpanic/crypto_data.db')
    new_df.to_sql('crypto_news_sentiment', conn, if_exists = 'append', index = False)
    conn.close()
