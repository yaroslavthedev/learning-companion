"""The only module that talks to OpenAI.

Prompts are built from one goal (already scoped to its owner by the caller)
and its own sessions and resources. Every failure becomes `AIUnavailable`
with a fixed message: OpenAI's own error text can quote the API key."""

import json
import logging
import re

from django.conf import settings
from openai import OpenAI, OpenAIError

from learning.models import Goal

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30
SESSIONS_IN_PROMPT = 10
MAX_STEPS = 3

NOT_CONFIGURED = "AI is not configured on this server yet."
UNAVAILABLE = "The AI service is not available right now. Please try again later."
UNREADABLE = "Could not read the suggestions from the AI. Please try again."

SUMMARY_INSTRUCTIONS = (
    "You are a learning coach. Write a short progress summary (3-5 sentences) "
    "for the learner's goal below: what they have done, how consistent they "
    "are and where they stand. Plain text, no markdown."
)
NEXT_STEPS_INSTRUCTIONS = (
    "You are a learning coach. Suggest 2-3 concrete next learning actions for "
    "the learner's goal below, based on what they have done so far. Reply with "
    'a JSON array of 2-3 short strings only, e.g. ["Read ...", "Build ..."].'
)

LIST_MARKER = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s*")
CODE_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class AIUnavailable(Exception):
    """The AI couldn't answer; str() is a message safe to show the user."""


def summarize_goal(goal: Goal) -> str:
    prompt = "\n\n".join([goal_text(goal), sessions_text(goal), resources_text(goal)])
    return ask(SUMMARY_INSTRUCTIONS, prompt)


def suggest_next_steps(goal: Goal) -> list[str]:
    prompt = "\n\n".join([goal_text(goal), sessions_text(goal)])
    steps = parse_steps(ask(NEXT_STEPS_INSTRUCTIONS, prompt))
    if not steps:
        raise AIUnavailable(UNREADABLE)
    return steps


def ask(instructions: str, prompt: str) -> str:
    if not settings.OPENAI_API_KEY:
        raise AIUnavailable(NOT_CONFIGURED)
    # No retries: the SDK default (2) could hold a request ~3 × timeout, longer
    # than the gunicorn worker timeout. A failure shows the "try again" notice.
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY, timeout=TIMEOUT_SECONDS, max_retries=0
    )
    try:
        completion = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt},
            ],
        )
    except OpenAIError as error:
        # The class name only: the message can contain the key.
        logger.warning("OpenAI request failed: %s", type(error).__name__)
        raise AIUnavailable(UNAVAILABLE) from None
    return (completion.choices[0].message.content or "").strip()


def goal_text(goal: Goal) -> str:
    lines = [f"Goal: {goal.title}", f"Status: {goal.get_status_display()}"]
    if goal.description:
        lines.append(f"Description: {goal.description}")
    return "\n".join(lines)


def sessions_text(goal: Goal) -> str:
    sessions = goal.sessions.prefetch_related("tags")[:SESSIONS_IN_PROMPT]
    if not sessions:
        return "No sessions logged yet."
    lines = [f"Last {len(sessions)} sessions (newest first):"]
    for session in sessions:
        tags = ", ".join(tag.name for tag in session.tags.all()) or "none"
        notes = session.notes or "no notes"
        lines.append(
            f"- {session.date:%Y-%m-%d}, {session.duration_minutes} min, "
            f"tags: {tags}, notes: {notes}"
        )
    return "\n".join(lines)


def resources_text(goal: Goal) -> str:
    resources = goal.resources.all()
    if not resources:
        return "No resources saved yet."
    lines = ["Resources:"]
    lines += [f"- {r.title} ({r.get_kind_display()})" for r in resources]
    return "\n".join(lines)


def parse_steps(reply: str) -> list[str]:
    """A JSON array (fenced or not), else one step per numbered/bulleted line."""
    text = reply.strip()
    fenced = CODE_FENCE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    try:
        items = json.loads(text)
    except ValueError:
        items = None
    if isinstance(items, list):
        steps = [str(item).strip() for item in items]
    else:
        steps = [LIST_MARKER.sub("", line).strip() for line in text.splitlines()]
    return [step for step in steps if step][:MAX_STEPS]
