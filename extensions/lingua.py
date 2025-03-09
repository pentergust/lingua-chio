"""Lingua.

Lingua — это помощник, который помогает вам с различными задачами,
предоставляя полезную информацию и выполняя команды.
Он всегда готов ответить на ваши вопросы и сделать общение
персонализированным и приятным.

TODO: Сделать нормальное хранилище для настроек.

Предоставляет
-------------

Copyright (c) 2024-2025 Qwaderton
Licensed under the Qwaderton License. All rights reserved.

Version: v0.8 (3)
Maintainer: atarwn
Source: https://github.com/atarwn/Lingua
"""

from collections.abc import Iterator
from os import getenv

import arc
import hikari
from openai import OpenAI

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("lingua")

# Настройки API
OAI_KEY = getenv("OPENAI_KEY")
API_URL = getenv("OPENAI_API_URL")

MODEL = "sophosympatheia/rogue-rose-103b-v0.2:free"
# Кормим нейронке, чтобы выдавала хорошие ответы
SYSTEM_PROMPT = (
    "Ты — Lingua, технический ассистент, созданный для помощи пользователям."
    "Отвечай чётко, по делу, без воды."
    "Если вопрос неясен, уточняй."
    "Не давай ложных данных, не выдумывай."
    "Если не знаешь — скажи об этом прямо."
    "Говори сдержанно, но не холодно."
    "Будь дружелюбным, но не переходи в панибратство."
    "Когда отвечаешь про программирование, старайся давать примеры кода."
    "Если разговор требует дополнительных уточнений — "
    "задавай вопросы пользователю."
)


class MessageStorage:
    """История сообщений с пользователем."""

    def __init__(self) -> None:
        self.history: dict[str, list[str]] = {}
        self.client = OpenAI(base_url=API_URL, api_key=OAI_KEY)
        self.system_prompt = SYSTEM_PROMPT

    async def generate_answer(self, ctx: arc.Context, message: str) -> str:
        """Генерирует некоторый ответ от AI."""
        user_id = str(ctx.user.id)

        if user_id not in self.history:
            self.history[user_id] = [{"role": "system", "content": self.system_prompt}]

        self.history[user_id].append({"role": "user", "content": message})

        completion = self.client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://lingua.qwa.su/",
                "X-Title": "Lingua AI",
            },
            model=MODEL,
            messages=self.history[user_id],
        )
        bot_reply = completion.choices[0].message.content
        self.history[user_id].append({"role": "assistant", "content": bot_reply})
        return bot_reply


STORAGE = MessageStorage()

# Дополнительные функции
# ======================

_BOT_DESC = (
    "Lingua — это помощник, который помогает вам с различными задачами, "
    "предоставляя полезную информацию и выполняя команды. "
    "Он всегда готов ответить на ваши вопросы и сделать общение "
    "персонализированным и приятным.\n\n"
)


def get_info() -> hikari.Embed:
    """Немного информации о расширении."""
    embed = hikari.Embed(
        title="Привет, я Lingua!",
        description=_BOT_DESC,
        color=0x0065BC,
    )
    embed.set_thumbnail(
        "https://raw.githubusercontent.com/atarwn/lingua/refs/heads/main/lingua.png"
    )
    embed.set_footer(text="Lingua v0.7.1 © Qwaderton Labs, 2024-2025")
    return embed


def iter_message(text: str, max_length: int = 2000) -> Iterator[str]:
    """Разбивает больше сообщение на кусочки по 2000 символов."""
    while len(text) > 0:
        if len(text) <= max_length:
            yield text
            break

        split_at = text.rfind(" ", 0, max_length)

        # Не найдено пробелов, вынужденно разбиваем по max_length
        if split_at == -1:
            chunk = text[:max_length]
            remaining = text[max_length:]

        # Разбиваем после пробела
        else:
            chunk = text[: split_at + 1]
            remaining = text[split_at + 1 :]

        yield chunk
        text = remaining


# определение команд
# ==================


@plugin.include
@arc.slash_command("lingua", description="Диалог с AI.")
async def lingua_handler(
    ctx: arc.GatewayContext,
    message: arc.Option[str | None, arc.StrParams("Сообщение для AI")] = None,
) -> None:
    """Отправляет сообщение в диалог с ботом или же выводит информацию."""
    if message is None:
        await ctx.respond(embed=get_info())
    else:
        resp = await ctx.respond("⏳ Генерация ответа...")
        async with ctx.get_channel().trigger_typing():
            answer = await STORAGE.generate_answer(ctx, message)
            answer_gen = iter_message(answer)
            await resp.edit(next(answer_gen))

    # Отправляем все оставшиеся кусочки
    for message_chunk in answer_gen:
        await ctx.respond(message_chunk)


@plugin.include
@arc.slash_command("reset_dialog", description="Сбрасывает диалог с пользователем.")
async def reset_ai_dialog(
    ctx: arc.GatewayContext,
) -> None:
    """Очищает историю сообщений для пользователя."""
    if ctx.user.id not in STORAGE.history:
        await ctx.response("⚠ У вас нет сохранённых сообщений.", ephemeral=True)
    STORAGE.history.pop(ctx.user.id)
    await ctx.response("✅ История очищена!", ephemeral=True)


# Загрузчики и выгрузчики плагина
# ===============================


@arc.loader
def loader(client: arc.GatewayClient) -> None:
    """Действия при загрузке плагина."""
    client.add_plugin(plugin)


@arc.unloader
def unloader(client: arc.GatewayClient) -> None:
    """Действия при выгрузке плагина."""
    client.remove_plugin(plugin)
