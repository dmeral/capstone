from flask import Flask, render_template, request, redirect
import requests
from bokeh.plotting import figure
from bokeh.embed import components 
#import simplejson as json
import pandas as pd
import numpy as np
from bokeh.io import output_file, output_notebook, show
import os
import pickle
from bokeh.io import show, save, output_notebook, export_png
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    ContinuousColorMapper,
    LabelSet,
    Label,
    LogColorMapper, 
    LogTicker, 
    FixedTicker,
    ColorBar, 
    LinearColorMapper,
    Legend
)
from bokeh.plotting import figure, output_file, show
## This is where we get the state data from:
from bokeh.sampledata.us_states import data as states
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.palettes import PRGn11 as palette
from bokeh.palettes import Category20,Spectral11,Category10,PRGn11
import pickle
lat_inkm = 111.132 ## at around lat = 45degrees from the wiki latitude page
lon_inkm = 78.847 ## at around lat = 45degrees from the wiki latitude page

df_state_slope_cluster_aslope_acolor = pickle.load(open("df_state_slope_cluster_aslope_acolor.pck", "rb"))
pay_count = pickle.load(open("pay_count.pck", "rb"))
#license_state = pickle.load(open("clustering_data.pck", "rb"))

def create_plot(state):
    print(state)
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
            print('if',cur_states)
        else:
            cur_states = [state]+sel_states[:7]
            print('else',cur_states)
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

app = Flask(__name__)

@app.route('/',methods=['GET','POST'])
def index():
  state_xs = pickle.load(open("state_xs.pck", "rb"))
  state_ys = pickle.load(open("state_ys.pck", "rb"))
  state_names = pickle.load(open("state_names.pck", "rb"))
  state_rates = pickle.load(open("state_rates.pck", "rb"))
  state_clusters = pickle.load(open("state_clusters.pck", "rb"))
  cluster_label = pickle.load(open("cluster_label.pck", "rb"))
  color_mapper = LinearColorMapper(palette=palette) 
  source = ColumnDataSource(data=dict(
    x=state_xs,
    y=state_ys,
    name=state_names,
    rate=state_rates,
    clusters=state_clusters,
    cluster_label=cluster_label,
  ))
  TOOLS = "pan,wheel_zoom,reset,hover,save"
  p = figure(title="Change in the number of malpractice cases filed per a million citizens per states, 1990-2018", 
    plot_width=int((max(max(state_xs))-min(min(state_xs)))*lon_inkm/4.5), 
    plot_height=int((max(max(state_ys))-min(min(state_ys)))*lat_inkm/4.5), tools=TOOLS,
    x_axis_location=None, y_axis_location=None
  )
  p.grid.grid_line_color = None
  p.patches('x', 'y', source=source,
            fill_color='clusters',
            fill_alpha=0.7, line_color="gray", line_width=0.5)
  color_bar = ColorBar(color_mapper=color_mapper, 
                       label_standoff=12,
                       border_line_color=None,
                       location=(0,0),
                       major_label_text_font_size="14pt")
  p.add_layout(color_bar, 'right')
  hover = p.select_one(HoverTool)
  hover.point_policy = "follow_mouse"
  hover.tooltips ="""
    <font size="3">State: <strong>@name</strong> </font> <br>
    <font size="3">Change in the number of   </font> <br>
    <font size="3">malpractice cases: <strong>@rate per 1,000,000</strong> </font> <br>
    <font size="3">Ranking: <strong>@cluster_label</strong> </font>
  """
  script, div = components(p)
  return render_template('index.html',script=script, div=div)

@app.route('/about',methods=['GET','POST'])
def about():
    if request.method == 'POST':
      state = request.form['state']
      #plot = create_plot(stock,options)
      plot = create_plot(state)
      script, div = components(plot)
      return render_template('graph.html',script=script, div=div, state=state)
  #return render_template('about.html')

if __name__ == '__main__':
  app.run(debug=True)
