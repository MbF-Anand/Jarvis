#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime, date, timedelta
from flask import jsonify, request, Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import dateutil.parser
import nltk
nltk.download('vader_lexicon')
from nltk.sentiment.vader import SentimentIntensityAnalyzer
sid = SentimentIntensityAnalyzer()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://jarvis:MarvelIron@localhost/jarvis'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://jarvis:MarvelIron@jarvis-mysql/jarvis'
db = SQLAlchemy(app)
import operator

@app.route('/')
def index():
    return 'Jarvis API - Running'

def getbookedslots(date):
	additionalquery = "WHERE date='%s' AND status=1"%(date)
	query = text("SELECT in_time, out_time  FROM meeting_room " + additionalquery)
	resp = db.engine.execute(query)
	slots = []
	for row in resp:
		temp = {}
		temp['from_time'] = row[0]
		temp['to_time'] = row[1]
		slots.append(temp)	
	return slots

@app.route('/firemate', methods=['POST'])
def firemate():

	responsedetails = {}

	req = request.get_json(force=True)

	status = "Invalid Request"

	try:
		date = req['queryResult']['parameters'].get('date')[0]
	except:
		date = req['queryResult']['parameters'].get('date')

	try:				
		timeperiod = req['queryResult']['parameters'].get('time-period')[0]
	except:
		timeperiod = req['queryResult']['parameters'].get('time-period')

	try:
		purpose = req['queryResult']['parameters'].get('purpose')[0]
	except:
		purpose = req['queryResult']['parameters'].get('purpose')

	try:
		email = req['queryResult']['parameters'].get('email')[0]
	except:
		email = req['queryResult']['parameters'].get('email')

	try:
		bookid = req['queryResult']['parameters'].get('bookid')[0]
	except:
		bookid = req['queryResult']['parameters'].get('bookid')


	action = req['queryResult'].get('action')

	try:
		feedback = req['queryResult']['parameters'].get('feedback')[0]
	except:
		feedback = req['queryResult']['parameters'].get('feedback')		

	additionalquery = ""
	count = starttime = endtime = False

	if date:
		date = dateutil.parser.parse(date).date()
	else:
		date = datetime.now().date()

	if action in ['askconferenceroom','checkconferenceavailablity']:

		additionalquery += "WHERE date='%s'"%(date)

		if timeperiod:
			starttime = str(dateutil.parser.parse(timeperiod.get('startTime')).time())
			endtime = str(dateutil.parser.parse(timeperiod.get('endTime')).time())
			additionalquery += " AND in_time>='%s' or out_time<='%s'"%(starttime,endtime)
			wherecondition = True

		slots = getbookedslots(date)

		available = True

		if starttime and endtime:
			for row in slots:
				if (row['from_time']>=endtime or row['to_time']<=starttime) == False:
					available = False

		if available and starttime and endtime:				
			status = 'This slot is available do you want to confirm'
		else:
			if starttime and endtime:
				status = 'This slot is not available %s these slots are already booked on %s. Please choose some other slots'%(slots,date)
			else:
				if slots:
					status = '%s these slots are already booked on %s. Please choose some other slots'%(slots,date)
				else:
					status = 'All slots are free'			
		
		if available and starttime and endtime:	
			nextintent = {}
			nextintent['name'] = "checkconferenceavailablity"
			nextintent['languageCode'] = "en-US"
			nextintent['parameters'] = {}		
			responsedetails['followupEventInput'] = nextintent	

	if action in ['bookconferenceroom']:

		additionalquery += "WHERE date='%s'"%(date)

		if timeperiod:
			starttime = str(dateutil.parser.parse(timeperiod.get('startTime')).time())
			endtime = str(dateutil.parser.parse(timeperiod.get('endTime')).time())
			additionalquery += " AND in_time>='%s' or out_time<='%s'"%(starttime,endtime)
			wherecondition = True

		slots = getbookedslots(date)

		available = True

		if starttime and endtime:
			for row in slots:
				if (row['from_time']>=endtime or row['to_time']<=starttime) == False:
					available = False

		if available and starttime and endtime:		

			query = "INSERT INTO meeting_room(date,in_time,out_time,status,reason,user_name) VALUES('%s','%s','%s','%s','%s','%s')"%(date,starttime,endtime,1,purpose,email)
			resp = db.engine.execute(query)
			bookid = resp.lastrowid
			status = "Booked successsfully, Booking ID: %s"%(bookid)			
		else:
			if starttime and endtime:
				status = 'This slot is not available %s these slots are already booked on %s. Please choose some other slots'%(slots,date)
			else:
				if slots:
					status = '%s these slots are already booked on %s. Please choose some other slots'%(slots,date)
				else:
					status = 'All slots are free'		


	if action in ['cancelconferenceroom']:

		if bookid:
			query = text("SELECT count(*) FROM meeting_room WHERE id='%s' AND user_name='%s'"%(bookid,email))
			booking_exist = db.engine.execute(query).fetchone()
			booking_exist = booking_exist[0]
			if booking_exist and bookid:
				val = text("UPDATE meeting_room SET status=0 WHERE id='%s'"%(bookid))
				val = db.engine.execute(val)
				status = 'successfully canceled'
			else:
				status = 'email is mismatch'


	if action in ['feedback']:

		positive = 0
		negative = 0
		neu = 0
		ss = sid.polarity_scores(feedback)
		sentiment = {}
		for k in ss:
			if k=='neg':
				negative= ss[k]
			if k=='neu':
				neu= ss[k]
			if k=='pos':
				positive= ss[k]
			sentiment['positive'] = positive
			sentiment['negative'] = negative
			sentiment['neutral'] = neu

		maximum = max(sentiment.iteritems(), key=operator.itemgetter(1))[0]

		val = text("UPDATE meeting_room SET feedback='%s', sentiment='%s' WHERE id='%s'"%(feedback,maximum,bookid))
		val = db.engine.execute(val)
		status = 'Feedback updated. Sentiment: %s'%(maximum)

	responsedetails['fulfillmentText'] = status
	responsedetails['outputContexts'] = req['queryResult']['outputContexts']

	return jsonify(responsedetails)


if __name__ == "__main__":
	# app.run(debug=True,host='0.0.0.0')  
    app.run(debug=True)