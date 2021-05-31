# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.schema import ChannelAccount
import requests
import re
from applicationinsights import TelemetryClient

url_luis_locale = "https://westeurope.api.cognitive.microsoft.com"
url_service_prediction_app = "/luis/prediction/v3.0/apps/" 
url_service_prediction_key = "/slots/production/predict?subscription-key=" 
url_service_prediction_query = "&verbose=true&show-all-intents=true&log=true" 
key_prediction_ressource = 'a16a0e1abc7a408a8e66ee03693d5f14'
app_id_luis = '690a3b83-f738-4430-8d76-3a30e516da8a'

instrumentation_key="1021fc72-bd40-48e1-a4a3-2624d953441e"
tc = TelemetryClient(instrumentation_key)

# Construit une URL de prédiction
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
    
class EchoBot(ActivityHandler):
    async def on_members_added_activity(
        self, members_added: [ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        global tc
        
        message_in = turn_context.activity.text
        
        # Telemetry text bot
        tc.track_event('Bot request', { 'text': message_in })
        
        # Replace
        message_in = re.sub('(\d+)st','\\1 st', message_in)
        message_in = re.sub('(\d+)th','\\1 th', message_in)
        message_in = re.sub('(\d+)TH','\\1 TH', message_in)
        message_in = re.sub('(\d+)rd','\\1 rd', message_in)
        message_in = re.sub('(\d+)nd','\\1 nd', message_in)
        message_in = re.sub('(\d+)USD','\\1 USD', message_in)
        
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
                dict_entities['str_date'] = ""
                dict_entities['end_date'] = ""
                dict_entities['or_city']=""
                dict_entities['dst_city']=""
                dict_entities['budget']=""        

                dict_prefix_entities = {}

                dict_prefix_entities['str_date'] = " from : "
                dict_prefix_entities['end_date'] = " to : "
                dict_prefix_entities['or_city']=" departure date : "
                dict_prefix_entities['dst_city']=" return date : "
                dict_prefix_entities['budget']=" for a maximum budget of :  "                

                for key in entities:
                    dict_entities[key] = dict_prefix_entities[key] + str(entities[key][0]['text']) + "\n\n"

                # le message de retour
                message = "Do you you want to {} a flight\n\n{}{}{}{}{}". \
                          format(intent, dict_entities['or_city'], dict_entities['dst_city'], dict_entities['str_date'], \
                                                       dict_entities['end_date'], dict_entities['budget'])
            except Exception as e:
                # Telemetry
                tc.track_event('Bot exception Luis response management', {'message_in': message_in, 'luis_response':data, 'text': str(e) })
                message = "We don't understand your message."            
        except Exception as e:    
            # Telemetry
            tc.track_event('Bot exception Luis', { 'message_in': message_in, 'text': str(e) })
            message = "We don't understand your message."   
        
        # La réponse                          
        return await turn_context.send_activity(     
            # Telemetry
            tc.track_event('Bot response', {'text': message })
            
            MessageFactory.text(message)
        )
