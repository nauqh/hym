import streamlit as st
import pandas as pd
import json

from utils.config import Config
from utils.riot import *
from utils.graph import *

st.set_page_config(
    page_title="Porostream",
    page_icon="app/img/favicon.png",
    layout="wide"
)

# NOTE: SETUP
cf = Config()
api = RiotAPI(cf.TOKEN)
df = load_data(cf.puuids)


# NOTE: LANDING
_, center, _ = st.columns([1, 10, 1])
with center:
    st.markdown("""
                <h1 style='text-align: center; font-weight: 600;
                    font-size: 6rem'>State of 
                <span style='background-color: #ffc300; padding: 0 0.5rem; color: #010A13; border-radius: 0.5rem'>HYM</span> 
                <span style='color: #ffc300; font-weight: 800'> > </span> 
                <br> Performance 2024</h1>""", unsafe_allow_html=True)
    st.markdown("""<h3 style='text-align: center; font-weight: 400;
                font-size: 2rem'>Dive into my team's journey in ARAM! Explore key metrics, trends, and insights from our analysis of recent matches.</h3>""",
                unsafe_allow_html=True)
    st.markdown("""
    <div style="display: flex; justify-content: center; align-items: center; column-gap: 1rem">
        <img src="https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=fafafa" alt="Python" />
        <img src="https://img.shields.io/badge/plotly%20-%2300416A.svg?&style=for-the-badge&logo=pandas&logoColor=white" alt="Plotly" />
        <img src="https://img.shields.io/badge/riotgames-D32936.svg?style=for-the-badge&logo=riotgames&logoColor=white" alt="Riot Games" />
    </div>
    """, unsafe_allow_html=True)

# NOTE: TEAM INFOMATION
st.write("##")
_, l, r, _ = st.columns([0.5, 1, 4, 0.5])
with l:
    st.image(
        f"https://ddragon.leagueoflegends.com/cdn/13.23.1/img/profileicon/3836.png", width=250)
    st.link_button("Summoner profile", "https://nauqh.github.io")
with r:
    w, l, t = calculate_wins_loses(df)
    _, a, b, _ = st.columns([1, 3, 2, 1])
    with a:
        st.write(f"""<span style='font-weight: 200; font-size: 1.5rem'>Challenger ARAM</span>""",
                 unsafe_allow_html=True)
        st.write(f"""<span style='
                    font-family: Recoleta-Regular; font-weight: 400;
                    font-size: 3rem'>Hoi Yeu Meo</span>""",
                 unsafe_allow_html=True)
        st.subheader(f":blue[{w}]W - :red[{l}]L")
        st.write(
            f"`Level`: 370")
        st.write(f"`LP`: 100")
        st.write(f"`Winrate`: {w/t*100:.2f}%")
    with b:
        st.image(f"app/img/CHALLENGER.png", width=250)

# NOTE: LINEUPS
st.write("##")
st.subheader("👨‍💻Lineups")
columns = st.columns(5)
for col, puuid in zip(columns, cf.puuids):
    info = api.get_info(puuid, 'vn2')
    col.image(
        f"https://ddragon.leagueoflegends.com/cdn/14.21.1/img/profileicon/{info['profileIconId']}.png")
    col.write(f"""
              {info['gameName']} #{info['tagLine']}\n
              Level: {info['summonerLevel']}
              """)


# NOTE: ROLES DISTRIBUTION
st.write("##")
st.subheader("🍰Roles Distribution")

l, r = st.columns([1, 1])
with l:
    st.info("📌 Roles are assigned based on Damage Dealt & Taken and CCs")
    fig = graph_role_dist(df)
    st.plotly_chart(fig, use_container_width=True)
with r:
    df_roles = df.groupby('riotIdGameName').agg({
        'assigned_roles': lambda roles: pd.Series([role for sublist in roles for role in sublist]).mode().tolist(),
        'championName': lambda x: x.mode()[0]
    }).reset_index()

    df_roles = df_roles.rename(columns={
        'riotIdGameName': 'Summoner',
        'assigned_roles': 'Most Appearing Roles',
        'championName': 'Most Used Champion'
    })

    df_roles['Most Appearing Roles'] = df_roles['Most Appearing Roles'].apply(
        lambda roles: ', '.join(roles))

    st.dataframe(df_roles, hide_index=True)

    st.write(
        "Roles are assigned based on a player's performance in a match. Players who rank among the top 3 in total damage dealt and primarily use physical damage are assigned the :red[AD Carry] role, while those who rank highly in damage dealt but primarily use magical damage are assigned the :blue[AP Carry] role.")
    st.write(
        "If no other primary role is assigned, players who take the most damage are assigned as :green[Tank]. Players who excel in crowd controls are assigned the :violet[Utility] role. This role assignment is based on factors such as damage dealt, damage taken, and CC contributions.")

# NOTE: OVERALL PERFORMANCE
st.write("##")
st.subheader("🏆Overall Performance")

fig = graph_team_participation(get_team_participation_stats(df))
st.plotly_chart(fig, use_container_width=True)

l, r = st.columns([1, 1])
with l:
    plt = generate_word_cloud(' '.join(df['championName']))
    st.pyplot(plt, clear_figure=True, use_container_width=True)

with r:
    st.subheader("Most used champions")
    champions = df['championName'].value_counts().nlargest(5).index
    cols = st.columns(5)
    for col, champion in zip(cols, champions):
        col.image(
            f'https://ddragon.leagueoflegends.com/cdn/14.21.1/img/champion/{champion}.png')
        wr = get_champ_winrate(champion, df)
        k, d, a = get_champ_kda(champion, df)
        col.write(f"""
                  :blue[{k:.1f}] / :red[{d:.0f}] / :green[{a:.0f}]
                    """)
    st.info("")

# NOTE: EARLY GAME PERFORMANCE
st.write("##")
st.subheader("🕐Early Game Performance")
fig = graph_team_early_game(get_team_early_game_stats(df))
st.plotly_chart(fig, use_container_width=True)

fig = graph_damage_over_matches(df)
st.plotly_chart(fig, use_container_width=True)
