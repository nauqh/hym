import bot
import hikari
import lightbulb
from .utils.config import Config
from .utils.extract import RiotAPI, extract_job

cf = Config('bot/data/settings.yml')

app = lightbulb.BotApp(
    cf.TOKEN,
    intents=hikari.Intents.ALL,
    default_enabled_guilds=cf.GUILD,
    help_slash_command=True,
    banner=None
)


app.load_extensions_from("./bot/extensions", must_exist=True)


@app.listen(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent) -> None:
    app.d.config = cf
    app.d.all_members_joined = False

current_members = set()


@app.listen(hikari.VoiceStateUpdateEvent)
async def on_voice_state_update(event: hikari.VoiceStateUpdateEvent) -> None:
    # Check if the member joined the channel
    if event.state.channel_id == cf.LEAGUE_CHANNEL_ID:
        current_members.add(event.state.user_id)
        member = await app.rest.fetch_member(cf.GUILD, event.state.user_id)

    # Check if the member left the channel
    if event.state.channel_id is None and event.old_state.channel_id == cf.LEAGUE_CHANNEL_ID:
        current_members.discard(event.state.user_id)

    # Check if all members have joined
    if len(current_members) == 5:
        app.d.all_members_joined = True
        print("All 5 members have joined the voice channel.")

    # Check if all members have left
    if len(current_members) == 0 and app.d.all_members_joined:
        print("All members have left the voice channel. Starting extraction job.")
        await start_extraction_job()
        app.d.all_members_joined = False


async def start_extraction_job():
    TOKEN = 'RGAPI-a384a673-d288-42ec-a860-55a1602dba94'

    api = RiotAPI(TOKEN)
    df = extract_job(api)
    df.to_csv('80games.csv', index=False)
    print("Data extraction completed.")


def run() -> None:
    app.run(
        activity=hikari.Activity(
            name=f"v{bot.__version__}",
            type=hikari.ActivityType.LISTENING,
            state="💡porodocs | /help")
    )
