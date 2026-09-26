#app/services/groq.py
import asyncio
import json
import os

from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIError,
    AsyncGroq,
    AuthenticationError,
    InternalServerError,
    RateLimitError,
)

from logger.logging import logger

load_dotenv(override=True)  

client = AsyncGroq(
    api_key= os.getenv("GROQ_API_KEY"),
    max_retries=4,
    timeout=30.0,
) 

async def gen_groq_json(payload):
    try:
        system_prompt = """
        The user will provide a payload that represents a support ticket. The payload has been validated and issued a quality check score.
        Please parse the relevant information and output it in JSON format.
        The JSON will have the following properties:

        category: Can be one of [Transaction Failure, API / Webhooks, Settlement & Payouts, Account Access, General Inquiry]
        sla_urgency: Can be one of [P1 (Critical Outage), P2 (High), P3 (Standard)]
        auto_route_to: Can be one of [On-Call Infrastructure, Payment Operations Tier 2, Merchant Support Tier 1, Self-Serve Knowledge Base]
        ○ reasoning: A concise 1-to-2 sentence justification for the classification.

        EXAMPLE INPUT: 
        {
            "ticket_id": "TCK-10492",
            "merchant_id": "mer_live_99812",
            "merchant_tier": "Enterprise",
            "contact_email": "merchant@example.com",
            "processing_timestamp": "2026-09-23T10:15:30Z",
            "issue_description": "Enterprise merchant experiencing 504 gateway timeouts on live webhook endpoints during active transaction processing.",
            "data_quality": {
                "score": 95,
                "status": "EXCELLENT",
                "flags": []
            }
        }

        EXAMPLE JSON OUTPUT:
        {
            "category": "API / Webhooks",
            "sla_urgency": "P1 (Critical Outage)",
            "auto_route_to": "On-Call Infrastructure",
            "reasoning": "Enterprise merchant experiencing 504 gateway timeouts on live webhook
            endpoints during active transaction processing."
        }
        """

        user_prompt = json.dumps(payload)

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]

        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            response_format={
                'type': 'json_object'
            }
        )

    except AuthenticationError as e:
        logger.critical("Groq Authentication failed (401): %s", e)
        return None

    except RateLimitError as e:
        logger.warning("Groq Rate Limit (429) persists after retries: %s", e)
        return None

    except InternalServerError as e:
        logger.error("Groq server error (5xx) after retries: %s", e)
        return None

    except APIConnectionError as e:
        logger.error("Failed to connect to Groq API: %s", e)
        return None

    except APIError as e:
        logger.error("Groq API returned an error (%s): %s", e.status_code, e.message)
        return None

    except Exception as e:
        logger.exception("Unexpected error during Groq call: %s", e)
        return None



    return json.loads(response.choices[0].message.content)

#     print(json.loads(response.choices[0].message.content))

# payload =  {
#             "ticket_id": "TCK-10492",
#             "merchant_id": "mer_live_99812",
#             "merchant_tier": "Enterprise",
#             "contact_email": "merchant@example.com",
#             "processing_timestamp": "2026-09-23T10:15:30Z",
#             "issue_description": "Enterprise merchant experiencing 504 gateway timeouts on live webhook endpoints during active transaction processing.",
#             "data_quality": {
#                 "score": 95,
#                 "status": "EXCELLENT",
#                 "flags": []
#             }
#         }

# asyncio.run(gen_groq_json(payload))