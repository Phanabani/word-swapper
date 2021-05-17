import logging
import sys

import discord
import discord.ext.commands as commands

from .generator import make_pun

logger = logging.getLogger('musician_pun.bot')


class Bot(commands.Bot):

    def __init__(self, *args, max_messages=None, **kwargs):
        super().__init__(*args, max_messages=max_messages, **kwargs)
        self.add_cog(Cog(self))

    async def on_connect(self):
        logger.info('Client connected')

    async def on_disconnect(self):
        logger.info('Client disconnected')

    async def on_resumed(self):
        logger.info('Session resumed')

    async def on_ready(self):
        logger.info('Client started')

    async def on_error(self, event_method: str, *args, **kwargs):
        exc_type, exc, tb = sys.exc_info()

        if exc_type is discord.HTTPException:
            logger.warning('HTTP exception', exc_info=True)

        elif exc_type is discord.Forbidden:
            logger.warning('Forbidden request', exc_info=True)

        elif event_method == 'on_message':
            msg: discord.Message = args[0]
            logger.error(
                f'Unhandled in on_message (content: {msg.content!r} '
                f'author: {msg.author} channel: {msg.channel})',
                exc_info=True
            )

        elif exc_type is KeyboardInterrupt:
            await self.close()

        else:
            logger.error(
                f"Unhandled in {event_method} (args: {args} kwargs: {kwargs})",
                exc_info=True
            )

    async def on_command_error(self, ctx: commands.Context, exception):
        logger.error("Unhandled exception", exc_info=exception)


class Cog(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command('pun')
    async def pun(self, ctx: commands.Context, *, phrase: str):
        pun = make_pun(phrase)
        if pun is None:
            pun = "Failed to generate anything"
        await ctx.send(pun)

    @commands.Cog.listener('on_raw_reaction_add')
    async def reroll(self, react: discord.RawReactionActionEvent):
        if react.user_id == self.bot.user.id:
            return

        emoji: discord.PartialEmoji = react.emoji
        if emoji.name == '🎲':
            await self.do_reroll(react.channel_id, react.message_id)

    async def do_reroll(self, chan_id: int, msg_id: int):
        chan: discord.TextChannel = self.bot.get_channel(chan_id)
        msg: discord.Message = await chan.fetch_message(msg_id)
        logger.info(f"Rerolling message")
        async for msg in chan.history(limit=3, before=msg):
            if not msg.content.startswith(self.bot.command_prefix):
                continue
            await self.bot.process_commands(msg)


def main():
    import json
    from pathlib import Path

    config = Path(__file__, '../config.json')

    with config.open() as f:
        bot_token = json.load(f)['bot_token']

    bot = Bot('$')
    bot.run(bot_token)
