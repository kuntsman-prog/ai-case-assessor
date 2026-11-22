"""Роль LLM: извлечь параметры кейса из свободного описания и написать резюме для руководства.

Принцип: «модель извлекает, правила решают». Экономику, класс риска и приоритет
считает прозрачный код, а не модель. Ответ модели проверяется по схеме;
при ошибке модель получает текст ошибки и одну попытку исправиться.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Callable

from pydantic import ValidationError

from .model import Case, case_from_dict

ChatFn = Callable[[list[dict]], str]

ALLOWED_FIELDS = {
    "name": "краткое название кейса",
    "process": "какой процесс и что делает ИИ",
    "operations_per_month": "целое число операций в месяц",
    "minutes_saved_per_op": "минут экономии на одну операцию",
    "adoption_rate": "доля использования 0..1",
    "hourly_cost_business": "стоимость часа сотрудника, руб.",
    "infra_month": "затраты на GPU, подписки, лицензии в месяц, руб.",
    "implementation_hours": "трудозатраты на внедрение, часов",
    "data_sensitivity": "public | internal | confidential | personal",
    "audience": "internal | clients",
    "autonomy": "assistant | agent | autonomous",
    "deployment": "local | russian_cloud | foreign_api",
    "decision_impact": "none | internal | client",
    "data_readiness": "1..5",
    "integration_simplicity": "1..5",
}

EXTRACT_PROMPT = (
    "Ты аналитик, который переводит описание бизнес-задачи в параметры для оценки ИИ-кейса. "
    "Верни ТОЛЬКО JSON-объект без пояснений. Включай поле, только если оно следует из текста; "
    "не выдумывай числа. Обязательны name, process, operations_per_month, minutes_saved_per_op. "
    "Допустимые поля:\n" + "\n".join(f"- {k}: {v}" for k, v in ALLOWED_FIELDS.items())
)


def ollama_chat(messages: list[dict]) -> str:
    url = os.environ.get("OLLAMA_URL", "http://localhost:11434") + "/api/chat"
    payload = {
        "model": os.environ.get("OLLAMA_MODEL", "qwen2.5:7b-instruct"),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
        "messages": messages,
    }
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())["message"]["content"]


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("в ответе нет JSON-объекта")
    data = json.loads(match.group(0))
    return {k: v for k, v in data.items() if k in ALLOWED_FIELDS}


def extract_case(description: str, chat: ChatFn = ollama_chat) -> Case:
    messages = [
        {"role": "system", "content": EXTRACT_PROMPT},
        {"role": "user", "content": description},
    ]
    last_error = ""
    for _ in range(2):
        raw = chat(messages)
        try:
            return case_from_dict(_parse_json(raw))
        except (ValueError, ValidationError) as e:
            last_error = str(e)[:500]
            messages += [
                {"role": "assistant", "content": raw},
                {"role": "user", "content": f"Ответ не прошёл проверку: {last_error}. Исправь и верни только JSON."},
            ]
    raise ValueError(f"Не удалось извлечь параметры кейса: {last_error}")


SUMMARY_PROMPT = (
    "Напиши резюме оценки ИИ-кейса для руководства: 3-4 предложения на русском, деловым языком. "
    "Используй только цифры и выводы из переданных данных, ничего не добавляй от себя. "
    "Не используй длинное тире."
)


def executive_summary(facts: dict, chat: ChatFn = ollama_chat) -> str:
    text = chat([
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": json.dumps(facts, ensure_ascii=False)},
    ])
    return text.replace("\u2014", "\u2013").strip()
