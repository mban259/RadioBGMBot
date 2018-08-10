import discord
import debug
import setting
import re
import os


class program:
    def __init__(self):
        self.client = discord.Client()
        setting.load_setting()
        self.player = None
        self.volume = 1

    async def on_ready(self):
        debug.log('login')
        debug.log('id:{0} name:{1}'.format(self.client.user.name, self.client.user.id))
        self.xpc_jp = self.client.get_server(setting.xpc_jp)

    def is_radio_personality(self, user_id):
        if setting.admin == user_id:
            return True
        member = self.xpc_jp.get_member(user_id)
        for r in member.roles:
            if r.id == setting.radio_role:
                return True
        return False

    async def join_radio(self):
        if await self.radio_connecting():
            debug.log('already connected')
            return False
        debug.log('join radio')
        await self.client.join_voice_channel(self.client.get_channel(setting.radio_vc))
        return True

    async def leave_radio(self):
        if not await self.radio_connecting():
            debug.log('not connecting')
            return False
        if await self.playing():
            debug.log('stop bgm')
            await self.stop_bgm()
        debug.log('leave radio')
        voice = self.client.voice_client_in(self.xpc_jp)
        await voice.disconnect()
        return True

    async def start_bgm(self, bgm_name):
        if not await self.radio_connecting():
            await self.join_radio()
        voice = self.client.voice_client_in(self.xpc_jp)
        if await self.playing():
            await self.stop_bgm()
        self.player = voice.create_ffmpeg_player('data/bgm/{0}'.format(bgm_name))
        self.player.volume = self.volume * 0.5
        self.player.start()
        self.volume = 1
        return True

    async def playing(self):
        if not await self.radio_connecting():
            debug.log('not connecting')
            return False
        if self.player == None:
            debug.log('player is None')
            return False
        if self.player.is_playing():
            debug.log('playing')
            return True
        else:
            debug.log('not playing')
            return False

    async def radio_connecting(self):
        if not self.client.is_voice_connected(self.xpc_jp):
            debug.log('not connecting')
            return False
        voice = self.client.voice_client_in(self.xpc_jp)
        if voice.channel.id == setting.radio_vc:
            debug.log('connecting')
            return True
        else:
            debug.log('connecting another vc')
            await voice.disconnect()
            return False

    async def stop_bgm(self):
        if not await self.playing():
            return False
        self.player.stop()
        debug.log('stop')
        return True

    async def list_bgm(self, channel):
        debug.log('list')
        bgm_list = os.listdir('data/bgm')
        list_text = '\n'.join(bgm_list)
        print(list_text)
        await self.client.send_message(channel, '```{0}```'.format(list_text))
        return True

    async def set_volume(self, value):
        self.volume = value * 0.5
        if self.playing():
            self.player.volume = value * 0.5
            return True
        else:

            return False

    async def help(self, channel):
        debug.log('help')
        await self.client.send_message(channel, '```asciidoc\n{0}\n```'.format(setting.helplist))
        return True

    async def ping(self, channel):
        debug.log('ping')
        await self.client.send_message(channel, 'pong')
        return True

    async def execute_radio_command(self, message):
        message_text = message.content
        success = False
        join_r = re.match('^\./takashi *join$', message_text)
        if join_r:
            success = await self.join_radio()
        leave_r = re.match(r'^\./takashi *leave$', message_text)
        if leave_r:
            success = await self.leave_radio()
        start_r = re.search(r'^\./takashi *start (?P<name>(\s|\S)+\.(mp3|wav))$', message_text)
        if start_r:
            name = str(start_r.group('name'))
            success = await self.start_bgm(name)
        start_volume_r = re.search(
            r'^\./takashi *start (?P<name>(\s|\S)+\.(mp3|wav)) *(?P<value>(([0-1](\.[0-9]+)?)|2(\.0+)?))$',
            message_text)
        if start_volume_r:
            name = start_volume_r.group('name')
            self.volume = float(start_volume_r.group('value'))
            success = await self.start_bgm(name)
        stop_r = re.match(r'^\./takashi *stop$', message_text)
        if stop_r:
            success = await self.stop_bgm()
        list_r = re.match(r'^\./takashi *list$', message_text)
        if list_r:
            success = await self.list_bgm(message.channel)
        set_volume_r = re.search(r'^\./takashi *setvolume *(?P<value>(([0-1](\.[0-9]+)?)|2(\.0+)?))$', message_text)
        if set_volume_r:
            success = await self.set_volume(float(set_volume_r.group('value')))
        help_r = re.match(r'^\./takashi *help$', message_text)
        if help_r:
            success = await self.help(message.channel)
        ping_r = re.match(r'\./takashi *ping$', message_text)
        if ping_r:
            success = await self.ping(message.channel)
        if success:
            await self.client.add_reaction(message, '✅')
            debug.log('command:{0}'.format(message_text))

    async def on_message(self, message):
        if message.author.id == self.client.user.id:
            return
        if message.channel.is_private:
            # for direct message
            if self.is_radio_personality(message.author.id):
                if message.content.startswith('./takashi'):
                    await self.execute_radio_command(message)
            return
        if message.channel.server.id == setting.xpc_jp:
            # for xpc jp
            if self.is_radio_personality(message.author.id):
                if message.content.startswith('./takashi'):
                    await self.execute_radio_command(message)
            return

    def run(self):
        self.client.run(setting.discord_token)


setting.load_setting()
program = program()


# なんかうまい方法ないのかしら
@program.client.event
async def on_message(message):
    await program.on_message(message)


@program.client.event
async def on_ready():
    await program.on_ready()


program.run()
