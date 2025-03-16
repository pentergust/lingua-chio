import disnake
from disnake.ext import commands as cmds
from dotenv import load_dotenv
from os import getenv
from openai import OpenAI

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")
OAI_KEY   = getenv("OPENAI_KEY")
API_URL   = getenv("API_URL")
MODEL     = getenv("MODEL")
OWNER_ID  = getenv("OWNER_ID")
SYSTEM_PROMPT = getenv("SYSTEM_PROMPT")

class Lingua(cmds.Bot):
    def __init__(self):
        super().__init__(
            intents=disnake.Intents.all(),
            command_prefix="lingua.",
            help_command=None  
        )
        self.history = {}
        self.client = OpenAI(
            base_url=API_URL,
            api_key=OAI_KEY
        )
        self.system_prompt = SYSTEM_PROMPT

    async def on_ready(self):
        print(f"✅ {self.user} успешно запущен!")
        print(f"🔗 Подключён к {len(self.guilds)} серверам")
        await self._sync_application_commands()  

    def split_message(self, text: str, max_length: int = 2000) -> list[str]:
        chunks = []
        while len(text) > 0:
            if len(text) <= max_length:
                chunks.append(text)
                break
            split_at = text.rfind(' ', 0, max_length)
            if split_at == -1:

                chunk = text[:max_length]
                remaining = text[max_length:]
            else:

                chunk = text[:split_at + 1]
                remaining = text[split_at + 1:]
            chunks.append(chunk)
            text = remaining
        return chunks

    async def on_message(self, message: disnake.Message):
        if message.author.bot or not self.user in message.mentions:
            return

        async with message.channel.typing():
            response = await self.generate_response(message)

        chunks = self.split_message(response)
        for i, chunk in enumerate(chunks):
            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(chunk)

    async def generate_response(self, message: disnake.Message) -> str:
        user_id = str(message.author.id)
        if user_id not in self.history:
            self.history[user_id] = [{"role": "system", "content": self.system_prompt}]

        self.history[user_id].append({"role": "user", "content": message.content})

        completion = self.client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://lingua.qwa.su/",
                "X-Title": "Lingua AI"
            },
            model=MODEL,
            messages=self.history[user_id]
        )
        bot_reply = completion.choices[0].message.content
        self.history[user_id].append({"role": "assistant", "content": bot_reply})
        return bot_reply

class GeneralCommands(cmds.Cog):
    def __init__(self, bot: Lingua):
        self.bot = bot

    @cmds.command(name="sync", description="Принудительная синхронизация команд.")
    async def sync(self, ctx: cmds.Context):
        if ctx.author.id != OWNER_ID:
            return  

        await self.bot.sync_all_application_commands()
        await ctx.send("✅ Команды синхронизированы!")

    @cmds.slash_command(name="ping", description="Ответит Pong!")
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message("🏓 Pong!")

    @cmds.slash_command(name="info", description="Информация о боте.")
    async def info(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title="Привет, я Lingua!",
            description="Lingua — это помощник, который помогает вам с различными задачами, предоставляя полезную информацию и выполняя команды. Он всегда готов ответить на ваши вопросы и сделать общение персонализированным и приятным.\n\n",
            color=0x0065bc
        )
        embed.set_thumbnail(url="https://raw.githubusercontent.com/atarwn/lingua/refs/heads/main/lingua.png")
        embed.set_footer(text="Lingua v0.7.2 © Qwaderton, 2024-2025")
        await inter.response.send_message(embed=embed)

    @cmds.slash_command(name="reset", description="Сбросить историю диалога с ботом.")
    async def reset(self, inter: disnake.ApplicationCommandInteraction):
        user_id = str(inter.author.id)
        if user_id not in self.bot.history:
            await inter.response.send_message("⚠ У вас нет сохранённых сообщений.", ephemeral=True)
            return

        del self.bot.history[user_id]
        await inter.response.send_message("✅ История очищена!", ephemeral=True)

if __name__ == "__main__":
    bot = Lingua()

    bot.add_cog(GeneralCommands(bot))

    try:
        bot.run(BOT_TOKEN)
    except KeyboardInterrupt:
        print("⏹ Бот остановлен.")