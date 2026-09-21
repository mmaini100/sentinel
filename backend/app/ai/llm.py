"""
LLM integration for generating root cause hypotheses.
Uses LiteLLM to support multiple providers (OpenAI, Anthropic, Gemini).
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from litellm import acompletion
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident
from app.models.root_cause import RootCauseAnalysis

logger = logging.getLogger("sentinel.ai.llm")

SYSTEM_PROMPT = """You are Sentinel's Root Cause Analysis engine. You are given a chronological
list of telemetry events (logs and metrics) associated with a single incident.
Your job is to identify the most likely root cause, explain your reasoning,
and cite the exact events that support your conclusion.

RULES:
1. Only cite event IDs that are present in the input. Never invent an event ID.
2. Base your hypothesis strictly on the provided events. Do not assume
   knowledge of the system beyond what the telemetry shows.
3. If the evidence is weak, contradictory, or insufficient to support a
   confident hypothesis, you MUST set "status" to "insufficient_evidence"
   rather than guessing. A low-confidence guess is worse than admitting
   uncertainty.
4. confidence_score reflects how strongly the cited events support the
   hypothesis, not how severe the incident is.
5. Keep "hypothesis" and "recommended_action" concise — 1-3 sentences each,
   written for an on-call engineer under time pressure.
6. "cited_event_ids" must be a subset of the input event IDs, ordered by
   causal relevance (most important first).

Respond ONLY with JSON matching the schema:
{
  "status": "success" | "insufficient_evidence",
  "hypothesis": "string",
  "confidence_score": 0.0,
  "recommended_action": "string",
  "cited_event_ids": ["uuid-1"]
}
No prose, no markdown fences.
"""


async def generate_root_cause_analysis(
    incident: Incident,
    events_data: list[dict[str, Any]],
    dependency_graph: dict[str, list[str]],
    session: AsyncSession,
) -> RootCauseAnalysis | None:
    """
    Generate an RCA for an incident using an LLM, and persist it to the DB.
    """
    try:
        # Construct the context payload
        prompt_context = {
            "incident": {
                "id": str(incident.id),
                "title": incident.title,
                "severity": incident.severity,
            },
            "events": events_data,
            "dependency_graph_context": dependency_graph,
        }

        user_prompt = f"Analyze the following incident data:\n{json.dumps(prompt_context, indent=2)}"

        logger.info(f"Triggering LLM for incident {incident.id}...")

        # We use a default fast/cheap model for local dev, but it can be overridden
        # via the standard LiteLLM environment variables (e.g. LITELLM_MODEL, OPENAI_API_KEY)
        model = "gpt-3.5-turbo"  # default, assuming OPENAI_API_KEY is provided
        
        # Check for Gemini API key first, then OpenAI
        gemini_api_key = os.environ.get("GEMINI_API_KEY")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        
        if gemini_api_key:
            model = "gemini/gemini-1.5-flash-latest"
            logger.info("Using Gemini (gemini-1.5-flash-latest) for RCA generation.")
        elif openai_api_key:
            model = "gpt-3.5-turbo"
            logger.info("Using OpenAI (gpt-3.5-turbo) for RCA generation.")
        else:
            logger.info("No API keys found, using mocked LLM response.")
            
            # Find a real event ID to cite
            cited_ids = []
            if events_data:
                cited_ids.append(events_data[-1]["id"])
                
            parsed = {
                "status": "success",
                "hypothesis": "[MOCKED] A database lock timeout caused cascading latency.",
                "confidence_score": 0.95,
                "recommended_action": "Check active database locks and query performance.",
                "cited_event_ids": cited_ids
            }
            model = "mock-gpt-3.5-turbo"

        if model != "mock-gpt-3.5-turbo":
            try:
                # Pass format as text and manually parse since litellm JSON mode is sometimes flaky with new models
                response = await acompletion(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.1,
                )

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("Empty response from LLM")
                
                # Clean markdown fences if the model still returns them
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]

                parsed = json.loads(content)
            except Exception as api_err:
                logger.error(f"LLM API call failed ({api_err}). Falling back to mock.")
                model = "mock-fallback"
                
                cited_ids = []
                fault_type = "unknown"
                
                if events_data:
                    cited_ids.append(events_data[-1]["id"])
                    
                # Analyze events to build a smart mock
                for e in events_data:
                    if "payload" in e:
                        p = e["payload"]
                        if isinstance(p, dict):
                            # Try parsing string payload if it's double serialized
                            pass
                        elif isinstance(p, str):
                            try:
                                p = json.loads(p)
                            except:
                                p = {}
                                
                        if p.get("metric_name") == "request_latency_ms" and float(p.get("value", 0)) > 200:
                            fault_type = "latency"
                        elif p.get("metric_name") == "error_rate" and float(p.get("value", 0)) > 0.3:
                            fault_type = "errors"
                        elif p.get("metric_name") == "cpu_percent" and float(p.get("value", 0)) > 80:
                            fault_type = "cpu_exhaustion"
                        elif "client error 429" in p.get("message", ""):
                            fault_type = "rate_limit"
                
                if fault_type == "latency":
                    hypothesis = "[FALLBACK MOCK] A significant latency spike was detected, likely caused by downstream dependency saturation or a slow database query."
                    action = "Scale up the database read replicas and investigate the slow query logs."
                elif fault_type == "errors":
                    hypothesis = "[FALLBACK MOCK] A massive burst of HTTP 5xx errors was detected, indicating a potential misconfiguration or crashing pods."
                    action = "Immediately rollback the latest deployment and check container crash loop logs."
                elif fault_type == "cpu_exhaustion":
                    hypothesis = "[FALLBACK MOCK] CPU utilization peaked above critical thresholds, leading to thread starvation and cascading failures."
                    action = "Increase the CPU resource limits for the affected pods in Kubernetes."
                elif fault_type == "rate_limit":
                    hypothesis = "[FALLBACK MOCK] Upstream API rate limits (HTTP 429) were hit, causing the gateway to reject incoming requests."
                    action = "Increase the rate limit quota in the API Gateway configuration or implement exponential backoff."
                else:
                    hypothesis = f"[FALLBACK MOCK] Detected critical anomaly footprint across {len(events_data)} telemetry events. Suspected resource exhaustion."
                    action = "Review system metrics and application logs for the affected services."
                
                parsed = {
                    "status": "success",
                    "hypothesis": hypothesis,
                    "confidence_score": 0.88,
                    "recommended_action": action,
                    "cited_event_ids": cited_ids
                }

        rca = RootCauseAnalysis(
            id=uuid.uuid4(),
            incident_id=incident.id,
            hypothesis=parsed.get("hypothesis", "Failed to parse hypothesis."),
            confidence=float(parsed.get("confidence_score", 0.0)),
            cited_event_ids=parsed.get("cited_event_ids", []),
            llm_provider_used=model,
            raw_llm_response=parsed,
        )

        session.add(rca)
        await session.commit()

        logger.info(
            f"Generated RCA for incident {incident.id}: "
            f"confidence={rca.confidence:.2f}, hypothesis='{rca.hypothesis[:50]}...'"
        )
        return rca

    except Exception as e:
        logger.error(f"Failed to generate RCA for incident {incident.id}: {e}")
        await session.rollback()
        return None
