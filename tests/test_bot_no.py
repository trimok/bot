import unittest
from bots import fly_bot
from bots.fly_bot import handler_state_final
from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, UserState, MemoryStorage

class TestBotNo(unittest.TestCase):
    def test_bot_no(self):

        MEMORY = MemoryStorage()
        USER_STATE = UserState(MEMORY)
        bot = fly_bot.FlyBot(USER_STATE)

        state = fly_bot.State()        
        state.name = 'Jack'
        state.state = fly_bot.STATE_FINAL        
                
        message_in = "no"    
        message = handler_state_final(state, message_in)
        
        self.assertEqual(message, state.name + ', sorry to not have understading your question')
