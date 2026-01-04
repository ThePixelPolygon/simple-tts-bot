import io
import os

import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
import pyttsx3
import i18n


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=None, intents=intents)
engine = pyttsx3.init()


i18n.load_path.append("locales")
i18n.set('fallback', 'en_CA')
i18n.set('skip_locale_root_data', True)
i18n.set('file_format', 'json')
i18n.set('filename_format', '{locale}.{format}')


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print('Ready')
    except Exception as e:
        print(e)
        exit(-1)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if message.guild.voice_client is None:
        return

    if not (message.author.voice is not None and message.channel.id == message.author.voice.channel.id):
        return

    source = convert_text_to_audio(message.content, message.author.name)
    with open(source, 'rb') as file:
        buffered_io = io.BytesIO(file.read())
        message.guild.voice_client.play(FFmpegPCMAudio(buffered_io, pipe=True))

    os.remove(source)


@bot.event
async def on_voice_state_update(member, before, after):
    if member.guild.voice_client is None:
        return

    if len(member.guild.voice_client.channel.members) - 1 == 0:
        await before.channel.send(i18n.t("disconnect.auto", channel=before.channel.name))
        await member.guild.voice_client.disconnect()


@bot.tree.command(name="start", description="Starts the TTS bot in your current voice channel.")
async def start_command(interaction: discord.Interaction):
    if interaction.user.voice is None:
        await interaction.response.send_message(i18n.t("errors.not_in_vc"), ephemeral=True)
        return

    await discord.VoiceChannel.connect(interaction.user.voice.channel)
    await interaction.response.send_message(i18n.t("connect_successful",
                                                   channel=interaction.guild.voice_client.channel),
                                            ephemeral=False)


@bot.tree.command(name="stop", description="Disconnects the TTS bot.")
async def stop_command(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.response.send_message(i18n.t("disconnect.manual",
                                                       channel=interaction.guild.voice_client.channel))
        await interaction.guild.voice_client.disconnect(force=True)


def convert_text_to_audio(text: str, username: str):
    filename = f"{username}.wav"
    engine.save_to_file(text, filename)
    engine.runAndWait()
    return filename


if __name__ == '__main__':
    bot.run(os.getenv('TOKEN'))