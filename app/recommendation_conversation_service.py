import logging
import json

import anthropic as anthropic_sdk

from llm_recommendations_module import (
    get_api_key, MODEL_HAIKU, MODEL_SONNET,
    get_user_coaching_spectrum, get_coaching_tone_instructions,
)
from prompt_constants import NORMALIZED_DIVERGENCE_FORMULA
from db_utils import (
    get_recommendation_conversation,
    upsert_recommendation_conversation,
    mark_conversation_extraction_done,
    get_athlete_model,
    upsert_athlete_model,
)

logger = logging.getLogger('recommendation_conversation_service')


def generate_why_explanation(user_id, recommendation_date, structured_output, todays_decision):
    try:
        so = structured_output or {}
        assessment = so.get('assessment', {})
        divergence_block = so.get('divergence', {})
        risk_block = so.get('risk', {})
        context_block = so.get('context', {})

        tone = get_coaching_tone_instructions(get_user_coaching_spectrum(user_id))

        system_prompt = (
            f"{tone}\n\n"
            "You are explaining the reasoning behind a specific training recommendation to the athlete. "
            "The recommendation text and its structured decision output are provided — use both. "
            "Cite the specific metrics and flags that drove the decision. "
            "Explain why THIS workout and not a harder or easier alternative. "
            "Identify the binding constraint today. "
            "3-5 sentences. No bullet points. Write directly to the athlete."
        )

        user_prompt = (
            f"RECOMMENDATION FOR {recommendation_date}:\n"
            f"{todays_decision}\n\n"
            f"STRUCTURED DECISION OUTPUT:\n"
            f"- Primary signal: {assessment.get('primary_signal', 'N/A')}\n"
            f"- Assessment: {assessment.get('category', 'N/A')} (confidence {assessment.get('confidence', 'N/A')})\n"
            f"- Primary driver: {assessment.get('primary_driver', 'N/A')}\n"
            f"- Divergence: {divergence_block.get('value', 'N/A')} — "
            f"{divergence_block.get('direction', 'N/A')} direction, "
            f"{divergence_block.get('severity', 'N/A')} severity, "
            f"interpretation: {divergence_block.get('interpretation', 'N/A')}\n"
            f"- ACWR external: {risk_block.get('acwr_external', 'N/A')}, "
            f"internal: {risk_block.get('acwr_internal', 'N/A')}\n"
            f"- Days since rest: {risk_block.get('days_since_rest', 'N/A')}\n"
            f"- Injury risk: {risk_block.get('injury_risk_level', 'N/A')}\n"
            f"- Risk flags: {risk_block.get('flags', [])}\n"
            f"- Autopsy-informed: {context_block.get('autopsy_informed', False)}\n"
            f"- Alignment trend: {context_block.get('alignment_trend', 'N/A')}\n\n"
            f"Explain the logic. Why this workout? What is the binding constraint?"
        )

        api_key = get_api_key()
        client = anthropic_sdk.Anthropic(api_key=api_key)

        logger.info(
            f"generate_why_explanation: user={user_id}, date={recommendation_date}, "
            f"model={MODEL_HAIKU}, max_tokens=500"
        )

        message = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        explanation = message.content[0].text
        logger.info(
            f"generate_why_explanation: input={message.usage.input_tokens}, "
            f"output={message.usage.output_tokens} tokens"
        )

        upsert_recommendation_conversation(
            user_id,
            recommendation_date,
            [{"role": "assistant", "content": explanation}],
        )

        return explanation

    except Exception as e:
        logger.error(f"Error in generate_why_explanation for user {user_id}: {e}", exc_info=True)
        return "Explanation unavailable."


def chat_turn(user_id, recommendation_date, user_message, conversation_history, structured_output):
    try:
        assessment = structured_output.get('assessment', {})
        risk = structured_output.get('risk', {})

        tone = get_coaching_tone_instructions(get_user_coaching_spectrum(user_id))
        system_prompt = (
            f"{tone}\n\n"
            f"You are helping an athlete understand the reasoning behind their training recommendation. "
            f"Answer questions by referencing specific metrics and constraints. Be precise, not generic.\n\n"
            f"Recommendation context:\n"
            f"- Assessment: {assessment.get('category', 'N/A')} | Risk: {risk.get('risk_level', 'N/A')}\n"
            f"- Primary driver: {assessment.get('primary_driver', 'N/A')}\n"
            f"- {NORMALIZED_DIVERGENCE_FORMULA}\n\n"
            f"Answer in 2-4 sentences. Cite specific values where relevant."
        )

        capped_history = conversation_history[-10:]
        messages = capped_history + [{"role": "user", "content": user_message}]

        api_key = get_api_key()
        client = anthropic_sdk.Anthropic(api_key=api_key)

        logger.info(
            f"chat_turn: user={user_id}, date={recommendation_date}, "
            f"model={MODEL_HAIKU}, max_tokens=500, history_len={len(capped_history)}"
        )

        message = client.messages.create(
            model=MODEL_HAIKU,
            max_tokens=500,
            system=system_prompt,
            messages=messages,
        )

        reply = message.content[0].text
        logger.info(
            f"chat_turn: SDK call successful: "
            f"{message.usage.input_tokens} input, {message.usage.output_tokens} output tokens"
        )

        updated_messages = capped_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        upsert_recommendation_conversation(user_id, recommendation_date, updated_messages)

        return reply

    except Exception as e:
        logger.error(f"Error in chat_turn for user {user_id}: {e}", exc_info=True)
        return "Sorry, I couldn't process that. Please try again."


def run_extraction_pass(user_id, recommendation_date, conversation_messages):
    try:
        if len(conversation_messages) < 2:
            logger.info(
                f"run_extraction_pass: skipping user={user_id}, date={recommendation_date} "
                f"— fewer than 2 messages"
            )
            return

        existing = get_recommendation_conversation(user_id, recommendation_date)
        if existing and existing.get('extraction_done'):
            logger.info(
                f"run_extraction_pass: skipping user={user_id}, date={recommendation_date} "
                f"— extraction already done"
            )
            return

        formatted_conversation = "\n".join(
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in conversation_messages
        )

        system_prompt = (
            "You are an AI coach reviewing a conversation between an athlete and their training assistant. "
            "Extract structured signals from the conversation. Return ONLY valid JSON, no surrounding text."
        )

        user_prompt = (
            f"CONVERSATION:\n{formatted_conversation}\n\n"
            f"Extract athlete signals. Return ONLY this JSON (use null if not mentioned):\n"
            f"{{\n"
            f'  "injury_or_pain_notes": null,\n'
            f'  "preference_note": null,\n'
            f'  "rpe_calibration_signal": null,\n'
            f'  "rpe_offset_delta": null,\n'
            f'  "nothing_significant": true\n'
            f"}}\n\n"
            f"Rules:\n"
            f"- injury_or_pain_notes: any injury, pain, physical issue, or rehab mention\n"
            f"- preference_note: any training preference (\"prefer mornings\", \"can't do back-to-back hard days\")\n"
            f"- rpe_calibration_signal: athlete says effort felt harder/easier than metrics suggest\n"
            f"- rpe_offset_delta: float — suggested RPE calibration adjustment "
            f"(+0.5 if consistently over-reporting ease)\n"
            f"- Set nothing_significant: true if none of the above apply"
        )

        api_key = get_api_key()
        client = anthropic_sdk.Anthropic(api_key=api_key)

        logger.info(
            f"run_extraction_pass: user={user_id}, date={recommendation_date}, "
            f"model={MODEL_SONNET}, max_tokens=800, messages={len(conversation_messages)}"
        )

        message = client.messages.create(
            model=MODEL_SONNET,
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw_response = message.content[0].text
        logger.info(
            f"run_extraction_pass: SDK call successful: "
            f"{message.usage.input_tokens} input, {message.usage.output_tokens} output tokens"
        )

        try:
            extracted = json.loads(raw_response)
        except json.JSONDecodeError as e:
            logger.error(
                f"run_extraction_pass: JSON parse failure for user {user_id}: {e} — raw: {raw_response[:200]}"
            )
            return

        injury_note = extracted.get('injury_or_pain_notes')
        if injury_note:
            current_model = get_athlete_model(user_id) or {}
            existing_injury_notes = current_model.get('injury_notes') or ''
            updated_injury_notes = (
                f"{existing_injury_notes}\n[{recommendation_date}] {injury_note}".lstrip('\n')
            )
            upsert_athlete_model(user_id, {'injury_notes': updated_injury_notes})
            logger.info(f"run_extraction_pass: updated injury_notes for user {user_id}")

        preference_note = extracted.get('preference_note')
        if preference_note:
            current_model = get_athlete_model(user_id) or {}
            existing_preference_notes = current_model.get('preference_notes') or ''
            updated_preference_notes = (
                f"{existing_preference_notes}\n[{recommendation_date}] {preference_note}".lstrip('\n')
            )
            upsert_athlete_model(user_id, {'preference_notes': updated_preference_notes})
            logger.info(f"run_extraction_pass: updated preference_notes for user {user_id}")

        rpe_offset_delta = extracted.get('rpe_offset_delta')
        if rpe_offset_delta is not None:
            try:
                delta = float(rpe_offset_delta)
                current_model = get_athlete_model(user_id) or {}
                current_offset = float(current_model.get('rpe_calibration_offset') or 0.0)
                current_count = int(current_model.get('rpe_sample_count') or 0)
                new_offset = max(-2.0, min(2.0, current_offset + delta))
                upsert_athlete_model(user_id, {
                    'rpe_calibration_offset': new_offset,
                    'rpe_sample_count': current_count + 1,
                })
                logger.info(
                    f"run_extraction_pass: updated rpe_calibration_offset to {new_offset} "
                    f"for user {user_id}"
                )
            except (TypeError, ValueError) as e:
                logger.error(f"run_extraction_pass: invalid rpe_offset_delta value for user {user_id}: {e}")

        mark_conversation_extraction_done(user_id, recommendation_date, extracted)
        logger.info(f"run_extraction_pass: marked extraction done for user {user_id}, date={recommendation_date}")

    except Exception as e:
        logger.error(f"Error in run_extraction_pass for user {user_id}: {e}", exc_info=True)
