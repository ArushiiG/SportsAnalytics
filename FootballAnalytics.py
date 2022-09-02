#!/usr/bin/env python
# coding: utf-8

# In[93]:

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import pandas as pd
import numpy as np
from mplsoccer import VerticalPitch, Radar #For soccer pitches (built on matplotlib)
import matplotlib.pyplot as plt            #Basic python visualization 
from plotly.subplots import make_subplots  #Interactive visualizations
import plotly.graph_objects as go        
import streamlit as st  
import wikipedia
import requests
import json
from PIL import Image
import urllib.request
import matplotlib.lines as mlines

plt.style.use('default')

WIKI_REQUEST = 'http://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles='

@st.cache(allow_output_mutation=True)
def get_wiki_image(search_term):
    try:
        result = wikipedia.search(search_term, results = 1)
        wikipedia.set_lang('en')
        wkpage = wikipedia.WikipediaPage(title = result[0])
        title = wkpage.title
        response  = requests.get(WIKI_REQUEST+title)
        json_data = json.loads(response.text)
        img_link = list(json_data['query']['pages'].values())[0]['original']['source']
        return img_link        
    except:
        return 0

###############################Import data#################################################
df_players = pd.read_csv(r"filtered_players.csv")
df_shots = pd.read_csv(r"shots_modified.csv")
df_apps = pd.read_csv(r"appearances_modified.csv")

###############################Streamlit Setup#############################################
st.set_page_config(layout="wide")
st.session_state.playerlist = df_players["Player Name"]
player_df = st.session_state.playerlist


#Default Player1
default_ix1 = df_players.index[df_players["Player Name"]=='Harry Kane'].tolist()
default_ix1 = [str(integer) for integer in default_ix1]
default_ix1 = int("".join(default_ix1))

#Default Player2
default_ix2 = df_players.index[df_players["Player Name"]=='Mohamed Salah'].tolist()
default_ix2 = [str(integer) for integer in default_ix2]
default_ix2 = int("".join(default_ix2))

#Add side bar wi
with st.sidebar:
    st.title('Player Performance Analysis')
    st.sidebar.markdown('''##### Compare two forwards across Europe's top 5 leagues''')
    player1 = st.selectbox("Select Player 1",player_df, index = default_ix1)
    player2 = st.selectbox("Select Player 2",player_df, index = default_ix2)
    season1 = st.selectbox("Select Season",['2016','2017','2018','2019','2020'], index = 4) #Default season 2020
    st.subheader('Key Metrics')
    st.sidebar.markdown("""
    | Metric | Description |
    | --- | ---- |
    | xGoals (xG) | Expected Goals is a statistical measure of the quality of chances created |
    | xAssist |xG of shot resulting from a player's pass|
    | xChains |xG of every posession of the player|
    | Goals90 | Goals per 90mins |
    | Shots90 |Shots per 90mins |
    | xG90 |Expected Goals per 90mins |
    | xA90 |xG of shot resulting from a player's pass per 90mins|
    | xC90 |xG of every posession of the player per 90mins|
    """
    )

#Add x player logo
logo_image = Image.open("logo1.png")
logo_image = logo_image.resize((400,150), Image.ANTIALIAS)
col1, col2, col3 = st.columns((2,4,1))
with col2:
    st.image(logo_image)

#################################Player Images############################################
col1, col2, col3, col4,col5,col6 = st.columns((1,2,1,1,2,1))

#player1 image
with col2:
    f"### {player1}"
    wiki_image1 = get_wiki_image(player1)
    urllib.request.urlretrieve(
      wiki_image1,
       "player1.png")
    wiki_image1 = Image.open("player1.png")
    wiki_image1 = wiki_image1.resize((1000,1000), Image.ANTIALIAS)
    st.image(wiki_image1)
    
#player2 image
with col5:
    f"### {player2}"
    wiki_image2 = get_wiki_image(player2)
    urllib.request.urlretrieve(
      wiki_image2,
       "player2.png")
    wiki_image2 = Image.open("player2.png")
    wiki_image2 = wiki_image2.resize((1000,1000), Image.ANTIALIAS)
    st.image(wiki_image2)
    
##################################General information table#############################     
player1_details = df_players[df_players["Player Name"]==player1].iloc[:,2:7].values.flatten().tolist()
player2_details = df_players[df_players["Player Name"]==player2].iloc[:,2:7].values.flatten().tolist()
df1 = pd.DataFrame(list(zip(player1_details, player2_details)),
                   columns=([f'{player1}',f'{player2}']),
                   index = ['Age','Nationality','Position','Preferred Foot','Current Club'],
                   dtype = 'str')

df1 = df1.style.set_table_styles([{'selector': 'th.row_heading',
                                   'props': [('background-color', '#AFBCD6'),
                                             ("color", "black")]},
                                  {'selector': 'thead',
                                    'props': [('background-color', '#AFBCD6'),
                                              ("color", "white"),("font-size", "1.2rem")]}])

col1, col2, col3 = st.columns((1, 2, 1))

with col2:
    st.subheader("General Information")
    st.table(df1)

##################################Apply user filters#############################    
#filter shots and appearances for season and OpenPlay
df_shots = df_shots[df_shots["season"] == int(season1)]    
df_openshots = df_shots[df_shots["situation"] == 'OpenPlay'].copy()

#Apply pitch dimensions to the coordinates
df_openshots["positionX"] = round(df_openshots["positionX"]*105,2)
df_openshots["positionY"] = round(df_openshots["positionY"]*68,2)

#filter shots for player 1
df_openshots_player1 = df_openshots[df_openshots["shooterName"] == player1]
df_goals_player1 = df_openshots_player1[df_openshots_player1["shotResult"] == 'Goal']

#filter shots for player 2
df_openshots_player2 = df_openshots[df_openshots["shooterName"] == player2]
df_goals_player2 = df_openshots_player2[df_openshots_player2["shotResult"] == 'Goal']

#filter apperance table for all games for player 1 or player2 
df_app_player = df_apps[(df_apps.PlayerName == player1) | (df_apps.PlayerName == player2)].copy()

##################################Historical Trending#############################    
st.markdown("## Season Trends:")

color = {f'{player1}': '#FF0000',
         f'{player2}': '#008080'}

fig = make_subplots(
    rows=2, cols=3,
    column_widths=[0.5, 0.5,0.5],
    row_heights=[1.5,1.5],
    specs=[[ {"type": "bar"}, {"type": "bar"}, {"type": "bar"}],[ {"type": "bar"}, {"type": "bar"}, {"type": "bar"}]],
    subplot_titles=("Shots","Goals Scored","Assists", "Expected Goals", "Expected Goals per 90mins","Goals/Expected Goals"))

xG_data = df_app_player.groupby(['PlayerName','season'], as_index=False).agg(
    Goals = ("goals", sum),
    t90s = ("time",lambda x: sum(x)/90),
    Shots = ("shots", sum),
    xGoals=("xGoals", sum),
    Assists=("assists", sum),
    KP=("keyPasses", sum),
    played =("HomeTeam", "count"))

for lbl in xG_data['PlayerName'].unique():
    dfp = xG_data[xG_data['PlayerName']==lbl]
    #print(dfp)
    fig.add_traces(go.Line(x=dfp['season'], 
                          y=dfp['Shots'], 
                          name=lbl,
                          marker_color = color[lbl],
                          showlegend=False,
                             ),rows=1,cols=1)

for lbl in xG_data['PlayerName'].unique():
    dfp = xG_data[xG_data['PlayerName']==lbl]
    #print(dfp)
    fig.add_traces(go.Line(x=dfp['season'], 
                          y=dfp['Goals'], 
                          name=lbl,
                          marker_color = color[lbl],
                          showlegend=False,
                             ),rows=1,cols=2)


for lbl in xG_data['PlayerName'].unique():
    dfp = xG_data[xG_data['PlayerName']==lbl]
    #print(dfp)
    fig.add_traces(go.Line(x=dfp['season'], 
                          y=dfp['Assists'], 
                          name=lbl,
                          marker_color = color[lbl],
                          showlegend=False,
                             ),rows=1,cols=3)

for lbl in xG_data['PlayerName'].unique():
    dfp = xG_data[xG_data['PlayerName']==lbl]
    #print(dfp)
    fig.add_traces(go.Line(x=dfp['season'], 
                          y=dfp['xGoals'], 
                          name=lbl,
                          marker_color = color[lbl],
                          showlegend=True         # Show legend for only one chart
                             ),rows=2,cols=1)


for lbl in xG_data['PlayerName'].unique():
    dfp = xG_data[xG_data['PlayerName']==lbl]
    #print(dfp)
    fig.add_traces(go.Line(x=dfp['season'], 
                           y=dfp.xGoals/dfp.t90s, 
                           name=lbl,
                           marker_color = color[lbl],
                           showlegend=False),rows=2,cols=2)

for lbl in xG_data['PlayerName'].unique():
    dfp = xG_data[xG_data['PlayerName']==lbl]
    #print(dfp)
    fig.add_traces(go.Line(x=dfp['season'], 
                           y=dfp.Goals/dfp.xGoals, 
                           name=lbl,
                           marker_color = color[lbl],
                           showlegend=False),rows=2,cols=3)
    
fig.update_layout(autosize=False,height=500,
      margin=dict(l=10, r=10, t=30, b=0))
fig.update_layout(legend = dict(orientation = "h",   # show entries horizontally
                     xanchor = "center",yanchor = 'top',  # use center of legend as anchor
                     x = 0.5)) 

st.plotly_chart(fig, use_container_width=True)

###############################Radar Chart for Key metrics########################
st.markdown(f"## {season1} Analysis:")

st.markdown(f"##### Comparison of Key Metrics") 

df_apps1 = df_apps[df_apps["season"] == int(season1)]
df_app_player1 = df_apps1[df_apps1["PlayerName"] == player1].copy()     #Player 1 filter for apperances
df_app_player2 = df_apps1[df_apps1["PlayerName"] == player2].copy()       

# ### Player 1 Attributes
player1_time = np.sum(df_app_player1.time)              #Total time played (mins)
player1_90s = round(np.sum(df_app_player1.time)/90,2)   #Total 90s played (total time/90)
player1_goals = np.sum(df_app_player1.goals)            #Total goals scored
player1_goals_90s = round(player1_goals/player1_90s,2)  #Total goals scored per 90
player1_shots = np.sum(df_app_player1.shots)            #Total goals scored per 90
player1_shots_90s = round(player1_shots/player1_90s,2)
player1_xG = np.sum(df_app_player1.xGoals)
player1_xG_90s = round(player1_xG/player1_90s,2)
player1_xGChains = np.sum(df_app_player1.xGoalsChain)
player1_xGChains_90s = round(player1_xGChains/player1_90s,2)
player1_xAssist = np.sum(df_app_player1.xAssists)
player1_xAssist_90s = round(player1_xAssist/player1_90s,2)
player1_xGBuildup = np.sum(df_app_player1.xGoalsBuildup)
player1_xGBuildup_90s = round(player1_xGBuildup/player1_90s,2)
radarvalues1 = player1_goals_90s, player1_shots_90s, player1_xG_90s, player1_xGChains_90s, player1_xAssist_90s


# ### Player 2 Attributes
player2_time = np.sum(df_app_player2.time)
player2_90s = round(np.sum(df_app_player2.time)/90,2)
player2_goals = np.sum(df_app_player2.goals)
player2_goals_90s = round(player2_goals/player2_90s,2)
player2_shots = np.sum(df_app_player2.shots)
player2_shots_90s = round(player2_shots/player2_90s,2)
player2_xG = np.sum(df_app_player2.xGoals)
player2_xG_90s = round(player2_xG/player2_90s,2)
player2_xGChains = np.sum(df_app_player2.xGoalsChain)
player2_xGChains_90s = round(player2_xGChains/player2_90s,2)
player2_xAssist = np.sum(df_app_player2.xAssists)
player2_xAssist_90s = round(player2_xAssist/player2_90s,2)
player2_xGBuildup = np.sum(df_app_player2.xGoalsBuildup)
player2_xGBuildup_90s = round(player2_xGBuildup/player2_90s,2)
radarvalues2 = player2_goals_90s, player2_shots_90s, player2_xG_90s, player2_xGChains_90s, player2_xAssist_90s

params = ['Goals90','Shots90','xG90',
           'xC90', 'xA90']
low =  [0.0, 0, 0.0, 0.0, 0.0]
high = [1.5, 8, 1.2, 1.5, 0.5]

radar = Radar(params, 
              min_range=low, 
              max_range=high,
              ring_width=1.2)

fig, ax = radar.setup_axis(figsize=(8, 8),facecolor='None')

rings_inner = radar.draw_circles(ax=ax, facecolor='None', edgecolor='#fc5f5f')
radar_output = radar.draw_radar_compare(radarvalues1, radarvalues2, 
                                        ax=ax, 
                                        kwargs_radar={'facecolor': '#FF0000', 'alpha': 0.6}, 
                                        kwargs_compare={'facecolor': '#008080', 'alpha': 0.6})
radar_poly, radar_poly2, vertices1, vertices2 = radar_output
param_labels = radar.draw_param_labels(ax=ax, fontsize=15)  # draw the param labels
range_labels = radar.draw_range_labels(ax=ax, fontsize=10)  # draw the range labels
ax.scatter(vertices1[:, 0], vertices1[:, 1],
                     c='#FF0000', edgecolors='#FF0000', marker='o', s=150, zorder=2)
ax.scatter(vertices2[:, 0], vertices2[:, 1],
                     c='#008080', edgecolors='#008080', marker='o', s=150, zorder=2)

title1_text = ax.text(4, 6.0, player1, fontsize=15, color='#FF0000')
title2_text = ax.text(4, 5.5, player2, fontsize=15, color='#008080')

fig.set_facecolor('none')

col1, col2, col3 = st.columns((1, 2, 1))

with col2:
    st.pyplot(fig)

###########################Pie charts for body part of Goals################################

st.markdown("#### Open Play Insights")
st.markdown("##### Breakdown of Goals scored by Body Part")

df_shotType1 = df_goals_player1.groupby('shotType', as_index=False).agg(
    goals = ("shotResult", "count"))

df_shotType2 = df_goals_player2.groupby('shotType', as_index=False).agg(
    goals = ("shotResult", "count"))

fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.5, 0.5],
    row_heights=[0.5],
    specs=[[ {"type": "pie"}, {"type": "pie"}]])

fig.add_trace(go.Pie( 
             values=df_shotType1.goals, 
             labels=df_shotType1.shotType,
             legendgroup="group",
             hole=.4),
             row=1, col=1)

fig.add_trace(go.Pie(values=df_shotType2.goals, 
             labels=df_shotType2.shotType,
             legendgroup="group",
             hole=.4),
             row=1, col=2)

fig.update_layout(legend = dict(orientation = "h",   # show entries horizontally
                     xanchor = "center",yanchor = 'top',  # use center of legend as anchor
                     x = 0.5)) 
fig.update_layout(autosize=False,height = 300,
    margin=dict(l=10, r=10, t=30, b=0))

col1, col2, col3 = st.columns((1,4,1))

with col2:
    st.plotly_chart(fig, use_container_width=True)

###################### Shot Distribution (Heat Map) ##########################
st.markdown("##### Heat Map of Shots")
col1, col2 = st.columns(2)

pitch = VerticalPitch(pitch_type = 'custom',
                      pitch_length=105,
                      pitch_width= 68,
                      pitch_color='None',
                      line_color='#000009',
                      line_zorder=2,
                      half=True)

fig1, ax = pitch.draw(figsize=(15, 15))
fig1.set_facecolor('none')

kde1 = pitch.kdeplot(df_openshots_player1.positionX, df_openshots_player1.positionY, ax=ax,
                    # shade using 100 levels so it looks smooth
                    shade=True, levels=100,
                    # shade the lowest area so it looks smooth
                    # so even if there are no events it gets some color
                    shade_lowest=True,
                    cut=20,  # extended the cut so it reaches the bottom edge
                    cmap='Reds')
with col1:
    st.pyplot(fig1)

pitch = VerticalPitch(pitch_type = 'custom',
                      pitch_length=105,
                      pitch_width= 68,
                      pitch_color='None',
                      line_color='#000009',
                      line_zorder=2,
                      half=True)

fig2, ax = pitch.draw(figsize=(8, 8))
fig2.set_facecolor('none')

kde = pitch.kdeplot(df_openshots_player2.positionX, df_openshots_player2.positionY, ax=ax,
                    # shade using 100 levels so it looks smooth
                    shade=True, levels=100,
                    # shade the lowest area so it looks smooth
                    # so even if there are no events it gets some color
                    shade_lowest=True,
                    cut=20,  # extended the cut so it reaches the bottom edge
                    cmap='Blues')

with col2:
    st.pyplot(fig2)

#############################Shot Result pie chart###########################################

st.markdown("##### Shot Outcomes")

df_shotResults1 = df_openshots_player1.groupby('shotResult', as_index=False).agg(
    shots = ("shotResult", "count"))

df_shotResults2 = df_openshots_player2.groupby('shotResult', as_index=False).agg(
    shots = ("shotResult", "count"),
    xGoals=("xGoal", sum))

colors = {'MissedShots':'red', 'SavedShot':'green', 'ShotOnPost':'blue', 'BlockedShot':'black','Goal':'#b94b75'}
colors1 = ['red','green','blue', 'black','#b94b75']


fig = make_subplots(
    rows=1, cols=2,
    column_widths=[0.5, 0.5],
    row_heights=[0.5],
    specs=[[ {"type": "pie"}, {"type": "pie"}]])

fig.add_trace(go.Pie( 
             values=df_shotResults1.shots, 
             labels=df_shotResults1.shotResult,
             legendgroup="group",marker_colors=df_shotResults1['shotResult'].map(colors),
             hole=.4),
             row=1, col=1)

fig.add_trace(go.Pie(values=df_shotResults2.shots, 
             labels=df_shotResults2.shotResult,
             legendgroup="group",marker_colors=df_shotResults2['shotResult'].map(colors),
             hole=.4),
             row=1, col=2)

fig.update_layout(autosize=False,height= 350,
     margin=dict(l=10, r=10, t=30, b=1))

fig.update_layout(legend = dict(orientation = "h",   # show entries horizontally
                      xanchor = "center",  # use center of legend as anchor
                      x = 0.5,y=-0.1)) 

col1, col2, col3 = st.columns((1,4,1))

with col2:
    st.plotly_chart(fig, use_container_width=True)
#    st.markdown("##### Shot Results (color) from Open Play with xG (Size)")   

#############################Scatter Pitch Map with all shots###############################

#@st.experimental_memo(suppress_st_warning=True) 
def shots_scatterplot(shotresult):  
    if shotresult == "All":
        df_nGopenshots_player1 = df_openshots_player1.copy()
        df_nGopenshots_player2 = df_openshots_player2.copy()
    else:
        df_nGopenshots_player1 = df_openshots_player1[df_openshots_player1["shotResult"] == shotresult]
        df_nGopenshots_player2 = df_openshots_player2[df_openshots_player2["shotResult"] == shotresult]        
    # # Scatter Plot
    pitch = VerticalPitch(pitch_type = 'custom',
                  pitch_length=105,
                  pitch_width=68,
                  pitch_color='None',
                  half=True,  # half of a pitch
                  goal_type='line',
                  line_color='black')
    
    fig, axs = pitch.grid(ncols=2,figheight=10, 
                          title_height=0.08, 
                          endnote_space=0,
                          axis=False,
                          title_space=0, 
                          grid_height=0.85, 
                          endnote_height=0.05)
    
    #Plotting shots from open play 
    sc1 = pitch.scatter(df_nGopenshots_player1.positionX, df_nGopenshots_player1.positionY, 
                        ax=axs['pitch'][0],
                        c='None',
                        marker='o',
                        edgecolors=df_nGopenshots_player1['shotResult'].map(colors),
                        s=(df_nGopenshots_player1.xGoal* 1900) + 100)
    
    sc2 = pitch.scatter(df_nGopenshots_player2.positionX, df_nGopenshots_player2.positionY, 
                        ax=axs['pitch'][1],
                        c='None',
                        marker='o',
                        edgecolors=df_nGopenshots_player2['shotResult'].map(colors),
                        s=(df_nGopenshots_player2.xGoal* 1900) + 100)
       
    red_line = mlines.Line2D([], [], color='None', marker='o',
                              markersize=15,label='Missed Shot',markeredgecolor = 'red')
    green_line = mlines.Line2D([], [], color='None', marker='o',
                              markersize=15,label='Saved Shot',markeredgecolor = 'green')
    blue_line = mlines.Line2D([], [], color='None', marker='o',
                              markersize=15,label='Shot On Post',markeredgecolor = 'blue')
    yellow_line = mlines.Line2D([], [], color='None', marker='o',
                              markersize=15,label='Blocked Shot',markeredgecolor = 'black')
    goal_line1 = mlines.Line2D([], [], color='None', marker='o',
                              markersize=15,label='Goal',markeredgecolor = '#b94b75')
    
    
    fig.legend(handles=[red_line,blue_line,green_line,yellow_line,goal_line1] ,
               loc='upper right',
               title="Shot Result",
               title_fontsize='xx-large',
               prop={'size': 20}) 
    
    fig.legend(*sc1.legend_elements("sizes", num=6,func= lambda x: (x-100)/1900),
               loc='upper left',
               title="xG",
               title_fontsize='xx-large',
               prop={'size': 20})
    
    
    fig.set_facecolor('None')
    fig.suptitle("Shot Results (colour) from Open Play with xG (size)",c="black", fontsize=40)   
    st.pyplot(fig) 

shotresult = st.radio("",['All','MissedShots', 'SavedShot', 'ShotOnPost', 'BlockedShot','Goal'],            
                      horizontal =True,
                      index = 0)

shots_scatterplot(shotresult)

########################Top Assisters to the player###########################################

st.markdown("#### Player Relationships")
st.markdown("##### Most assists to selected players")

df_shots_player1 = df_shots[df_shots["shooterName"] == player1].copy()
df_shots_player2 = df_shots[df_shots["shooterName"] == player2].copy()

df_shots_player1["goal"] = df_shots_player1["shotResult"].apply(lambda g: 1 if g == 'Goal' else 0)
df_shots_player2["goal"] = df_shots_player2["shotResult"].apply(lambda g: 1 if g == 'Goal' else 0)

data1 = df_shots_player1.groupby('assisterName', as_index=True).agg(
    KeyPasses = ("goal", "count"),
    Assists = ("goal", sum),
    xGoals=("xGoal", sum)).sort_values(['xGoals'], ascending=False)

data2 = df_shots_player2.groupby('assisterName', as_index=True).agg(
    KeyPasses = ("goal", "count"),
    Assists = ("goal", sum),
    xGoals=("xGoal", sum)).sort_values(['xGoals'], ascending=False)

data1 = data1.head(10).style.set_table_styles([{'selector': 'th.row_heading',
                                   'props': [('background-color', '#AFBCD6'),
                                             ("color", "black")]},])

data2 = data2.head(10).style.set_table_styles([{'selector': 'th.row_heading',
                                   'props': [('background-color', '#AFBCD6'),
                                             ("color", "black")]},])

col1, col2 = st.columns(2)

with col1:
    st.table(data1)
    
with col2:
    st.table(data2)
    
########################Top Assist to###########################################
st.markdown("##### Most assists by selected players")

df_assists_player1 = df_shots[df_shots["assisterName"] == player1].copy()
df_assists_player2 = df_shots[df_shots["assisterName"] == player2].copy()

df_assists_player1["goal"] = df_assists_player1["shotResult"].apply(lambda g: 1 if g == 'Goal' else 0)
df_assists_player2["goal"] = df_assists_player2["shotResult"].apply(lambda g: 1 if g == 'Goal' else 0)

data1 = df_assists_player1.groupby('shooterName', as_index=True).agg(
    KeyPasses = ("goal", "count"),
    Assists = ("goal", sum),
    xAssist=("xGoal", sum)).sort_values(['xAssist'], ascending=False)

data2 = df_assists_player2.groupby('shooterName', as_index=True).agg(
    KeyPasses = ("goal", "count"),
    Assists = ("goal", sum),
    xAssist=("xGoal", sum)).sort_values(['xAssist'], ascending=False)

data1 = data1.head(10).style.set_table_styles([{'selector': 'th.row_heading',
                                   'props': [('background-color', '#AFBCD6'),
                                             ("color", "black")]},])

data2 = data2.head(10).style.set_table_styles([{'selector': 'th.row_heading',
                                   'props': [('background-color', '#AFBCD6'),
                                             ("color", "black")]},])

col1, col2 = st.columns(2)

with col1:
    st.table(data1)
    
with col2:
    st.table(data2)