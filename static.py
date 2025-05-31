from data_quality import load_dataframe, data_quality_check, overview, data_quality_recommendations
from maintenance import convert_numpy
from flask import Flask, render_template, request, session, redirect, url_for
import json
from datetime import datetime
import numpy as np

app = Flask(__name__)
df = load_dataframe(r'/Users/sam-disclosed/Downloads/Total Clustered People + Event.csv')
data_quality = data_quality_check(df)
overview_data = overview(df, data_quality)
data_quality_recs = data_quality_recommendations(df, overview_data, data_quality)
data_quality = convert_numpy(data_quality)
overview_data = convert_numpy(overview_data)
data_quality_recs = convert_numpy(data_quality_recs)


@app.route('/overview')
def index():
    return render_template('index.html', 
                           overview=overview_data, 
                           year=datetime.now().year)


@app.route('/datatype-analysis')
def datatype_analysis():    
    return render_template(
        'datatype_analysis.html',
        data_quality=data_quality,
        year=datetime.now().year
    )

@app.route('/data-quality-checklist')
def data_quality_checklist():
    safe_data = convert_numpy(data_quality_recs)
    return render_template(
        'data_quality_checklist.html',
        data_quality_recommendations = safe_data,
        year=datetime.now().year
    )

if __name__ == '__main__':
    app.run(debug=True)