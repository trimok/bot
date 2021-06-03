import unittest
from bots import fly_bot
from bots.fly_bot import handler_state_final
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, UserState, MemoryStorage

class TestBotYes(unittest.TestCase):
    def test_bot_yes(self):

        MEMORY = MemoryStorage()
        USER_STATE = UserState(MEMORY)
        bot = fly_bot.FlyBot(USER_STATE)

        state = fly_bot.State()        
        state.name = 'Jack'
        state.message_in = 'Hi I want to go from Paris to Tunis'
        state.state = fly_bot.STATE_FINAL        
        state.or_city='paris'
        state.dst_city='tunis'
        state.str_date='anytime'
        state.end_date='anytime'
                
        message_in = "yes"    
        
        message = handler_state_final(state, message_in)
        
        self.assertIn("you have a fly", message)
