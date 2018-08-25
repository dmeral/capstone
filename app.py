from flask import Flask, render_template, request, redirect
import requests
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.layouts import column, layout, widgetbox,row

#import simplejson as json 
import pandas as pd
import numpy as np
from bokeh.io import output_file, output_notebook, show
import os
import pickle
from bokeh.io import show, save, output_notebook, export_png
from bokeh.models.widgets import DataTable, TableColumn, HTMLTemplateFormatter
from bokeh.models import (
    ranges,
    ColumnDataSource,
    CustomJS,
    HoverTool,
    ContinuousColorMapper,
    LabelSet,
    Label,
    LogColorMapper,
    LogTicker, 
    FixedTicker,
    BasicTicker,
    Dropdown,
    ColorBar, 
    LinearColorMapper,
    Legend,
    Whisker
)

from bokeh.plotting import figure, output_file, show
## This is where we get the state data from:
from bokeh.sampledata.us_states import data as states
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.palettes import RdYlBu11 as palette
from bokeh.palettes import Category20
lat_inkm = 111.132 ## at around lat = 45degrees from the wiki latitude page
lon_inkm = 78.847 ## at around lat = 45degrees from the wiki latitude page

df_state_slope_cluster_aslope_acolor = pickle.load(open("df_state_slope_cluster_aslope_acolor.pck", "rb"))
df_state_slope_clusters = pickle.load(open("df_state_slope_clusters.pck", "rb"))
pay_count = pickle.load(open("pay_count.pck", "rb"))
#license_state = pickle.load(open("clustering_data.pck", "rb"))
estimator_columns = pickle.load(open("estimator_columns.pck", "rb"))
estimator_model = pickle.load(open("estimator_model.pck", "rb"))
features_mean_cost = pickle.load(open("features_mean_cost.pck", "rb"))
features_total_cost = pickle.load(open("features_total_cost.pck", "rb"))
features_count = pickle.load(open("features_count.pck", "rb"))
df_total_cost =  pickle.load(open("df_total_cost.pck", "rb"))
df_mean_cost =  pickle.load(open("df_mean_cost.pck", "rb"))
df_count =  pickle.load(open("df_count.pck", "rb"))

def ordinal_num(num):
    if num%10==1:
        return str(num)+'st'
    elif num%10==2:
        return str(num)+'nd'
    elif num%10==3:
        return str(num)+'rd'
    else:
        return str(num)+'th'

def datatable(df):
    source = ColumnDataSource(data=df)
    columns = [TableColumn(field=df.columns[0], title=df.columns[0]),
               TableColumn(field=df.columns[1], title=df.columns[1])]
    data_table = DataTable(source=source, columns=columns, width=400)
    return data_table

def features_bar(order,xs,ys,yerrs):
    feature_dict = {'gdp': 'GDP', 
                'population': "Population", 
                'md2do': "MD:DO Ratio", 
                'nurses_never': "Nurse Comm. Nev.",
                'nurses_usually': "Nurses Comm. Usual.",
                'nurses_always': "Nurses Comm. Alw.",
                'doctors_never': "Docs Comm. Nev.",
                'doctors_usually': "Docs Comm. Usual.",
                'doctors_always': "Docs Comm. Alw.",
                'error_disc': "Error Disclosure",
                'time_after_treatment': "Time All. Aft. Treatment",
                'time_after_discovery': "Time All. Aft. Discovery",
                'max_time': "Max. Time All.",
                'cap': "P.O. Cap",
                'cap_death_injury': "P.O. Cap (Death/Serious Injury)"}
    p = figure(plot_width=400, plot_height=600, y_axis_label='Feature Importance',
           y_range= ranges.Range1d(start=0,end=0.35))
    p.yaxis.axis_label_text_font_size = "15pt"
    base, lower, upper = [], [], []
    err_xs = []
    err_ys_low = []
    err_ys_up = []
    #xs=range(X.shape[1])
    #ys=importances[indices]
    #yerrs=std[indices]
    for x, y, yerr in zip(xs, ys, yerrs):
        err_xs.append(x)
        err_ys_low.append(y - yerr)
        err_ys_up.append(y + yerr)
    base = xs
    lower = err_ys_low
    upper = err_ys_up
    source_error = ColumnDataSource(data=dict(base=base, x=order, lower=lower, upper=upper, values=ys))
    p.vbar(source=source_error,x='base',top='values',bottom=0,width=0.8,color='firebrick')
    p.add_layout(Whisker(source=source_error, base="base", upper="upper", lower="lower", level='overlay'))
    p.xaxis.ticker = base
    label_dict = {}
    for num,label in zip(base,order):
        label_dict[num]=feature_dict[label]
    p.xaxis.major_label_overrides = label_dict
    p.xaxis.major_label_orientation = np.pi/4
    p.xaxis.major_label_text_font_size = "12pt"
    return(p)


def create_plot_old(state):
    #print(state)
    p = figure(plot_width=700, plot_height=500, x_axis_label='Years', y_axis_label='Malpractice cases filed per 1,000,000')
    p.xaxis.axis_label_text_font_size = "15pt"
    p.yaxis.axis_label_text_font_size = "15pt"
    rank = int(df_state_slope_cluster_aslope_acolor[df_state_slope_cluster_aslope_acolor['state']==state]['cl_colors'])
    cur_states = list(df_state_slope_cluster_aslope_acolor[df_state_slope_cluster_aslope_acolor["cl_colors"]==rank]["state"])
    states_title = str()
    #print(cur_states)
    for x in cur_states:
        states_title = states_title+x+', '
    if len(cur_states)>8:
        sel_states = list(np.random.choice(cur_states,size=8,replace=False))
        sel_states.sort()
        if state in sel_states:
            sel_states.pop(sel_states.index(state))
            cur_states = [state]+sel_states
            #print('if',cur_states)
        else:
            cur_states = [state]+sel_states[:7]
            #print('else',cur_states)
        states_title = str()
        for x in cur_states:
            states_title = states_title+x+', '
        p.title.text = states_title[:-2]+" among others (Ranking "+str(rank)+")."
    else:
        p.title.text = states_title[:-2]+" (Ranking "+str(rank)+")."
    
    for state_, color in zip(cur_states, Category20[20]):
        curve = pay_count[state_,"count_per_1000000"]
        #plt.plot(range(1990,2018),curve,label=state,marker='.')
        r = p.line(curve.index, curve,line_width=2, color=color, alpha=1.,
                   muted_color=color, muted_alpha=0.2, legend=state_)
        if state_!=state:
            r.muted=True
    p.legend.location = "top_right"
    p.legend.click_policy="mute"
    return(p)

def create_plot(state,metric):
    mn = ["pay_per_case","count_per_1000000","total_pay"][metric]
    if metric==0:
        y_ax_label = 'Average Payout for Cases.'
    elif metric==1:
        y_ax_label = 'Cases Filed Per Million.'
    elif metric==2:
        y_ax_label = 'Total Annual State Payout.'
    #print(state,mn)
    p = figure(plot_width=400, plot_height=400, x_axis_label='Years') #, y_axis_label=y_ax_label)
    p.xaxis.axis_label_text_font_size = "15pt"
    p.yaxis.axis_label_text_font_size = "15pt"
    rank = int(df_state_slope_clusters[df_state_slope_clusters['state']==state]['cluster_slope_'+mn])
    cur_states = list(df_state_slope_clusters[df_state_slope_clusters["cluster_slope_"+mn]==rank]["state"])
    states_title = str()
    #print(cur_states)
    for x in cur_states:
        states_title = states_title+x+', '
    if len(cur_states)>4:
        sel_states = list(np.random.choice(cur_states,size=4,replace=False))
        sel_states.sort()
        if state in sel_states:
            sel_states.pop(sel_states.index(state))
            cur_states = [state]+sel_states
            #print('if',cur_states)
        else:
            cur_states = [state]+sel_states[:3]
            #print('else',cur_states)
        states_title = str()
        for x in cur_states:
            states_title = states_title+x+', '
        p.title.text = y_ax_label #+" for "+states_title[:-2]+" among others."
        p.title.text_font_size = "18pt"
    else:
        p.title.text = y_ax_label #+" for "+states_title[:-2]+"."
        p.title.text_font_size = "18pt"
    
    for state_, color in zip(cur_states, Category20[20]):
        curve = pay_count[state_,mn]
        #plt.plot(range(1990,2018),curve,label=state,marker='.')
        r = p.line(curve.index, curve,line_width=2, color=color, alpha=1.,
                   muted_color=color, muted_alpha=0.2, legend=state_)
        if state_!=state:
            r.muted=True
    p.legend.location = "top_left"
    p.legend.click_policy="mute"
    return(p)

app = Flask(__name__)

@app.route('/index',methods=['GET','POST'])
def index():
  state_xs = pickle.load(open("state_xs.pck", "rb"))
  state_ys = pickle.load(open("state_ys.pck", "rb"))
  state_names = pickle.load(open("state_names.pck", "rb"))
  state_rates = pickle.load(open("state_rates.pck", "rb"))
  state_clusters = pickle.load(open("state_clusters.pck", "rb"))
  cluster_label = pickle.load(open("cluster_label.pck", "rb"))
  slope_pay_per_case = pickle.load(open("slope_per_case.pck", "rb"))
  slope_count_per_1000000 = pickle.load(open("slope_count_per_1000000.pck", "rb"))
  slope_total_pay = pickle.load(open("slope_total_pay.pck", "rb"))
  color_mapper = LinearColorMapper(palette=palette) 
  color_mapper = LinearColorMapper(palette=palette) #, low=min(slope_count_per_1000000), high=max(slope_count_per_1000000))
  source = ColumnDataSource(data=dict(
    x=state_xs,
    y=state_ys,
    name=state_names,
    clusters=state_clusters,
    cluster_label=cluster_label,
    slopes1=slope_pay_per_case,
    slopes2=slope_count_per_1000000,
    slopes3=slope_total_pay,
  ))
  TOOLS = "pan,wheel_zoom,reset,hover,save"
  p = figure(#title="Change in the number of malpractice cases filed per a million citizens per states, 1990-2018", 
    plot_width=int((max(max(state_xs))-min(min(state_xs)))*lon_inkm/4.5), 
    plot_height=int((max(max(state_ys))-min(min(state_ys)))*lat_inkm/4.5), tools=TOOLS,
    x_axis_location=None, y_axis_location=None
  )
  p.grid.grid_line_color = None
  mypatches = p.patches('x', 'y', source=source,
          fill_color={'field': 'slopes2', 'transform': color_mapper},
          fill_alpha=0.7, line_color="gray", line_width=0.5)
  color_bar = ColorBar(color_mapper=color_mapper, ticker=BasicTicker(),
                     label_standoff=12, border_line_color=None, location=(0,0),major_label_text_font_size="14pt")
  p.add_layout(color_bar, 'right')
  #HoverTool(tooltips=None, callback=callback, renderers=[cr])
  hover = p.select_one(HoverTool) #(tooltips=None, callback=callback, renderers=[mypatches]))
  hover.point_policy = "follow_mouse"
  hover.tooltips ="""
    <font size="3">State: <strong>@name</strong> </font> <br>
    <font size="3">Average changes over the last 27 years in...</font> <br>
    <font size="3">...mean state payout: <strong>$@slopes1 </strong> </font> <br>
    <font size="3">...number of cases/mil: <strong>@slopes2 cases per million</strong> </font> <br>
    <font size="3">...total state payout: <strong>$@slopes3</strong> </font> <br>
  """
  #output_notebook()
  callback = CustomJS(args=dict(source=source, patches=mypatches), code="""
    var selected_slopes = cb_obj.value;
    patches.glyph.fill_color.field = selected_slopes;
    source.change.emit();
  """)
  menu = [("mean state payout ($)", "slopes1"), 
        ("number of cases per million", "slopes2"), 
        ("total state payout ($)", "slopes3")]
  dropdown = Dropdown(menu=menu, label="Select option to see change in...", button_type="danger")
  dropdown.js_on_change('value', callback)
  layout_ = column(children=[dropdown,p],sizing_mode='fixed')
  script, div = components(layout_)
  #print script
  return render_template('index.html',script=script, div=div)

@app.route('/about',methods=['GET','POST'])     
def about():
    if request.method == 'GET':
        return render_template('about.html',message="Please select state.")
    if request.method == 'POST':
        state = request.form['state']
        if state=="":
            return render_template('about.html',message="Please select state.")
        #plot = create_plot(state,1)
        plot_mini1 = create_plot(state,0)
        plot_mini2 = create_plot(state,1)
        plot_mini3 = create_plot(state,2)
        bar1 = features_bar(features_mean_cost[0],
                            features_mean_cost[1],
                            features_mean_cost[2],
                            features_mean_cost[3])
        bar2 = features_bar(features_count[0],
                            features_count[1],
                            features_count[2],
                            features_count[3])
        bar3 = features_bar(features_total_cost[0],
                            features_total_cost[1],
                            features_total_cost[2],
                            features_total_cost[3])
        datatab1 = datatable(df_mean_cost)
        datatab2 = datatable(df_count)
        datatab3 = datatable(df_total_cost)
        layoutx = layout([[plot_mini1,plot_mini2,plot_mini3],
                          [bar1,bar2,bar3],
                          [datatab1,datatab2,datatab3]])
        script, div = components(layoutx)
        rank1 = df_mean_cost[df_mean_cost["State"]==state].index[0]
        rank1_ = ordinal_num(rank1+1)
        rank2 = df_count[df_count["State"]==state].index[0]
        rank2_ = ordinal_num(rank2+1)
        rank3 = df_total_cost[df_total_cost["State"]==state].index[0]
        rank3_ = ordinal_num(rank3+1)
        summary = "Your state ranks as "+rank1_+" in the average payout of a malpractice case, "+rank2_+" in the total annual number of malpractice cases per million citizens, and "+rank3_+" in the total amount that is spent on malpractice cases by practitioners and institutions."
        return render_template('about.html',script=script, div=div,
                               state=state,message="You have selected "+request.form['state']+".",
                               summary=summary,rank1=rank1_,rank2=rank2_,rank3=rank3_)


@app.route('/estimator',methods=['GET','POST'])     
def estimator():
    if request.method == 'GET':
        return render_template('estimator.html', payout="$0")
    if request.method == 'POST':
        estimator_list = [request.form['workstat'],
                          request.form['licnfeld'],
                          request.form['practage'],
                          request.form['algnnatr'],
                          request.form['alegatn1'],
                          request.form['alegatn2'],
                          request.form['outcome'],
                          request.form['paytype'],
                          request.form['ptage'],
                          request.form['ptgender'],
                          request.form['pttype']]
        patient_vector = np.zeros(len(estimator_columns))
        for el in estimator_list:
            if el in estimator_columns:
                patient_vector[estimator_columns[el]] = 1
            else:
                title = el.split('_')
                patient_vector[estimator_columns[title[0]+"_unknown"]] = 1
        final_payout=str('${:,.2f}'.format(int(round(estimator_model.predict([patient_vector])[0],-2))))
        selections = str(request.form)
        return render_template('estimator.html', payout=final_payout, selections=selections)

if __name__ == '__main__':
    app.run(debug=False)
