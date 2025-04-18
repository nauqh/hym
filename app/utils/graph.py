from plotly.subplots import make_subplots
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt


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
        xaxis_title=None,
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
    wordcloud = WordCloud(background_color='black').generate(champions)
    plt.figure(frameon=False)
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
        xaxis_title=None,
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

    return fig


def graph_damage_over_matches(df):
    df['encoded_matchId'] = 'M' + \
        (df['matchId'].astype('category').cat.codes + 1).astype(str)

    grouped_stats = df.groupby(['encoded_matchId', 'riotIdGameName', 'date'])[
        'totalDamageDealtToChampions'].sum().reset_index().sort_values(by='date')
    summoners = grouped_stats['riotIdGameName'].unique()

    fig = go.Figure()

    for i, summoner in enumerate(summoners):
        summoner_stats = grouped_stats[grouped_stats['riotIdGameName'] == summoner]
        if i == 0:
            hovertemplate = (
                'Date: %{text}<extra></extra><br>' +
                'Dmg: %{y:,.0f}'
            )
        else:
            hovertemplate = 'Dmg: %{y:,.0f}<extra></extra>'
        fig.add_trace(go.Scatter(
            x=summoner_stats['encoded_matchId'],
            y=summoner_stats['totalDamageDealtToChampions'],
            mode='lines',
            name=summoner,
            hovertemplate=hovertemplate,
            text=summoner_stats['date'].dt.strftime('%d %b %y %H:%M'),
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


def graph_team_combat(combat_stats: dict) -> None:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Metrics for primary y-axis
    metrics_primary = ['goldEarned',
                       'totalDamageDealtToChampions', 'totalDamageTaken']

    for metric in metrics_primary:
        fig.add_trace(go.Bar(
            x=combat_stats['riotIdGameName'],
            y=combat_stats[metric],
            name=metric.title(),
            hovertemplate='%{x}<br>%{fullData.name}: %{y:,.0f} <extra></extra>',
            hoverlabel=dict(font_color='#fff'),
        ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=combat_stats['riotIdGameName'],
        y=combat_stats['totalHealsOnTeammates'],
        mode='lines+markers',
        name='Heals On Teammates',
        hovertemplate='%{x}<br>Heal on Teammates: %{y:,.0f} <extra></extra>',
        line=dict(color='gold', width=2),
        marker=dict(size=8)
    ), secondary_y=True)

    # Update layout for the plot
    fig.update_layout(
        title="Team Combat Performance",
        xaxis_title="Summoner",
        barmode='group',
        hoverlabel=dict(bgcolor='#010A13', font_color='#fff'),
        template='plotly_dark',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        height=500,
    )

    fig.update_yaxes(title_text="Damage Dealt/Taken", secondary_y=False)
    fig.update_yaxes(title_text="Heal on Teammates",
                     secondary_y=True, showgrid=False)
    fig.update_xaxes(title=None)

    return fig


def graph_team_dmgproportion(damage_proportion: dict):
    names = damage_proportion['riotIdGameName']
    trues = damage_proportion['trueDamageDealtToChampions']
    physicals = damage_proportion['physicalDamageDealtToChampions']
    magics = damage_proportion['magicDamageDealtToChampions']

    fig = go.Figure()

    damage_types = ['True Damage', 'Physical Damage', 'Magic Damage']
    colors = ['#ff9500', '#ffc300', '#ffdd00']

    for damage_type, color in zip(damage_types, colors):
        fig.add_trace(go.Bar(
            y=names,
            x=trues if damage_type == 'True Damage' else (
                physicals if damage_type == 'Physical Damage' else magics),
            name=damage_type,
            orientation='h',
            marker=dict(color=color),
            hovertemplate='%{x:,.0f}<extra></extra>'
        ))

    fig.update_layout(title='Team Damage Proportion', barmode='stack',
                      height=500,
                      xaxis_title="Damage Dealt",
                      hoverlabel=dict(bgcolor='#010A13', font_color='#fff'),
                      legend=dict(orientation="h", yanchor="top",
                                  xanchor="center", x=0.5, y=1.1),
                      template='plotly_dark')

    return fig


def graph_winrate_by_side(df):
    side_win_rates = df.groupby('teamId')[
        'win'].mean() * 100

    fig = go.Figure()

    for team_id, win_rate in side_win_rates.items():
        side = 'Red' if team_id == 100 else 'Blue'

        fig.add_trace(go.Bar(
            name='',
            y=[f'{side} side'],
            x=[win_rate],
            orientation='h',
            hoverinfo='text',
            hovertext=f'{win_rate:.0f}%',
            width=0.7
        ))

    fig.update_layout(
        title='Winrate by Side',
        margin=dict(t=30, l=0, r=0, b=30),
        showlegend=False,
        hoverlabel=dict(bgcolor='#010A13', font_color='#fff'),
        xaxis_title=None,
        height=200,
    )

    return fig
