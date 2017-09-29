import requests
import json
from flask import Flask, request
import apiai
import pyowm


OWM_TOKEN ="ff66a55cf163cad6cf0db8c7f3d93352"

VERIFY_TOKEN='abcd123'
#FB
#PAGE_ACCESS_TOKEN = 'EAALjV1sGsOMBAOZAW1aiZAgfTakNKVURIA89qBpdnsmWOHL7cHwpUGUtfO78CBexJbnHJWjKaRVIPZBh2TAYxRhaLHkWZBDYT4EESWDiWf0ZAgbOnMRBxqS9Sa0o2F8ZBGJPevmQnWLURKvLQjr44ZAzWTT86fgim4FB8omAubiqQZDZD'
PAGE_ACCESS_TOKEN='EAADYWMVfOd4BAAgUir9ZAxgUCdYnU2F7ehVZAu49pDjVdJZCD1KA8EgZBY4K3p4kXvBsmYVZCxOiG0lFxmf885iOVBtPnVtCxOLanZA5fmOYt3B3F3IpMz2rZBBZBMwQEMu6AJqEjOwPt3rwhrk6V7ZBvB0AvAZCJwtc3WSzGd1JRLqAZDZD'
CLIENT_ACCESS_TOKEN = '70290e7963e543d392a19b33c4e8a90f'
own = pyowm.OWM(OWM_TOKEN)

ai = apiai.ApiAI(CLIENT_ACCESS_TOKEN)

app = Flask(__name__)
@app.route('/',methods=['GET'])
def handle_veriication():
	'''
			Verifies facebook webhook subscription
			Successful when verify_token is same as token sent by FB App
	'''

	if (request.args.get('hub.verify_token', '') == 'abcd123'):
		print("succefully verified")
		return request.args.get('hub.challenge', '')
	else:
		print("Wrong verification token!")
		return "Wrong validation token"

@app.route('/', methods=['POST'])
def handle_message():
	'''
	Handle messages sent by facebook messenger to the applicaiton
	'''
	data = request.get_json()

	if data["object"] == "page":
		for entry in data["entry"]:
			for messaging_event in entry["messaging"]:
				if messaging_event.get("message"):  

					sender_id = messaging_event["sender"]["id"]        
					recipient_id = messaging_event["recipient"]["id"]  
					message_text = messaging_event["message"]["text"]  
					send_message_response(sender_id, parse_user_message(message_text)) 

	return "ok"


def send_message(sender_id, message_text):
	'''
	Sending response back to the user using facebook graph API
	'''
	r = requests.post("https://graph.facebook.com/v2.6/me/messages",

		params={"access_token": PAGE_ACCESS_TOKEN},

		headers={"Content-Type": "application/json"}, 

		data=json.dumps({
		"recipient": {"id": sender_id},
		"message": {"text": message_text}
	}))

def parse_user_message(user_text):
	'''
	Send the message to API AI which invokes an intent
	and sends the response accordingly
	The bot response is appened with weaher data fetched from
	open weather map client
	'''
	
	request = ai.text_request()
	request.query = user_text

	response = json.loads(request.getresponse().read().decode('utf-8'))
	responseStatus = response['status']['code']
	if (responseStatus == 200):

		print("API AI response", response['result']['fulfillment']['speech'])
		try:
			#Using open weather map client to fetch the weather report
			weather_report = ''

			input_city = response['result']['parameters']['geo-city']
			print("City ", input_city)

			owm = pyowm.OWM(OWM_TOKEN)  # You MUST provide a valid API key

			forecast = owm.daily_forecast(input_city)

			observation = owm.weather_at_place(input_city)
			w = observation.get_weather()
			print(w)                      
			print(w.get_wind())                 
			print(w.get_humidity())      
			max_temp = str(w.get_temperature('celsius')['temp_max'])  
			min_temp = str(w.get_temperature('celsius')['temp_min'])
			current_temp = str(w.get_temperature('celsius')['temp'])
			wind_speed = str(w.get_wind()['speed'])
			humidity = str(w.get_humidity())

			weather_report = ' max temp: ' + max_temp + ' min temp: ' + min_temp + ' current temp: ' + current_temp + ' wind speed :' + wind_speed + ' humidity ' + humidity + '%'
			print("Weather report ", weather_report)

			return (response['result']['fulfillment']['speech'] + weather_report)
		except:
			return (response['result']['fulfillment']['speech'])

	else:
		return ("Sorry, I couldn't understand that question")

def send_message_response(sender_id, message_text):

	sentenceDelimiter = ". "
	messages = message_text.split(sentenceDelimiter)
	
	for message in messages:
		send_message(sender_id, message)



if __name__ == '__main__':
	app.run()
