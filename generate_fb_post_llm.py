import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Tuple


DEFAULT_MODEL = "gpt-5.4-mini"
API_URL = "https://api.openai.com/v1/responses"


SYSTEM_PROMPT = """你是安親班的資深班主任文案助手。你的任務是根據輸入資料，產生 Facebook 貼文。

必須遵守：
1) 語氣自然，像真人老師分享，不要像廣告機器文。
2) 內容務必可被活動照片驗證，不可幻想不存在的細節。
3) 禁止使用空泛口號與 AI 腔，例如「在這個充滿挑戰的時代」「讓我們一起」「每一位孩子都是獨一無二」。
4) 專業風、痛點風、溫馨風必須有明顯差異。
5) 文字以繁體中文輸出。
6) 只輸出 JSON，不要加任何前後說明。"""


SINGLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["post_style", "title", "body", "hashtags", "char_count"],
    "properties": {
        "post_style": {"type": "string", "enum": ["professional", "pain_point", "warm"]},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "hashtags": {"type": "string"},
        "char_count": {"type": "integer"},
    },
}


BATCH_ITEM_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["post_style", "title", "body", "hashtags", "char_count"],
    "properties": {
        "post_style": {"type": "string", "enum": ["professional", "pain_point", "warm"]},
        "title": {"type": "string"},
        "body": {"type": "string"},
        "hashtags": {"type": "string"},
        "char_count": {"type": "integer"},
    },
}


BATCH_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["results"],
    "properties": {
        "results": {
            "type": "array",
            "minItems": 3,
            "items": BATCH_ITEM_SCHEMA,
        }
    },
}


def build_user_prompt(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any], str]:
    if "generate_styles" in payload:
        prompt = (
            "請根據輸入資料，一次產生三種風格的 FB 貼文：professional、pain_point、warm。\n\n"
            "[INPUT]\n"
            f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
            "[RULES]\n"
            "- 三篇都要基於同一活動事實，不得虛構。\n"
            "- 三篇語氣要有差異，不能只換幾個詞。\n"
            "- 每篇 80~180 字。\n"
            "- 每篇都要有 title、body、hashtags、char_count。\n"
            "- Hashtag 以單一字串輸出（例：#安親班 #美語課 #學習日常）。\n"
            "- 只輸出 JSON。\n"
        )
        return prompt, BATCH_SCHEMA, "fb_post_batch"

    prompt = (
        "請依下列輸入資料生成 1 篇 FB 貼文。\n\n"
        "[INPUT]\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "[RULES]\n"
        "- post_style=professional：重點放教學設計與可觀察成果。\n"
        "- post_style=pain_point：先點出家長痛點，再給具體做法，不能製造焦慮。\n"
        "- post_style=warm：有畫面、有溫度，但避免過度抒情。\n"
        "- 字數建議 80~180 字，最多 250 字。\n"
        "- Hashtag 請組成單一字串，空格分隔。\n"
        "- 若 title 未提供，依風格生成 1 句自然標題。\n"
        "- body 必須至少包含 1 個可被照片驗證的活動細節。\n"
        "- 只輸出 JSON。\n"
    )
    return prompt, SINGLE_SCHEMA, "fb_post_single"


def extract_output_text(response_obj: Dict[str, Any]) -> str:
    if isinstance(response_obj.get("output_text"), str) and response_obj["output_text"].strip():
        return response_obj["output_text"].strip()

    output = response_obj.get("output", [])
    chunks = []
    for item in output:
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def call_responses_api(api_key: str, model: str, user_prompt: str, schema: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
    body = {
        "model": model,
        "input": [
            {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": schema_name,
                "schema": schema,
                "strict": True,
            }
        },
    }

    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="ignore")
        return {
            "error": True,
            "error_code": "API_ERROR",
            "message": f"HTTP {exc.code}",
            "details": raw,
        }
    except urllib.error.URLError as exc:
        return {
            "error": True,
            "error_code": "NETWORK_ERROR",
            "message": str(exc),
        }

    try:
        response_obj = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "error": True,
            "error_code": "API_PARSE_ERROR",
            "message": "Responses API 回傳非 JSON",
            "details": raw,
        }

    text = extract_output_text(response_obj)
    if not text:
        return {
            "error": True,
            "error_code": "EMPTY_MODEL_OUTPUT",
            "message": "模型未回傳可解析的文字內容",
            "details": response_obj,
        }

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "error": True,
            "error_code": "MODEL_JSON_PARSE_ERROR",
            "message": "模型輸出不是合法 JSON",
            "raw_output": text,
        }

    return parsed


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FB posts via LLM (OpenAI Responses API).")
    parser.add_argument("-i", "--input", required=True, help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true", help="Only print request payload preview, do not call API")
    args = parser.parse_args()

    try:
        payload = load_json(args.input)
    except FileNotFoundError:
        print(json.dumps({"error": True, "message": f"找不到輸入檔案: {args.input}"}, ensure_ascii=False, indent=2))
        return 1
    except json.JSONDecodeError:
        print(json.dumps({"error": True, "message": "輸入 JSON 格式錯誤"}, ensure_ascii=False, indent=2))
        return 1

    user_prompt, schema, schema_name = build_user_prompt(payload)

    if args.dry_run:
        preview = {
            "mode": "dry_run",
            "model": args.model,
            "system_prompt": SYSTEM_PROMPT,
            "user_prompt": user_prompt,
            "schema_name": schema_name,
            "schema": schema,
        }
        output = json.dumps(preview, ensure_ascii=False, indent=2)
    else:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            err = {
                "error": True,
                "error_code": "MISSING_API_KEY",
                "message": "請先設定 OPENAI_API_KEY，或改用 --dry-run",
            }
            output = json.dumps(err, ensure_ascii=False, indent=2)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(output + "\n")
            else:
                print(output)
            return 1

        result = call_responses_api(api_key, args.model, user_prompt, schema, schema_name)
        output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    sys.exit(main())

