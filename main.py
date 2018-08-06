import discord
import debug
import setting
import re
import asyncio
import traceback
import os
from multiprocessing import Value

playing = False
client = discord.Client()
setting.load_setting()
volume = 1


async def play_bgm():
    debug.log('start')
    global client
    global set_bgm
    global playing
    global xpc
    global player
    global stopped
    global volume
    while True:
        if playing:
            debug.log("play_bgm")
            playing_bgm = set_bgm
            voice = client.voice_client_in(xpc)
            debug.log('load data/bgm/{0}'.format(playing_bgm))
            player = voice.create_ffmpeg_player('data/bgm/{0}'.format(playing_bgm))
            player.start()
            while not player.is_done():
                player.volume = volume
                if (not playing):
                    player.stop()
                    stopped = True
                    break
                await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0.01)


@client.event
async def on_ready():
    global playing
    playing = False
    global xpc
    debug.log('login')
    debug.log('id:{0} name:{1}'.format(client.user.name, client.user.id))
    xpc = client.get_server(setting.xpc_jp)


def is_radio_personality(user_id):
    global client
    global xpc
    member = xpc.get_member(user_id)
    for r in member.roles:
        if r.id == setting.radio_role:
            return True
    return False


async def join_radio():
    global client
    global xpc
    if client.is_voice_connected(xpc):
        if client.voice_client_in(xpc).channel.id == setting.radio_vc:
            debug.log("already join radio")
            return False
    debug.log("join radio")
    await client.join_voice_channel(client.get_channel(setting.radio_vc))
    return True


async def leave_radio():
    global client
    global xpc
    if client.is_voice_connected(xpc):
        if playing:
            await stop_bgm()
        debug.log("left radio")
        radio = client.voice_client_in(xpc)
        await radio.disconnect()
        return True
    else:
        debug.log('not connect radio')
        return False


async def start_bgm(bgm_name):
    global playing
    global set_bgm
    if not os.path.isfile('data/bgm/{0}'.format(bgm_name)):
        return False
    await join_radio()
    debug.log("start {0}".format(bgm_name))
    set_bgm = bgm_name
    if playing:
        await stop_bgm()
    playing = True
    return True


async def stop_bgm():
    global playing
    global stopped
    if playing:
        debug.log('stop_bgm')
        stopped = False
        playing = False
        while not stopped:
            await asyncio.sleep(0.01)
        return True
    else:
        return False

async def list_bgm(channel):
    global client
    print('list')
    bgm_list = os.listdir('data/bgm')
    list_text = '\n'.join(bgm_list)
    print(list_text)
    await client.send_message(channel, '```{0}```'.format(list_text))
    return True

async def set_volume(value):
    global volume
    volume = value
    return True

async def help(channel):
    global client
    await client.send_message(channel, '```asciidoc\n{0}\n```'.format(setting.helplist))
    return True


async def execute_radio_command(message):
    global client
    message_text = message.content
    success = False
    join_r = re.match('^\./takashi *join$', message_text)
    if join_r:
        success = await join_radio()
    leave_r = re.match(r'^\./takashi *leave$', message_text)
    if leave_r:
        success = await leave_radio()
    start_r = re.search(r'^\./takashi *start (?P<name>(\s|\S)+\.(mp3|wav))$', message_text)
    if start_r:
        name = str(start_r.group('name'))
        success = await start_bgm(name)
    stop_r = re.match(r'^\./takashi *stop$', message_text)
    if stop_r:
        success = await stop_bgm()
    list_r = re.match(r'^\./takashi *list$', message_text)
    if list_r:
        success = await list_bgm(message.channel)
    set_volume_r = re.search(r'^\./takashi *setvolume *(?P<value>(([0-1](\.[0-9])?)|2(\.0)?))$', message_text)
    if set_volume_r:
        success = await set_volume(float(set_volume_r.group('value')))
    help_r = re.match(r'^\./takashi help$', message_text)
    if help_r:
        success = await help(message.channel)
    if success:
        await client.add_reaction(message, '✅')
        debug.log('command:{0}'.format(message_text))


@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    if message.channel.id:
        # for direct message
        if is_radio_personality(message.author.id):
            if message.content.startswith('./takashi'):
                await execute_radio_command(message)
        return
    if message.channel.server.id == setting.xpc_jp:
        # for xpc jp
        if is_radio_personality(message.author.id):
            if message.content.startswith('./takashi'):
                await execute_radio_command(message)
        return


loop = asyncio.get_event_loop()
asyncio.ensure_future(play_bgm())
asyncio.ensure_future(client.run(setting.discord_token))
loop.run_forever()
