import json
import os

import openai
from dotenv import load_dotenv

load_dotenv()


class LLMError(Exception):
    """화면에 그대로 보여 줄 한국어 한 줄 메시지."""


def ask_json(instructions, user_input, schema, name):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise LLMError("OPENAI_API_KEY 가 없어요. .env 파일을 확인해 주세요.")
    try:
        res = openai.OpenAI(api_key=key).responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
            instructions=instructions,
            input=user_input,
            text={"format": {"type": "json_schema", "name": name, "schema": schema, "strict": True}},
        )
        return json.loads(res.output_text)
    except openai.AuthenticationError:
        raise LLMError("API 키가 올바르지 않아요. .env 의 키를 확인해 주세요.") from None
    except openai.RateLimitError:
        raise LLMError("크레딧이 부족하거나 요청이 너무 많아요. 결제 · 사용량을 확인해 주세요.") from None
    except openai.APIConnectionError:
        raise LLMError("OpenAI 에 연결하지 못했어요. 인터넷 연결을 확인해 주세요.") from None
    except (openai.OpenAIError, ValueError):
        raise LLMError("AI 응답을 받지 못했어요. 잠시 뒤 다시 시도해 주세요.") from None
