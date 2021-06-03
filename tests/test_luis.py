import unittest
from bots import fly_bot
from bots.fly_bot import query_luis
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, UserState, MemoryStorage

class TestLuis(unittest.TestCase):
    def test_luis(self):

        MEMORY = MemoryStorage()
        USER_STATE = UserState(MEMORY)
        bot = fly_bot.FlyBot(USER_STATE)

        or_city = 'paris'
        dst_city = 'tunis'

        data, intents, entities, error  = query_luis("Hi I want to go from " +  or_city + " to " + dst_city)
        
        or_city_luis = entities['or_city'][0]['text']
        dst_city_luis = entities['dst_city'][0]['text']

        self.assertEqual(or_city, or_city_luis)
        self.assertEqual(dst_city, dst_city_luis)