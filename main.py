#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime, date, timedelta
from flask import jsonify, request, Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import dateutil.parser

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://jarvis:MarvelIron@localhost/jarvis'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return 'Jarvis API - Running'

def getbookedslots(date):
	additionalquery = "WHERE date='%s'"%(date)
	query = text("SELECT in_time, out_time  FROM meeting_room " + additionalquery)
	resp = db.engine.execute(query)
	slots = []
	for row in resp:
		temp = {}
		temp['from_time'] = row[0]
		temp['to_time'] = row[1]
		slots.append(temp)	
	return slots

@app.route('/availability', methods=['POST'])
def availability():

	responsedetails = {}

	req = request.get_json(force=True)

	date = req['queryResult']['parameters'].get('date')
	availability = req['queryResult']['parameters'].get('Availability')
	timeperiod = req['queryResult']['parameters'].get('time-period')

	additionalquery = ""
	count = starttime = endtime = False

	if date:
		date = dateutil.parser.parse(date[0]).date()
	else:
		date = datetime.now().date()

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

	if available:				
		status = 'This slot is available do you want to confirm'
	else:
		status = 'This slot is not available %s these slots are already booked on %s. Please choose some other slots'%(slots,date)

	responsedetails['fulfillmentText'] = status
	responsedetails['outputContexts'] = req['queryResult']['outputContexts']

	return jsonify(responsedetails)


if __name__ == "__main__":  
    app.run(debug=True)