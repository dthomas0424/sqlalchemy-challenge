# Import the dependencies.
from flask import Flask, jsonify, request
import numpy as np
import datetime as dt
from datetime import timedelta
from datetime import datetime

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save reference to the tables
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)
Base.metadata.create_all(engine)


#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    return(
        f"Hawaii Climate API App<br/>"
        f"Available routes:<br>"
        f"/api/v1.0/precipitation<br/> "
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/> "
        f"/api/v1.0/start<br/>" 
        f"/api/v1.0/start/end<br/>"
        f"Enter Date as 'YYYY-MM-DD' in place of 'start' and/or 'end'.<br/>"
    )


# Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
        
    end_date = dt.date(2017, 8, 23)
    start_date = end_date - dt.timedelta(days=365)
    
        
    precipitation = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date >= start_date, measurement.date <= end_date).all()
    session.close()
    
        
    precip_results = {date: prcp for date, prcp in precipitation}
    return jsonify(precip_results)


#Return a JSON list of stations from the dataset
@app.route("/api/v1.0/stations")
def stations():
       
    station_results = session.query(station.name).all()
    session.close()

    
    stations = list(np.ravel(station_results))
    return jsonify(stations)


#Query the dates and temperature observations of the most-active station for the previous year of data.    
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    end_date = dt.date(2017, 8, 23)
    start_date = end_date - dt.timedelta(days=365)
       
    
    MAS_id_temps = session.query(measurement.date, measurement.tobs).filter(measurement.station == 'USC00519281', \
                                                                       measurement.date >= start_date, \
                                                                       measurement.date <= end_date).all()
    
     
    tobs = [{"date": date, "temperature": temp} for date, temp in MAS_id_temps]

    #Return a JSON list of temperature observations for the previous year.
    return jsonify(tobs)


#Return a JSON list of the minimum temperature, the average temperature, and the maximum temperature for a specified start or start-end range
@app.route('/api/v1.0/<start>')
def get_temp_stats(start):
    session = Session(engine)
    
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d')
    except ValueError:
        return jsonify({"error": "Invalid start date (date not available) or Invalid start date format. Use YYYY-MM-DD."}), 400

    #For a specified start, calculate min, avg and max for all the dates greater than or equal to the start date
    temp_stats=session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).all()
    
    
    temp_data = {
        "start_date": start_date.strptime(start,'%Y-%m-%d'),
        "MIN": temp_stats[0][0],
        "AVG": temp_stats[0][1],
        "MAX": temp_stats[0][2]
    }
    session.close()
    # Return the JSON response
    return jsonify(temp_data)

#For a specified start date and end date, calculate min, avg an max for the dates from the start date to the end date
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    session = Session(engine)
    start_date = dt.datetime.strptime(start,'%Y-%m-%d')
    end_date = dt.datetime.strptime(end,'%Y-%m-%d')
    
    temp_stats=session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter((measurement.date >= start_date),(measurement.date <= end_date)).all()
    
    if not temp_stats:
        return jsonify({"error": "No data found for the specified date range."}), 404

    
    temp_data = {
        "start_date": start_date.strptime(start,'%Y-%m-%d'), 
        "end_date": end_date.strptime(end,'%Y-%m-%d'),
        "MIN": temp_stats[0][0],
        "AVG": temp_stats[0][1],
        "MAX": temp_stats[0][2]
    }
        
    session.close()
    # Return the JSON response
    return jsonify(temp_data)


if __name__ == "__main__":
    app.run(debug=True)   