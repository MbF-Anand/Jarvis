#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime, date, timedelta
from flask import jsonify, request, Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://jarvis:MarvelIron@localhost/jarvis'
db = SQLAlchemy(app)


@app.route('/')
def index():
    return 'Jarvis API - Running'



@app.route('/getmbfintent', methods=['POST'])
def getmbfintent():

	data = request.json['intentDetails']
	responsedetails = {}    
	iname = "%%"+data['intent_name']+"%%"
	itype = "%%"+data['intent_type']+"%%"

	query = """SELECT intent_response FROM mbf_assistant where intent_name like "%s" AND intent_type like "%s" """%(iname,itype)
	resp = db.engine.execute(query)  

	responsedetails['status'] = 'none'
	for row in resp:
		responsedetails['status'] = 'success'
		responsedetails['message'] = row[0]

	return jsonify(responsedetails)


if __name__ == "__main__":  
    app.run(debug=True)