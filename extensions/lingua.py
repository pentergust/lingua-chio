"""Lingua.

Lingua — это помощник, который помогает вам с различными задачами,
предоставляя полезную информацию и выполняя команды.
Он всегда готов ответить на ваши вопросы и сделать общение
персонализированным и приятным.

TODO: Сделать нормальное хранилище для настроек.

Предоставляет
-------------

Version: v0.9 (4)
Maintainer: atarwn
Source: https://github.com/atarwn/Lingua
"""

from collections import deque
from collections.abc import Iterator
from os import getenv

import arc
import hikari
from openai import OpenAI

# Глобальные переменные
# =====================

plugin = arc.GatewayPlugin("lingua")
MAX_HISTORY_LENGTH = 20

# Настройки API
OAI_KEY = getenv("OPENAI_KEY")
API_URL = getenv("OPENAI_API_URL")
OWNER_ID = getenv("OWNER_ID")
MODEL = getenv("AI_MODEL", "meta-llama/llama-4-maverick:free")

# Кормим нейронке, чтобы выдавала хорошие ответы
SYSTEM_PROMPT = getenv("SYSTEM_PROMPT")


class MessageStorage:
    """История сообщений с пользователем."""

    def __init__(
        self, model: str, system_prompt: str | None, history_length: int
    ) -> None:
        self.model = model
        self.system_prompt = system_prompt
        self.history_length = history_length

        self.history: dict[int, deque[dict]] = {}
        self.client = OpenAI(base_url=API_URL, api_key=OAI_KEY)

    async def get_completion(self, messages: deque[dict]) -> str:
        """Делает запрос к AI модели."""
        return (
            self.client.chat.completions.create(
                extra_headers={
                    "HTTP-Referer": "https://lingua.qwa.su/",
                    "X-Title": "Lingua AI",
                },
                model=self.model,
                messages=messages,
            )
            .choices[0]
            .message.content
        )

    async def add_to_history(self, user_id: int, message: str) -> None:
        """Добавляет новое сообщение в историю."""
        if user_id not in self.history:
            self.history[user_id] = deque(maxlen=self.history_length)

            self.history[user_id].append(
                {"role": "system", "content": self.system_prompt}
            )
        self.history[user_id].append({"role": "user", "content": message})

    async def generate_answer(self, user_id: int, message: str) -> str:
        """Генерирует некоторый ответ от AI."""
        await self.add_to_history(user_id, message)
        completion = await self.get_completion(self.history[user_id])
        self.history[user_id].append({"role": "assistant", "content": completion})
        return completion


STORAGE = MessageStorage(
    model=MODEL, system_prompt=SYSTEM_PROMPT, history_length=MAX_HISTORY_LENGTH
)

# Дополнительные функции
# ======================


def get_info() -> hikari.Embed:
    """Немного информации о расширении."""
    embed = hikari.Embed(
        title="Привет, я Lingua!",
        description="Lingua — Ваш многофункциональный помощник для решения  технических задач.",
        color=0x00AAE5,
    )
    embed.set_thumbnail(
        "https://raw.githubusercontent.com/atarwn/Lingua/refs/heads/main/assets/lingua.png"
    )
    embed.set_footer(text="Lingua v0.9 © Qwaderton Labs, 2024-2025")
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
            answer = await STORAGE.generate_answer(ctx.user.id, message)
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
