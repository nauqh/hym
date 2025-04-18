import streamlit.components.v1 as components
import streamlit as st
import pandas as pd
import requests

from utils.config import Config
from utils.riot import *
from utils.graph import *

st.set_page_config(
    page_title="Porostream",
    page_icon="app/img/logo.svg",
    layout="wide"
)

# NOTE: SETUP
cf = Config()
api = RiotAPI(cf.TOKEN)
df = load_data(cf.puuids)


def filter_by_period(df, period):
    # Extract the month and year from the selected period
    month_name, year = period.split()
    # Convert month name to month number
    month = pd.to_datetime(month_name, format='%B').month
    year = int(year)

    # Define the start and end dates for filtering
    start_date = f"{year}-{month:02d}-01"
    if month == 12:  # If December, increment the year for the end date
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    # Filter the DataFrame for the selected period
    filtered_df = df[(df['date'] >= start_date) & (df['date'] < end_date)]

    return filtered_df


# Fetch latest version
try:
    response = requests.get(
        "https://ddragon.leagueoflegends.com/api/versions.json", timeout=10)
    response.raise_for_status()
    versions = response.json()
    latest_version = versions[0] if versions else None
except Exception as e:
    latest_version = None
    print(f"Error fetching LoL version: {e}")


# NOTE: LANDING
_, center, _ = st.columns([1, 10, 1])
with center:
    st.markdown("""
                <h1 style='text-align: center; font-weight: 600;
                    font-size: 6rem'>State of
                <span style='background-color: #ffc300; padding: 0 0.5rem; color: #010A13; border-radius: 0.5rem'>HYM</span>
                <span style='color: #ffc300; font-weight: 800'> > </span>
                <br> Performance 2025</h1>""", unsafe_allow_html=True)
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
_, center, _ = st.columns([0.5, 1, 0.5])
with center:
    l, r = st.columns([1, 1])

    with l:
        st.image("app/img/logo.svg", width=250)

    with r:
        w, l, t = calculate_wins_loses(df)

        st.write("""<span style='font-weight: 200; font-size: 1.5rem'>Challenger ARAM</span>""",
                 unsafe_allow_html=True)
        st.write("""<span style='
                    font-family: Recoleta-Regular; font-weight: 400;
                    font-size: 3rem'>Hoi Yeu Meo</span>""",
                 unsafe_allow_html=True)
        st.subheader(f":blue[{w}]W - :red[{l}]L")

        st.write(f"`Winrate`: {w/t*100:.2f}%")

    periods = [f"{date.strftime('%B')} {date.year}" for date in df['date'].dt.to_period(
        "M").unique()] + ['All time']
    filtered_period = st.selectbox(
        "`Time period`:", periods, index=periods.index('All time'))
    if filtered_period and filtered_period != 'All time':
        df = filter_by_period(df, filtered_period)


# NOTE: LINEUPS


@st.cache_data
@st.cache_data(ttl=3600)
def get_team_lineups(puuids):
    return [api.get_info(puuid, 'vn2') for puuid in puuids]


st.write("##")
st.header("📑 Team Lineups")

infos = get_team_lineups(cf.puuids)
for info in infos:
    info['name'] = next(
        (key for key, value in cf.players.items() if value == info['puuid']), None)

columns = st.columns(len(infos))

for col, info in zip(columns, infos):
    col.image(
        f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/profileicon/{info['profileIconId']}.png")
    col.write(
        f"""
        {info['name'].title()} `#{info['tagLine']}`\n
        Level: {info['summonerLevel']}""")

chosen_summoners = st.multiselect(
    "Choose summoners",
    [info['name'] for info in infos],
    default=[info['name'] for info in infos]
)
if len(chosen_summoners) > 1:
    df = df[df['riotIdGameName'].isin(chosen_summoners)]
else:
    st.error("Please select at least 2 summoners")
    st.stop()

# NOTE: ROLES DISTRIBUTION
st.write("##")
st.header("🍰 Roles Distribution")

l, r = st.columns([1, 1])
with l:
    fig = graph_role_dist(df)
    st.plotly_chart(fig, use_container_width=True)

    fig = graph_winrate_by_side(df)
    st.plotly_chart(fig, use_container_width=True)
with r:
    df_roles = calculate_roles_winrate(df)

    st.dataframe(
        df_roles[['Summoner', 'Roles', 'Most Used Champion',
                  'Win Rate (%)', 'Damage Rank']], hide_index=True)

    st.write(
        "Roles are assigned based on a player's performance in a match. Players who rank among the top 3 in total damage dealt and primarily use physical damage are assigned the :red[AD Carry] role, while those who rank highly in damage dealt but primarily use magical damage are assigned the :blue[AP Carry] role.")
    st.write(
        "If no other primary role is assigned, players who take the most damage are assigned as :green[Tank]. Players who excel in crowd controls are assigned the :violet[Utility] role. This role assignment is based on factors such as damage dealt, damage taken, and CC contributions.")

# NOTE: OVERALL PERFORMANCE
st.write("##")
st.header("🏆Overall Performance")

fig = graph_team_participation(get_team_participation_stats(df))
st.plotly_chart(fig, use_container_width=True)

l, r = st.columns([1.2, 1])
with l:
    plt = generate_word_cloud(' '.join(df['championName']))
    st.pyplot(plt, clear_figure=True, use_container_width=True)

with r:
    st.subheader("Most used champions")
    champions = df['championName'].value_counts().nlargest(5).index
    cols = st.columns(5)
    for col, champion in zip(cols, champions):
        col.image(
            f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/champion/{champion}.png')
        wr = get_champ_winrate(champion, df)
        k, d, a = get_champ_kda(champion, df)
        col.write(f"""
                  :blue[{k:.1f}] / :red[{d:.0f}] / :green[{a:.0f}]
                    """)

# NOTE: EARLY GAME PERFORMANCE
st.write("##")
st.header("🕐 Early Game Performance")
fig = graph_team_early_game(get_team_early_game_stats(df))
st.plotly_chart(fig, use_container_width=True)

fig = graph_damage_over_matches(df)
st.plotly_chart(fig, use_container_width=True)

# NOTE: COMBAT PERFROMANCE
st.write("##")
st.header("🗡️ Combat Performance")

fig = graph_team_combat(get_team_combat_stats(df))
st.plotly_chart(fig, use_container_width=True)

fig = graph_team_dmgproportion(get_team_damage_proportion(df))
st.plotly_chart(fig, use_container_width=True)

# NOTE: INDIVIDUAL PERFORMANCE
st.write("##")
l, r = st.columns([1, 2])
with l:
    st.header("📑Summoner")
with r:
    options = chosen_summoners
    if 'selected_summoner' not in st.session_state:
        st.session_state.selected_summoner = None

    st.session_state.selected_summoner = st.selectbox(
        "Select a column:",
        options,
        key="column_selectbox",
        index=(
            options.index(st.session_state.selected_summoner)
            if st.session_state.selected_summoner in options
            else 0
        )
    )
l, r = st.columns([1, 2])

with l:
    summoner = next(
        (info for info in infos if info['name'] == st.session_state.selected_summoner), None)
    st.image(
        f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/profileicon/{summoner['profileIconId']}.png")
    st.link_button("Summoner profile",
                   f"https://www.op.gg/summoners/vn/{summoner['gameName']}-{summoner['tagLine']}")

with r:
    stats = get_summoner_stats(df, summoner['name'])
    w, l, t = calculate_wins_loses(df)
    columns_data = {
        "🎯Games": f"{t}G :blue[{w}]W :red[{l}]L",
        "🏆Winrates": f"{w/t*100:.2f} %",
        "⚔️KDA": f"{stats['kills']:.1f}/{stats['deaths']:.1f}/{stats['assists']:.1f}",
        "🥊Damage": f"{stats['totalDamageDealtToChampions']:,.0f}",
        "🔥Pentakills": stats['pentaKills'],
        "🔍Vision": "N.A.",
        "🧑‍🌾Minions": f"Avg. {stats['totalMinionsKilled']:.1f}",
        "⛓️‍💥CCs Dealt": f"Avg. {stats['totalTimeCCDealt']:.1f}s",
        "👩‍🚀Time Alive": f"Avg. {int(stats['longestTimeSpentLiving'] / 60)} min"
    }
    for i in range(0, len(columns_data), 3):
        l, m, r = st.columns([1, 1, 1])
        with l:
            title, value = list(columns_data.items())[i]
            st.subheader(title)
            st.subheader(value)
        with m:
            title, value = list(columns_data.items())[i + 1]
            st.subheader(title)
            st.subheader(value)
        with r:
            title, value = list(columns_data.items())[i + 2]
            st.subheader(title)
            st.subheader(value)

st.write("##")
st.subheader("Signature champion")

name = df[df['riotIdGameName'] == summoner['name']].groupby(
    'riotIdGameName')['championName'].value_counts().idxmax()[1]
champion = requests.get(
    f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/data/en_US/champion/{name}.json").json()['data'][name]

l, r = st.columns([1, 1])
with l:
    st.image(
        f"https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{name}_0.jpg")
    plt = generate_word_cloud(' '.join(
        df[df['riotIdGameName'] == st.session_state.selected_summoner]['championName']))
    st.pyplot(plt, clear_figure=True, use_container_width=True)
with r:
    st.write(f"""
            <h3 style='font-family: Recoleta-Regular; font-weight: 200; font-size: 2rem; text-align: center;color:#ffc300'>{champion['name']}</h3>
            """, unsafe_allow_html=True)
    st.markdown(f"{champion['blurb']}")
    st.markdown(f"`Title`: {champion['title']}")
    st.markdown(f"`Role`: {', '.join(champion['tags'])}")


st.write("##")
st.markdown("### ⭐ Star the project on Github")
components.iframe(
    "https://ghbtns.com/github-btn.html?user=nauqh&type=follow&count=true&size=large")
