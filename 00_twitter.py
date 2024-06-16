import tweepy

# Twitter APIキーとトークン

import time
import tweepy
import configparser
import logging
from logging import getLogger,Formatter,StreamHandler
import json

BT= 'AAAAAAAAAAAAAAAAAAAAAB%2BktQEAAAAACWIJVqHUpGVYz%2FVy4nDOU%2BmRbAo%3Dv0NrB2mxz4md1JMbTtFkn62BxwRHOKisJ5ZWKmHFDOSNWskr3V'
CK= 'rrnY1WHOOFRdDfKkCyNTju2wJ'
CS= 'PByxtCR9SIDYCVVTfw8fCS3NOSm3HEhOQ5xtxDCRy0n7pQg9CA'
AT= '1346756863862349826-8Db7AmK4p0EkE6VlaL3c5Jd4ABRHwI'
AS= 'kO9od6AutTaEqbVB6YOcWDIyvrQUPrz1WBs3761Oh7yJs'

target_user=['NaomiSuzuki_','KesaGataMe0']
target_keywords=['#Phishing','hxxps']

target_keyword = '('
for idx, word in enumerate(target_keywords):
    target_keyword = target_keyword + '"' + word + '"' + ' OR '
target_keyword = target_keyword[:-4] + ')'

logger=getLogger('autoLikeAndRT')
streamFormat=Formatter('%(name)s:%(levelname)s:%(message)s')
stream=StreamHandler()
stream.setFormatter(streamFormat)
logger.addHandler(stream)
logger.setLevel(logging.DEBUG)

class Listner(tweepy.StreamingClient):
    def on_tweet(self, tweet):
        logger.info(f' id:{tweet.author_id} tweeted. text:{tweet.text}')
        for user in self.includes:
            if user.get('id')==tweet.author_id:
                self.username=user.get('username')
            else:
                self.username='?'
        self.client.like(tweet.id)
        logger.info(f'Liked tweet from id:{tweet.author_id} userid:{self.username} (tweet_id:{tweet.id} text:{tweet.text})')
        self.client.retweet(tweet.id)
        logger.info(f'Retweeted tweet from id:{tweet.author_id} userid:{self.username} (tweet_id:{tweet.id} text:{tweet.text})')

    def on_connect(self):
        logger.info('Connecting to streaming.')
        response=self.get_rules()
        if response.data!=None:
            for rule in response.data:
                self.delete_rules(rule.id)
                logger.info(f'Deleted previous rule({rule.value})')
        self.target=target_user
        self.keywords=target_keyword
        logger.info(f'Loaded target{self.target}')
        for target in self.target:
            keywords = self.keywords
            self.add_rules(tweepy.StreamRule(f'{keywords} from:{target} -is:reply -is:retweet -is:quote'))
            logger.info(f'Added rule.({keywords} from:{target})')
        self.client=tweepy.Client(bearer_token=BT,consumer_key=CK,consumer_secret=CS,access_token=AT,access_token_secret=AS,wait_on_rate_limit=True)
        logger.info(f'Created Twitter API client.')
        self.includes=[]
        self.ids=[]
        self.username='?'
        self.error_count={'time':time.time()}

    def on_includes(self, includes):
        for user in includes.get('users'):
            if user.get('id') not in self.ids:
                self.ids.append(user.get('id'))
                self.includes.append({'id':includes.get('users')[0].id,'name':includes.get('users')[0].name,'username':includes.get('users')[0].username})

    def on_errors(self, errors):
        print(errors)

    def on_exception(self, exception):
        logger.warning(f'Exception occured.\n{exception}\nRestarting Streaming.')
        time.sleep(3)
        if time.time()-self.error_count['time'] > 10:
            listner = Listner(BT)
            listner.filter(expansions='author_id',user_fields='username',tweet_fields='author_id')
        else:
            logger.error('Error occured within 10s after the instance started. ')

    def on_data(self, data):
        json_data = json.loads(data)
        print("--json-data--",json_data)

listner = Listner(BT)
listner.filter(expansions='author_id',user_fields='username',tweet_fields='author_id')

