from plotly.subplots import make_subplots
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd


def split_text(champions, n=4):
    """Splits a list of champions into lines."""
    return "<br>".join([", ".join(champions[i:i + n]) for i in range(0, len(champions), n)])


def graph_role_dist(df):
    df['damage_rank'] = df.groupby(
        'matchId')['totalDamageDealtToChampions'].rank(ascending=False)
    df['damage_taken_rank'] = df.groupby(
        'matchId')['totalDamageTaken'].rank(ascending=False)
    df['CCDealt_rank'] = df.groupby(
        'matchId')['totalTimeCCDealt'].rank(ascending=False)

    # Assign roles based on conditions
    df['assigned_roles'] = df.apply(lambda row: [
        role for role in (
            'AD' if row['damage_rank'] <= 3 and row['physicalDamageDealtToChampions'] > row['magicDamageDealtToChampions'] else None,
            'AP' if row['damage_rank'] <= 3 and row['physicalDamageDealtToChampions'] <= row['magicDamageDealtToChampions'] else None,
            'Tank' if row['damage_taken_rank'] <= 2 else None,
            'Utility' if row['CCDealt_rank'] <= 2 else None
        ) if role is not None
    ], axis=1)

    df_exploded = df.explode('assigned_roles').dropna(
        subset=['assigned_roles'])

    role_counts = df_exploded['assigned_roles'].value_counts()
    labels = role_counts.index

    champions_by_role = df_exploded.groupby(
        'assigned_roles')['championName'].agg(lambda x: list(set(x))).to_dict()
    hover_texts = [
        f"{split_text(champions_by_role[role], n=4)}" for role in labels
    ]

    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=role_counts.values,
        hole=0.4,
        sort=False,
        direction='clockwise',
        pull=[0.1] * len(role_counts)
    )])

    fig.update_traces(
        hovertemplate='%{hovertext}<extra></extra>',
        hovertext=hover_texts,
        marker=dict(line=dict(color='#000', width=1))
    )

    fig.update_layout(
        title='Champions/Roles Distribution',
        margin=dict(t=40, l=0, r=0, b=0),
        legend=dict(x=0, y=1),
        height=350,
        template="plotly_white",
        hoverlabel=dict(font_color='#fff')
    )

    return fig


def graph_team_participation(team_participation_stats: dict) -> None:

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    metrics_primary = ['kills', 'deaths', 'assists']

    for metric in metrics_primary:
        fig.add_trace(go.Bar(
            x=team_participation_stats['riotIdGameName'],
            y=team_participation_stats[metric],
            name=metric.title(),
            hovertemplate='%{x}<br>%{fullData.name}: %{y} <extra></extra>',
            hoverlabel=dict(font_color='#fff'),
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=team_participation_stats['riotIdGameName'],
        y=team_participation_stats['challenges.killParticipation'],
        mode='lines+markers',
        name='Kill Participation (%)',
        hovertemplate='%{x}<br>KP: %{y:.1f}% <extra></extra>',
        line=dict(color='orange', width=2),
        marker=dict(size=8)
    ), secondary_y=True)

    fig.update_layout(
        title="Team Participation Performance",
        xaxis_title="Summoner",
        barmode='group',
        template='plotly_dark',
        hoverlabel=dict(bgcolor='#010A13', font_color='#fff'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        height=500
    )

    # Update the y-axis titles
    fig.update_yaxes(title_text="Total K/D/A", secondary_y=False)
    fig.update_yaxes(title_text="KP (%)", secondary_y=True,
                     range=[0, 100], showgrid=False)

    return fig


def generate_word_cloud(champions):
    wordcloud = WordCloud(background_color='white').generate(champions)
    plt.figure()
    plt.imshow(wordcloud)
    plt.axis('off')

    return plt


def graph_team_early_game(team_early_game_stats: dict):
    fig = go.Figure()

    # Adding traces for each metric
    metrics = ['firstBloodKill', 'firstBloodAssist',
               'firstTowerKill', 'firstTowerAssist']
    colors = ['#3d8f57', '#81d497',  '#4682B4', '#87ceeb']

    for i, metric in enumerate(metrics):
        fig.add_trace(go.Bar(
            x=team_early_game_stats['riotIdGameName'],
            y=team_early_game_stats[metric],
            name=metric,
            marker_color=colors[i],
            hovertemplate='Summoner: %{x}<br>%{fullData.name}: %{y} <extra></extra>',
        ))

    fig.update_layout(
        title="Early Game Performance",
        xaxis_title="Summoner",
        barmode='group',
        template='plotly_dark',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        hoverlabel=dict(bgcolor='#010A13', font_color='#fff'),
        height=500
    )

    fig.update_xaxes(title=None)

    return fig


def graph_damage_over_matches(df):
    df['encoded_matchId'] = 'M' + \
        (df['matchId'].astype('category').cat.codes + 1).astype(str)

    df['info.gameStartTimestamp'] = pd.to_datetime(
        df['info.gameStartTimestamp'], unit='ms')
    df['date'] = df['info.gameStartTimestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    grouped_stats = df.groupby(['encoded_matchId', 'riotIdGameName', 'date'])[
        'totalDamageDealtToChampions'].sum().reset_index().sort_values(by='date')
    summoners = grouped_stats['riotIdGameName'].unique()

    fig = go.Figure()

    for summoner in summoners:
        summoner_stats = grouped_stats[grouped_stats['riotIdGameName'] == summoner]
        fig.add_trace(go.Scatter(
            x=summoner_stats['encoded_matchId'],
            y=summoner_stats['totalDamageDealtToChampions'],
            mode='lines',
            name=summoner,
            hovertemplate=(
                'Damage: %{y:,.0f}<br>' +
                'Date: %{text}<extra></extra>'
            ),
            text=summoner_stats['date'],
        ))

    fig.update_layout(
        title="Total Damage Dealt Over Matches",
        xaxis_title="Encoded Match ID",
        yaxis_title="Damage Dealt",
        legend=dict(orientation="h", yanchor="top",
                    xanchor="center", x=0.5, y=1.1),
        hovermode="x unified",
        height=500
    )

    fig.update_xaxes(showgrid=False)

    return fig
