# -*- coding: utf-8 -*-
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'py_utils'))
import redis
import hashlib
import datetime
from config import QUE_MONITOR_SCRAPER, REDIS, SLEEP
from rabbitMQ import RabbitMQ
from newsapi_client import getNewsFromNewsAPI

# set up rabbitMQ between monitor and scraper
mqClient = RabbitMQ(QUE_MONITOR_SCRAPER['URI'], QUE_MONITOR_SCRAPER['NAME'])

# set up redis store new news for one day
redisClient = redis.StrictRedis(REDIS['HOST'], REDIS['PORT'])

# TODO: add complete news source to getNewsFromNewsAPI()

while True: 
    newslist = getNewsFromNewsAPI()
    if(newslist):
        newsAmount = 0
        for news in newslist:
            digest = hashlib.md5(news['title'].encode('utf-8')).digest().encode('base64')
            # if we never seen this news in past day
            if redisClient.get(digest) is None:
                news['digest'] = digest
                newsAmount = newsAmount + 1
                if news['publishedAt'] is None:
                    # format: YYYY-MM-DDTHH:MM:SS in UTC
                    news['publishedAt'] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                redisClient.set(digest, news)
                redisClient.expire(digest, REDIS['NEWS_EXPIRATION'])

                mqClient.sendMessage(news)

            # if we seen this news in past day, ignore it.
            
        print 'fetched %d new news.' % newsAmount
    mqClient.sleep(SLEEP['MONITOR'])