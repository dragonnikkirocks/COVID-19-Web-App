from flask import Flask,render_template,url_for
import requests
import json
import logging
import pandas as pd
import numpy as np
import datetime
from prettytable import PrettyTable
from datetime import datetime as dt
from bokeh.models import DatetimeTickFormatter


from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.resources import INLINE
from bokeh.models.tools import HoverTool


now = datetime.datetime.now()
today = now.strftime("%d.%m.%Y")



logging.basicConfig(level=logging.DEBUG)

app= Flask(__name__)


rki_url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/ArcGIS/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&time=&geometry=&geometryType=esriGeometryEnvelope&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&returnGeodetic=false&outFields=*&returnGeometry=false&returnCentroid=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pjson"

def process_by_region():
    place_list=[159,172,176,193,194,200,202,205]
    df_list = list()
    kwargs =dict()
    count =1
    for element in place_list:
        rki_region_url = rki_url+ "&objectIds="+str(element)
        response = requests.get(rki_region_url)
        assert response.status_code == 200
        data_region = json.loads(response.text)
        region_info_generation(data_region,element)
        file_name = 'data'+str(element)+'.json'
        df_Region = pd.read_json(file_name,orient='split')
        kwargs['Cases'+str(count)] = df_Region['Cases'].to_list()[-1]
        kwargs['deaths'+str(count)] = df_Region['deaths'].to_list()[-1]
        kwargs['death_rate'+str(count)] = round(df_Region['death_rate'].to_list()[-1],3)
        kwargs['cases_7_bl'+str(count)] = df_Region['cases_7_bl'].to_list()[-1]
        kwargs['last_update'] = df_Region['last_update'].to_list()[-1]

        count+=1
    return kwargs

 
def region_info_generation(data_region,element):
    file_name = 'data'+str(element)+'.json'
    df_Region = pd.read_json(file_name,orient='split')
    latestDate = str(df_Region['last_update'].tolist()[-1])
    for feature in data_region['features']:
        last_u = feature['attributes']['last_update'].split()[0][:-1]
        if latestDate!=last_u:
            #print("Latest update as in local file ",latestDate)
            #print("Last update in url json", last_u)
            #if new date then update the file
            s = pd.Series([feature['attributes']['cases'], 
                           feature['attributes']['GEN']+" "+ feature['attributes']['BEZ'],
                            feature['attributes']['deaths'],
                           feature['attributes']['death_rate'], 
                           feature['attributes']['cases7_bl'],last_u], 
                           index=["Cases", "place", "deaths", "death_rate","cases_7_bl","last_update"])

            df_Region =df_Region.append(s, ignore_index=True)
            df_Region.to_json('data'+str(element)+'.json', orient='split',indent=5)




    
def process_place(filename):
    df_stadt = pd.read_json (filename,orient='split')
    x = PrettyTable()
    x.border=True
    x.left_padding_width =2
    x.right_padding_width =2
    deaths = df_stadt['deaths'].to_list()
    cases =df_stadt['Cases'].to_list()
    death_rate = df_stadt['death_rate'].to_list() 
    death_rate = [round(i,3) for i in death_rate]
    cases_7_bl = df_stadt['cases_7_bl'].to_list()
    Date = df_stadt['last_update'].to_list()
    x.add_column("Total No of deaths", deaths)
    x.add_column("Death Rate", death_rate)
    x.add_column("Cases in the last 7 days ", cases_7_bl)
    x.add_column("Total No of Cases", cases)
    x.add_column("Updated Date",Date)
    html_tabel1 = x.get_html_string() 

    return html_tabel1

def datetime(x):
    return np.array(x, dtype=np.datetime64)

def graph_cases(filename):
    df_Region =pd.read_json(filename,orient='split')
    cases = list(df_Region['Cases'])
    days =df_Region['last_update'].to_list()
    days = [pd.datetime.strptime(x,'%d.%m.%Y') for x in days]
    p=figure(plot_width=500,plot_height=300,x_axis_type='datetime', x_axis_label="days", y_axis_label="Total no of COVID-19 cases")
    p.circle(days, cases, color='blue', fill_color='white', size=10)
    p.line(days,cases,legend_label="Total Reported COVID-19 Cases", line_width=2,line_color ="blue")
    p.legend.location = "top_left"
    p.xaxis.formatter=DatetimeTickFormatter(days=["%d.%m.%Y"])
    p.xgrid.grid_line_color = None
    p.add_tools(HoverTool(
    tooltips='<font face="Arial" size="3">Total cases : @y</font>',
    mode='vline'
    ))
    return p

def graph_cases_7_bl(filename):
    df_Region =pd.read_json(filename,orient='split')
    cases = list(df_Region['cases_7_bl'])
    days =df_Region['last_update'].to_list()
    days = [pd.datetime.strptime(x,'%d.%m.%Y') for x in days]
    p=figure(plot_width=500,plot_height=300,x_axis_type='datetime',
                               x_axis_label="days",y_axis_label="COVID-19 Cases over last 7 days",
                               sizing_mode="stretch_width")
    p.circle(days, cases, color='purple', fill_color='white', size=10)
    p.line(days,cases,legend_label="COVID-19 Cases over last 7 days", line_width=2,line_color ="purple")
    p.legend.location = "top_left"
    p.xaxis.formatter=DatetimeTickFormatter(days=["%d.%m.%Y"])
    p.xgrid.grid_line_color = None
    p.add_tools(HoverTool(
    tooltips='<font face="Arial" size="3"> @y</font>',
    mode='vline'
    ))
    return p

def graph_deaths(filename):
    df_Region =pd.read_json(filename,orient='split')
    deaths = list(df_Region['deaths'])
    #days = df_Region['last_update'].to_list()
    #days = pd.to_datetime(days)
    days =df_Region['last_update'].to_list()
    days = [pd.datetime.strptime(x,'%d.%m.%Y') for x in days]
    p=figure(plot_width=500,plot_height=300,x_axis_type='datetime',
                               x_axis_label="days",y_axis_label="Total no of deaths due to COVID-19",
                               sizing_mode="stretch_width")
    p.circle(days, deaths, color='red', fill_color='white', size=10)
    p.line(days,deaths,legend_label="Total deaths", line_width=2,line_color ="red")
    p.legend.location = "top_left"
    p.xaxis.formatter=DatetimeTickFormatter(days=["%d.%m.%Y"])
    p.xgrid.grid_line_color = None
    p.add_tools(HoverTool(
    tooltips='<font face="Arial" size="3">Total deaths : @y</font>',
    mode='vline'
    ))
    return p

def graph_deathrate(filename):
    df_Region =pd.read_json(filename,orient='split')
    deaths_rate = list(df_Region['death_rate'])
    days =df_Region['last_update'].to_list()
    days = [pd.datetime.strptime(x,'%d.%m.%Y') for x in days]
    p=figure(plot_width=500,plot_height=300,x_axis_type='datetime',
                               x_axis_label="days",y_axis_label="Death rate due to COVID-19",
                               sizing_mode="stretch_width")
    p.circle(days, deaths_rate, color='black', fill_color='white', size=10)
    p.line(days,deaths_rate,legend_label="Death Rate", line_width=2,line_color ="black")
    p.legend.location = "top_left"
    p.xaxis.formatter=DatetimeTickFormatter(days=["%d.%m.%Y"])
    p.xgrid.grid_line_color = None
    p.add_tools(HoverTool(
    tooltips='<font face="Arial" size="3">Death rate : @y{0.000}</font>',
    mode='vline'
    ))
    return p


@app.route('/')
def index():
    kwargs = process_by_region()
    return render_template('index_new.html',**kwargs)

    
@app.route('/karlsruhe')
def karlsruhe():
    filename ='data193.json'
    html_tabel1 =process_place(filename)
    p1 = graph_cases(filename)
    p2 = graph_cases_7_bl(filename)
    p3 =graph_deaths(filename)
    p4 = graph_deathrate(filename)
     
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script1,div1 = components(p1)
    script2,div2 = components(p2)
    script3,div3 = components(p3)
    script4,div4 = components(p4)
    kwargs = {'script': script1, 'div': div1,'js_resources':js_resources,'css_resources':css_resources,
                'script2': script2, 'div2': div2,
                'script3': script3, 'div3': div3,
                'script4': script4, 'div4': div4}
    
    return render_template('karlsruhe.html',html_tabel1=html_tabel1,**kwargs)
    

@app.route('/frankenthal')
def frankenthal():
    filename ='data159.json'
    html_tabel1 =process_place(filename)
    p1 = graph_cases(filename)
    p2 = graph_cases_7_bl(filename)
    p3 =graph_deaths(filename)
    p4 = graph_deathrate(filename)
     
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script1,div1 = components(p1)
    script2,div2 = components(p2)
    script3,div3 = components(p3)
    script4,div4 = components(p4)
    kwargs = {'script': script1, 'div': div1,'js_resources':js_resources,'css_resources':css_resources,
                'script2': script2, 'div2': div2,
                'script3': script3, 'div3': div3,
                'script4': script4, 'div4': div4}
    
    return render_template('frankenthal.html',html_tabel1=html_tabel1,**kwargs)

@app.route('/Germersheim')
def Germersheim():
    filename ='data172.json'
    html_tabel1 =process_place(filename)
    p1 = graph_cases(filename)
    p2 = graph_cases_7_bl(filename)
    p3 =graph_deaths(filename)
    p4 = graph_deathrate(filename)
     
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script1,div1 = components(p1)
    script2,div2 = components(p2)
    script3,div3 = components(p3)
    script4,div4 = components(p4)
    kwargs = {'script': script1, 'div': div1,'js_resources':js_resources,'css_resources':css_resources,
                'script2': script2, 'div2': div2,
                'script3': script3, 'div3': div3,
                'script4': script4, 'div4': div4}
    
    return render_template('Germersheim.html',html_tabel1=html_tabel1,**kwargs)

@app.route('/Breisgau')
def Breisgau():
    filename ='data205.json'
    html_tabel1 =process_place(filename)
    p1 = graph_cases(filename)
    p2 = graph_cases_7_bl(filename)
    p3 =graph_deaths(filename)
    p4 = graph_deathrate(filename)
     
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script1,div1 = components(p1)
    script2,div2 = components(p2)
    script3,div3 = components(p3)
    script4,div4 = components(p4)
    kwargs = {'script': script1, 'div': div1,'js_resources':js_resources,'css_resources':css_resources,
                'script2': script2, 'div2': div2,
                'script3': script3, 'div3': div3,
                'script4': script4, 'div4': div4}
    
    return render_template('Germersheim.html',html_tabel1=html_tabel1,**kwargs)


@app.route('/rheinpfalz')
def rheinpfalz():
    filename ='data176.json'
    html_tabel1 =process_place(filename)
    p1 = graph_cases(filename)
    p2 = graph_cases_7_bl(filename)
    p3 =graph_deaths(filename)
    p4 = graph_deathrate(filename)
     
    # grab the static resources
    js_resources = INLINE.render_js()
    css_resources = INLINE.render_css()

    script1,div1 = components(p1)
    script2,div2 = components(p2)
    script3,div3 = components(p3)
    script4,div4 = components(p4)
    kwargs = {'script': script1, 'div': div1,'js_resources':js_resources,'css_resources':css_resources,
                'script2': script2, 'div2': div2,
                'script3': script3, 'div3': div3,
                'script4': script4, 'div4': div4}
    
    return render_template('rheinpfalz.html',html_tabel1=html_tabel1,**kwargs)


@app.route('/contact')
def about():
    return render_template('contact.html')


if __name__=="__main__":
    app.run(debug=True)
