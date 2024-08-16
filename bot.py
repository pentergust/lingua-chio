import disnake
from disnake.ext import commands
import ollama
import psutil
import GPUtil
from disnake.ui import Button, View
import concurrent.futures
import asyncio

# Чтение токена бота из файла
with open("token.txt", "r") as f:
    TOKEN = f.read().strip()

# Модель для генерации ответов
MODEL = 'llama3.1'

# Создаем экземпляр бота
bot = commands.Bot(intents=disnake.Intents.all())

# ID пользователя, которому доступны текстовые команды
AUTHORIZED_USER_ID = 805442059178737664

# Словарь для хранения истории сообщений для каждого сервера или пользователя
messages = {}
# Словарь для хранения характера бота для каждого сервера или пользователя
bot_character = {}

# Создаем ThreadPoolExecutor для выполнения задач в отдельных потоках
executor = concurrent.futures.ThreadPoolExecutor()

def get_context_id(ctx):
    """Возвращает идентификатор контекста (сервер или пользователь)."""
    if isinstance(ctx.channel, disnake.DMChannel):
        return ctx.author.id
    return ctx.guild.id

def get_system_character(context_id):
    return {'role': 'system', 'content': f"{bot_character[context_id]}"}

async def generate_summary(messages_context):
    """Функция для создания суммаризации."""
    summary = await asyncio.get_event_loop().run_in_executor(
        executor, lambda: ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': 'Please summarize the following conversation, highlighting the key points and important information. Make sure the summary is concise and captures the essence of the conversation.'}
        ] + messages_context)
    )
    return summary['message']['content']

async def generate_response(chat_history):
    """Функция для генерации ответа."""
    response = await asyncio.get_event_loop().run_in_executor(
        executor, lambda: ollama.chat(model=MODEL, messages=chat_history)
    )
    return response['message']['content']

@bot.event
async def on_ready():
    print(f'Бот {bot.user} успешно запущен!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    context_id = get_context_id(message)
    if context_id not in messages:
        messages[context_id] = []
        bot_character[context_id] = "Твоё имя Лингва!" # Speak ONLY in Russian.

    if bot.user.mentioned_in(message):
        message.content = message.content.replace(f"<@{bot.user.id}>", "")


    if bot.user.mentioned_in(message) or isinstance(message.channel, disnake.DMChannel):
         # Добавляем сообщение в историю контекста
        messages[context_id].append({'role': 'system', 'content': f'Пользователь <@{message.author.id}>({message.author.name}) в канале <#{message.channel.id}>({message.channel.name}) написал:'})
        messages[context_id].append({'role': 'user', 'content': f"{message.content}"})
        print(f'System: User <@{message.author.id}>({message.author.name}) in channel <#{message.channel.id}>({message.channel.name})')
        print(f"User: {message.content}")

        chat_history = [get_system_character(context_id)] + messages[context_id]
        
        async with message.channel.typing():
            response_content = await generate_response(chat_history)
        
        messages[context_id].append({'role': 'assistant', 'content': response_content})
        await message.reply(response_content)

        print(f"Ai: {response_content}")

    await bot.process_commands(message)

@bot.slash_command(
    name="ping", 
    description="Ответит Pong!"
)
async def ping(inter: disnake.ApplicationCommandInteraction):
    await inter.response.send_message("Pong!")

@bot.slash_command(
    name="set", 
    description="Изменяет характер бота для текущего сервера или пользователя"
)
async def set(inter: disnake.ApplicationCommandInteraction, character: str):
    if not isinstance(inter.channel, disnake.DMChannel) and not inter.author.guild_permissions.manage_guild or not AUTHORIZED_USER_ID:
        await inter.response.send_message("🚫 У вас нет прав для изменения характера бота.", ephemeral=True)
        return

    async def button_callback(interaction):
        context_id = get_context_id(inter)
        bot_character[context_id] = character
        messages[context_id] = []
        await inter.delete_original_response()
        await interaction.response.send_message(f"✅ Характер бота изменен на: ```{character}``` и история сообщений очищена.", ephemeral=True)

    view = View()
    yes_button = Button(label="Да", style=disnake.ButtonStyle.danger)
    yes_button.callback = button_callback
    no_button = Button(label="Нет", style=disnake.ButtonStyle.gray, disabled=False)

    async def no_button_callback(interaction):
        await inter.delete_original_response()
        await interaction.response.send_message("ℹ️ Операция изменения характера отменена.", ephemeral=True)

    no_button.callback = no_button_callback
    view.add_item(yes_button)
    view.add_item(no_button)

    await inter.response.send_message(
        f"⚠️ Вы действительно хотите изменить характер бота?\nЭто сбросит текущую историю общения!",
        view=view,
        ephemeral=True
    )

@bot.slash_command(
    name="view",
    description="Показывает текущий характер бота для текущего сервера или пользователя"
)
async def view(inter: disnake.ApplicationCommandInteraction):
    context_id = get_context_id(inter)
    character = bot_character.get(context_id, "Характер не установлен.")
    await inter.response.send_message(f"🔍 Текущий характер бота: ```{character}```", ephemeral=True)

@bot.slash_command(
    name="reset",
    description="Сбрасывает историю сообщений, сохраняя установленный характер"
)
async def reset(inter: disnake.ApplicationCommandInteraction):
    if not isinstance(inter.channel, disnake.DMChannel) and not inter.author.guild_permissions.manage_guild or not AUTHORIZED_USER_ID:
        await inter.response.send_message("🚫 У вас нет прав для сброса истории сообщений.", ephemeral=True)
        return

    context_id = get_context_id(inter)
    messages[context_id] = []
    await inter.response.send_message("✅ История сообщений была успешно сброшена.")

@bot.slash_command(
    name="info", 
    description="Показывает информацию о боте"
)
async def info(inter):
    memory_info = psutil.virtual_memory()
    gpus = GPUtil.getGPUs()

    gpu_info = ""
    for gpu in gpus:
        gpu_info += f"GPU {gpu.id}: {gpu.load * 100:.1f}%\n"

    embed = disnake.Embed(
        title=str(bot.user),
        description=(
            "Lingua — простой и кастомизируемый чатбот. Готов поболтать на любые темы, поиграть в ролевые игры, или просто поддержать в трудную минуту.\n\n"
            "```yaml\n"
            f"RAM: {memory_info.percent}%\n"
            f"{gpu_info}"
            f"MODEL: {MODEL}\n"
            "```\n"
        ),
        color=660265
    )
    embed.set_thumbnail(url="https://qwa.su/chatbot/logo-t.png")
    embed.set_footer(text="Lingua v0.5.1 © Qwaderton Software, 2024")
    
    await inter.response.send_message(embed=embed)


@bot.slash_command(
    name="shutdown",
    description="Завершает работу бота"
)
async def shutdown(inter: disnake.ApplicationCommandInteraction):
    if inter.author.id != AUTHORIZED_USER_ID:
        await inter.response.send_message("🚫 У вас нет прав для завершения работы бота.", ephemeral=True)
        return
    
    await inter.response.send_message("🔌 Бот завершает работу...")
    await bot.close()

# Запускаем бота
bot.run(TOKEN)
