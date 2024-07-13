import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from collections import Counter

st.set_page_config(
    page_title="SenCrypto",
    page_icon="chart_with_upwards_trend",
    layout="wide"
)

conn = sqlite3.connect('crypto_data.db')
query = "SELECT * FROM crypto_news_sentiment"
query_df = pd.read_sql_query(query, conn)
conn.close()
query_df['published_at'] = pd.to_datetime(query_df['published_at']).dt.tz_localize(None)

st.header("SenCrypto")

st.subheader("Dates")
st.write(f"- Dashboard last refreshed (UTC -8): {datetime.utcnow().replace(microsecond=0)}")
st.write(f"- Latest article available (UTC -8): {query_df['published_at'].max()}")

st.subheader("Select Date Range")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Select a start date", min_value = query_df['published_at'].min(), max_value = query_df['published_at'].max(), value= query_df['published_at'].min())
with col2:
    end_date = st.date_input("Select a end date", min_value = start_date, max_value = query_df['published_at'].max(), value= query_df['published_at'].max())

filtered_df = query_df[(query_df['published_at'].dt.date >= start_date) & (query_df['published_at'].dt.date <= end_date)]
filtered_df['datetime'] = filtered_df['published_at'].dt.floor('h')
filtered_df['date'] = filtered_df['published_at'].dt.floor('D')

col1, col2 = st.columns(2)
with col1:
    counts_df = filtered_df.groupby(['sentiment']).agg({'id': 'count'}).reset_index()
    filtered_agg_df = filtered_df.groupby(['datetime', 'sentiment']).agg({'id': 'count'}).reset_index()
    crypto_list = sum([x.split(',') for x in filtered_df['coins'].values if x!=''],[])
    crypto_list = [x for x in crypto_list if x not in ['OG','U']]
    crypto_count_dict = Counter(crypto_list)
    crypto_count_df = pd.DataFrame(list(crypto_count_dict.items()), columns=['crypto', 'count']).sort_values('count', ascending = False)
    st.subheader("Cryptos by Mention")
    st.write(f"Top 5 cryptos by mention: {', '.join([str(x[0]) for x in crypto_count_df.head(5).values])}")
    fig = px.pie(crypto_count_df, names="crypto", values ='count')
    fig.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig)
with col2:
    st.subheader('Top 10 Cryptos by Sentiment Counts')
    crypto_list_unique = list(set(crypto_list))
    crypto_list_unique.sort()
    crypto_dict_list = []
    for crypto in crypto_list_unique:
        crypto_dict = {}
        crypto_dict['coins'] = crypto
        crypto_df = filtered_df[filtered_df['coins'].str.contains(crypto)]
        crypto_dict['positive_count'] = len(crypto_df[crypto_df['sentiment'] == "Positive"])
        crypto_dict['neutral_count'] = len(crypto_df[crypto_df['sentiment'] == "Neutral"])
        crypto_dict['negative_count'] = len(crypto_df[crypto_df['sentiment'] == "Negative"])
        crypto_dict['total'] = len(crypto_df)
        crypto_dict_list.append(crypto_dict)
    crypto_sentiment_df = pd.DataFrame(crypto_dict_list).sort_values('total', ascending= False)
    st.write(f"Top 5 cryptos by positive counts: {', '.join([str(x[0]) for x in crypto_sentiment_df.sort_values('positive_count', ascending= False).head(5).values])}")
    st.write(f"Top 5 cryptos by negative counts: {', '.join([str(x[0]) for x in crypto_sentiment_df.sort_values('negative_count', ascending=False).head(5).values])}")
    st.plotly_chart(px.bar(crypto_sentiment_df.head(10), x = "coins", y = ["positive_count", "neutral_count", "negative_count"]))



col1, col2, col3 = st.columns(3)
for idx, sentiment in enumerate(["Positive", "Neutral", "Negative"], 1):
    ts_df = filtered_agg_df[filtered_agg_df['sentiment'] == sentiment]
    max_time = ts_df['datetime'].max()
    max_time_24h_before = max_time - timedelta(hours=24)
    ts_24h_df = ts_df[(ts_df['datetime'] <= max_time) & (ts_df['datetime'] >= max_time_24h_before)]
    date_range = pd.date_range(ts_24h_df['datetime'].min(), ts_24h_df['datetime'].max(), freq='h')
    dates_df = pd.DataFrame(columns=['datetime'], data = date_range)
    dates_df = dates_df.merge(ts_24h_df, how = 'left', on = 'datetime').fillna(0)[['datetime','id']]
    if idx == 1:
        with col1:
            st.subheader(f"{sentiment} Sentiment Articles")
            st.metric(f"Article count:", counts_df[counts_df['sentiment'] == sentiment]['id'].values[0])
            st.plotly_chart(px.area(dates_df, x = "datetime", y="id", title = 'Articles in the Last 24h:', color_discrete_sequence = ["limegreen"], width = 550, height = 500))
    if idx == 2:
        with col2:
            st.subheader(f"{sentiment} Sentiment Articles")
            st.metric(f"Article count:", counts_df[counts_df['sentiment'] == sentiment]['id'].values[0])
            st.plotly_chart(px.area(dates_df, x = "datetime", y="id", title = 'Articles in the Last 24h:', color_discrete_sequence = ["gray"], width = 550, height = 500))
    if idx == 3:
        with col3:
            st.subheader(f"{sentiment} Sentiment Articles")
            st.metric(f"Article count:", counts_df[counts_df['sentiment'] == sentiment]['id'].values[0])
            st.plotly_chart(px.area(dates_df, x = "datetime", y="id", title = 'Articles in the Last 24h:', color_discrete_sequence = ["red"], width = 550, height = 500))

coin_selection = st.selectbox("Select a crypto", options = crypto_list_unique)

filtered_df = filtered_df[filtered_df['coins'].str.contains(coin_selection)]

pos_filtered_df = filtered_df[filtered_df['sentiment'] == "Positive"].sort_values('datetime', ascending = False)
neu_filtered_df = filtered_df[filtered_df['sentiment'] == "Neutral"].sort_values('datetime', ascending = False)
neg_filtered_df = filtered_df[filtered_df['sentiment'] == "Negative"].sort_values('datetime', ascending = False)

pos_rate = len(pos_filtered_df)
neu_rate = len(neu_filtered_df)
neg_rate = len(neg_filtered_df)

metric1, metric2, metric3 = st.columns(3)
with metric1:
    st.metric(label = "Positive Articles", value = pos_rate)
    if pos_rate > 0:
        st.write("Articles:")
    dates = set(pos_filtered_df['date'].values)
    for date in dates:
        st.markdown(f'- {pd.to_datetime(date).date()}')
        for id, title in zip(pos_filtered_df[pos_filtered_df['date'] == date]['id'].values,
                             pos_filtered_df[pos_filtered_df['date'] == date]['title'].values):
            st.markdown(f"[{title}]({f'https://cryptopanic.com/news/click/{id}/'})")
with metric2:
    st.metric(label = "Neutral Articles", value = neu_rate)
    if neu_rate > 0:
        st.write("Articles:")
    dates = set(neu_filtered_df['date'].values)
    for date in dates:
        st.markdown(f'- {pd.to_datetime(date).date()}')
        for id, title in zip(neu_filtered_df[neu_filtered_df['date'] == date]['id'].values,
                             neu_filtered_df[neu_filtered_df['date'] == date]['title'].values):
            st.markdown(f" [{title}]({f'https://cryptopanic.com/news/click/{id}/'})")
with metric3:
    st.metric(label = "Negative Articles", value = neg_rate)
    if neg_rate > 0:
        st.write("Articles:")
    dates = set(neg_filtered_df['date'].values)
    for date in dates:
        st.markdown(f'- {pd.to_datetime(date).date()}')
        for id, title in zip(neg_filtered_df[neg_filtered_df['date'] == date]['id'].values,
                             neg_filtered_df[neg_filtered_df['date'] == date]['title'].values):
            st.markdown(f"[{title}]({f'https://cryptopanic.com/news/click/{id}/'})")
