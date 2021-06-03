# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext, UserState
from botbuilder.schema import ChannelAccount
import requests
import re
import applicationinsights
from applicationinsights import TelemetryClient
import json

# URL et clés pour Luis
url_luis_locale = "https://westeurope.api.cognitive.microsoft.com"
url_service_prediction_app = "/luis/prediction/v3.0/apps/" 
url_service_prediction_key = "/slots/production/predict?subscription-key=" 
url_service_prediction_query = "&verbose=true&show-all-intents=true&log=true" 
key_prediction_ressource = 'a16a0e1abc7a408a8e66ee03693d5f14'
app_id_luis = '690a3b83-f738-4430-8d76-3a30e516da8a'

# Telemetrie
instrumentation_key="1021fc72-bd40-48e1-a4a3-2624d953441e"
tc = TelemetryClient(instrumentation_key)

# Construit une URL de prédiction LUIS
def make_url_prediction ():

    global url_service_prediction_app
    global url_service_prediction_key
    global url_service_prediction_query
    global url_luis_locale 
    global app_id_luis
    global key_prediction_ressource
    
    return url_luis_locale \
           + url_service_prediction_app \
           + app_id_luis \
           + url_service_prediction_key \
           + key_prediction_ressource \
           + url_service_prediction_query

# Template connection
def connection(url, headers={}, params={}, data="", post=True):       
    try:
        if post:
            response = requests.post(url, headers=headers, params=params, data=data)
        else:    
            response = requests.get(url, headers=headers, params=params, data=data)
        data = response.json()
        print(response.status_code)
        return data, None
    except requests.exceptions.HTTPError as error:
        print(error)
        return None, error
    
# Interroge le système Luis
def query_luis(query):
    print("Interrogation...\n")

    # Headers
    headers = {}
            
    # Params
    params = {"query" : query}     
    
    # Url
    url = make_url_prediction ()
    
    # Appel    
    data, error =  connection(url, headers, params, post=False)
    
    # Traitement de la réponse
    if error is not None:
        return None, None, None, error
    else:    
        try:
            # Affichage des intentions
            intents = data['prediction']['intents']
            print ("\nIntents : \n")                
            for key in intents:
                print(key + " : " + str(intents[key]['score']))    

            # Affichage des entités    
            print ("\nEntities : \n")
            entities = data['prediction']['entities']['$instance']
            for key in entities:
                print(key + " : " + entities[key][0]['text'])
            print ("\n")    

            # On retourne une version simplifiée des énoncés(avec score), et la valeur des entités    
            return data, intents, entities, None               
        except:
            print("Erreur : ", data)
            return data, None, None, "Erreur"    
        
# Retourne un Code date mois jour sous la forme "yyyy-mm-dd"       
def get_code_mois_jour(date):
    
    if date == "anytime":
        return date

    months = {"JANUARY":"01", 
           "FEBRUARY":"02", 
           'MARCH':"03", 
           "APRIL":"04", 
           "MAY":"05", 
           "JUNE":"06",
           "JULY":"07",
           "AUGUST":"08", 
           "SEMPTEMBER":"09", 
           "OCTOBER":"10", 
           "NOVEMBER":"11", 
           "DECEMBER":"12"}

    upper_date = date.upper()
    for month in months:
        index = upper_date.find(month)
        if index > -1:
            day = upper_date[index + len(month):].strip()
            if len(day) == 1:
                day = "0" + day
            return "2021-" + months[month] + "-" + day        
    
# Transforme 200USD en 200 USD    
def replace_devise(message_in):
     # Replace
    message_in = re.sub('(\d+)st','\\1 st', message_in)
    message_in = re.sub('(\d+)th','\\1 th', message_in)
    message_in = re.sub('(\d+)TH','\\1 TH', message_in)
    message_in = re.sub('(\d+)rd','\\1 rd', message_in)
    message_in = re.sub('(\d+)nd','\\1 nd', message_in)
    message_in = re.sub('(\d+)USD','\\1 USD', message_in)
    return message_in        


# Les etats du bot
STATE_WELCOME = 0    
STATE_NAME = 1    
STATE_QUESTION = 2    
STATE_FINAL = 3

# Traitement du démarraage de la conversation
def handler_state_welcome(state):
    state.state = STATE_NAME
    message = "Welcome to FLY ME ! What is your first name ?"

    return message

# Gestion après l'envoi du prénom
def handler_state_name(state, message_in):
    state.name = message_in
    state.state = STATE_QUESTION 
    message = "Hi, " + state.name + ", ask your question." 
    
    return message

# Traitement d'une question par interrogation du système Luis
def handler_state_question(state, message_in):
     # luis query
    try:
        data, intents, entities, error = query_luis(message_in)

        # Construction de la réponse        
        try:
            # Intentions            
            message = "Your Intent : \n"                
            best_score = 0
            best_key = 0
            for key in intents:
                if intents[key]['score'] > best_score:
                    best_score = intents[key]['score']
                    best_key = key
            intent = best_key        

            # Entités    
            dict_entities = {}
            dict_entities['str_date'] = "anytime"
            dict_entities['end_date'] = "anytime"
            dict_entities['or_city']=""
            dict_entities['dst_city']=""
            dict_entities['budget']=""        

            dict_prefix_entities = {}

            dict_prefix_entities['str_date'] = " departure date : "
            dict_prefix_entities['end_date'] = " return date : "
            dict_prefix_entities['or_city']=" from : "
            dict_prefix_entities['dst_city']=" to : "
            dict_prefix_entities['budget']=" for a maximum budget of :  "   

            dict_format_entities={}
            dict_format_entities['str_date'] = ""
            dict_format_entities['end_date'] = ""
            dict_format_entities['or_city']=""
            dict_format_entities['dst_city']=""
            dict_format_entities['budget']=""        


            for key in entities:
                dict_format_entities[key] = dict_prefix_entities[key] + str(entities[key][0]['text']) + "\n\n"
                dict_entities[key] = str(entities[key][0]['text'])

            # le message de retour
            message = state.name + ", do you mean you want to {} a flight : \n\n{}{}{}{}{}\n\n(yes/no)". \
                      format(intent, dict_format_entities['or_city'], dict_format_entities['dst_city'], 
                             dict_format_entities['str_date'], dict_format_entities['end_date'], dict_format_entities['budget'])
            
            # Mémorisation des informations dans l'état du bot
            state.state = STATE_FINAL
            state.message_out = message
            state.or_city = dict_entities['or_city']
            state.dst_city = dict_entities['dst_city']
            state.str_date= dict_entities['str_date']
            state.end_date = dict_entities['end_date']
        except Exception as e:
            # Telemetry
            tc.track_event('Bot exception Luis response management', {'message_in': message_in, 'luis_response':data, 'text': str(e) })
            tc.flush()
            message = state.name + ", I don't understand your message."                       
    except Exception as e:    
        # Telemetry
        tc.track_event('Bot exception Luis', { 'message_in': message_in, 'text': str(e) })
        tc.flush()
        message = state.name + ", I don't understand your message."   

    # Mémorisation du message en entrée   
    state.message_in = message_in
    
    return message

# Gestion de l'état final
def handler_state_final(state, message_in):
    if message_in.upper() == 'YES' or message_in.upper() == 'Y':
        try:    
            # Interrogation API  libre Skyscanner        
            headers = {
            'x-rapidapi-key': "2e7cb423dbmshd7dfc72b958ca46p16714ajsn1b6876f0a66d",
            'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
            'Accept':'application/json'
            }
            
            apikey = "ra66933236979928"
            
            url_get_token = "https://partners.api.skyscanner.net/apiservices/token/v2/gettoken"
            url_get_code_city = "http://partners.api.skyscanner.net/apiservices/autosuggest/v1.0/US/USD/us"
            url_get_quotes = "https://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/US/USD/us/"

            # Obtention d'un token
            params = {"apiKey":apikey}
            token, error = connection(url_get_token, headers=headers, params=params, post=False)
            
            # Recherche du code correspondant à la ville de départ
            if error is None:                
                params = {"apiKey":apikey, "query":state.or_city}
                data, error = connection(url_get_code_city, headers=headers, params=params, post=False)
                or_city_code = data["Places"][0]['PlaceId']

            # Recherche du code correspondant à la ville de destination    
            if error is None:                    
                params = {"apiKey":apikey, "query":state.dst_city}
                data, error = connection(url_get_code_city, headers=headers, params=params, post=False)
                dst_city_code = data["Places"][0]['PlaceId']

            # Construction de l'url d'interrogation pour obtenir les vols
            if error is None: 
                params = {"apiKey":apikey}
                url = url_get_quotes \
                      + or_city_code \
                      + "/" \
                      + dst_city_code \
                      + "/" \
                      + get_code_mois_jour(state.str_date) \
                      + "/" \
                      +get_code_mois_jour(state.end_date) 

                data, error = connection(url, headers=headers, params=params, post=False)

            if error is None:    
                # On prend la première proposition
                quote = data["Quotes"][0]

                # Le prix
                price = quote["MinPrice"]

                # Metadata pour lLes aéroports de départ et d'arrivée
                places = data['Places']

                # Récupération date, code aéroports depart et destination (aller)
                begin_departure_date = quote["OutboundLeg"]["DepartureDate"]
                begin_origin_city_id = quote["OutboundLeg"]["OriginId"]
                begin_destination_city_id = quote["OutboundLeg"]["DestinationId"]

                # Récupération date, code aéroports depart et destination (retour)
                end_departure_date = quote["InboundLeg"]["DepartureDate"]
                end_origin_city_id = quote["InboundLeg"]["OriginId"]
                end_destination_city_id = quote["InboundLeg"]["DestinationId"]

                # On récupère les noms des aéroports de départ et d'arrivée à partir du code
                for place in places:
                    if place['PlaceId'] == begin_origin_city_id:
                        begin_origin_city = place["Name"] 
                    if place['PlaceId'] == begin_destination_city_id:
                        begin_destination_city = place["Name"] 
                    if place['PlaceId'] == end_origin_city_id:
                        end_origin_city = place["Name"] 
                    if place['PlaceId'] == end_destination_city_id:
                        end_destination_city = place["Name"] 

                # Construction du message        
                message =  state.name + ", you have a fly : \n\ngo : from {} to {}, departure {}, \n\nback : from {} to {}, departure {}, \n\nprice : {} USD ". \
                         format(begin_origin_city, begin_destination_city, begin_departure_date, 
                              end_origin_city, end_destination_city, end_departure_date, price)
                tc.track_event('Bot success', {'message_in': state.message_in, 'message_out':state.message_out})
                tc.flush()     
                
            if  error is not None:
                raise Exception(error)
        except Exception as e:
            print (str(e))
            message = "Sorry, " +  state.name + ", we don't find a fly."
            tc.track_event('Bot noflyfound', {'message_in': state.message_in, 'message_out':state.message_out})
            tc.flush()                    
    else :
        message = state.name + ', sorry to not have understading your question'
        tc.track_event('Bot exception Bad Luis Analysis', {'message_in': state.message_in, 'message_out':state.message_out})
        tc.flush()
    state.state = STATE_QUESTION  
    
    return message
    
# La classe Etat
class State:
    def __init__(self, state: int = STATE_WELCOME, message_in:str ='', message_out:str ='', message_luis:str='', name:str='',
                or_city:str='', dst_city:str='', str_date:str='', end_date:str=''):
        self.state = state    
        self.message_in = message_in
        self.message_out = message_out
        self.message_luis = message_luis
        self.name = name
        self.or_city=or_city
        self.dst_city=dst_city
        self.str_date=str_date
        self.end_date=end_date
  
# La classe Bot
class FlyBot(ActivityHandler):
    def __init__(self, user_state: UserState):
        if user_state is None:
            raise TypeError(
                "[WelcomeBot]: Missing parameter. user_state is required but None was given"
            )

        self._user_state = user_state
        self.user_state_accessor = self._user_state.create_property("State")
        
    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)

        # save changes to UserState after each turn
        await self._user_state.save_changes(turn_context)               
    
    # Démarrage de la conversation
    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
         # Get the state properties from the turn context.
        state = await self.user_state_accessor.get(
            turn_context, State
        )
        
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                message = handler_state_welcome(state)
                await turn_context.send_activity(message)

    # Traitement du message suivant l'état du bot            
    async def on_message_activity(self, turn_context: TurnContext):
        
        # Le message en entrée
        message_in = turn_context.activity.text
        
        # Get the state properties from the turn context.
        state = await self.user_state_accessor.get(
            turn_context, State
        )
        # Trace
        print("state " + str(state.state))   
        
        # Mémorisation du message
        state.message_in = message_in                
        
        # Telemetry text bot
        tc.track_event('Bot request', { 'text': message_in })
        tc.flush()
        
        # Replace (pre-traitement)
        message_in = replace_devise(message_in)
        
        # Traitement du message suivant l'état du bot
        if state.state == STATE_NAME:       
            message = handler_state_name(state, message_in)
        elif state.state == STATE_QUESTION:
            message = handler_state_question(state, message_in)           
        elif state.state == STATE_FINAL:
            message = handler_state_final(state, message_in)       
        
        # Telemetry
        tc.track_event('Bot response', {'text': message })
        tc.flush()
        
        # La réponse                          
        return await turn_context.send_activity(                             
            MessageFactory.text(message)
        )
