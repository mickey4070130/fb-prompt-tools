import argparse
import json
import re
import sys
from typing import Any, Dict, List


DISALLOWED_PHRASES = [
    "在這個充滿挑戰的時代",
    "讓我們一起",
    "每一位孩子都是獨一無二",
]

REQUIRED_FIELDS = [
    "activity_name",
    "course_type",
    "class_group",
    "activity_highlights",
    "child_observations",
    "teaching_goal",
    "parent_message",
    "cta",
    "hashtags",
]

STYLE_VALUES = {"professional", "pain_point", "warm"}


def fail(message: str, missing_fields: List[str] = None) -> Dict[str, Any]:
    return {
        "error": True,
        "error_code": "VALIDATION_ERROR",
        "message": message,
        "missing_fields": missing_fields or [],
    }


def normalize_text(text: str) -> str:
    for phrase in DISALLOWED_PHRASES:
        text = text.replace(phrase, "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def validate_common(payload: Dict[str, Any]) -> Dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if field not in payload]
    if missing:
        return fail("缺少必填欄位", missing)

    if not isinstance(payload["activity_highlights"], list) or not payload["activity_highlights"]:
        return fail("activity_highlights 必須是非空陣列", ["activity_highlights"])
    if not isinstance(payload["child_observations"], list) or not payload["child_observations"]:
        return fail("child_observations 必須是非空陣列", ["child_observations"])
    if not isinstance(payload["hashtags"], list) or len(payload["hashtags"]) < 3:
        return fail("hashtags 必須是陣列且至少 3 筆", ["hashtags"])

    for tag in payload["hashtags"]:
        if not isinstance(tag, str) or not tag.startswith("#"):
            return fail("hashtags 每筆都需以 # 開頭", ["hashtags"])

    return {}


def join_items(items: List[str]) -> str:
    return "、".join([str(x).strip() for x in items if str(x).strip()])


def render_title(style: str, data: Dict[str, Any]) -> str:
    if data.get("title"):
        return str(data["title"]).strip()
    if style == "professional":
        return f"今天的{data['activity_name']}，孩子不只完成，更學會方法"
    if style == "pain_point":
        return "孩子不是不會，是需要對的方法"
    return "今天又收集到孩子們一個很棒的成長瞬間"


def render_body(style: str, data: Dict[str, Any]) -> str:
    highlights = join_items(data["activity_highlights"])
    observations = join_items(data["child_observations"])

    if style == "professional":
        body = (
            f"今天在{data['course_type']}的{data['activity_name']}，"
            f"我們帶{data['class_group']}孩子進行{highlights}。"
            f"課程重點放在{data['teaching_goal']}，不只完成任務，也練習真正理解與表達。"
            f"從現場可以看到孩子們{observations}。"
            f"{data['parent_message']} {data['cta']}"
        )
    elif style == "pain_point":
        pain_point_topic = data.get("pain_point_topic", "").strip()
        if not pain_point_topic:
            raise ValueError("pain_point style requires pain_point_topic")
        body = (
            f"不少家長會擔心「{pain_point_topic}」，這是很常見的情況。"
            f"在{data['course_type']}裡，我們用{highlights}把孩子從被動完成，帶到知道自己在學什麼。"
            f"以今天{data['activity_name']}來看，孩子們已經{observations}。"
            f"{data['parent_message']} {data['cta']}"
        )
    else:
        body = (
            f"今天的{data['activity_name']}很有活力，{data['class_group']}的孩子在{highlights}時特別投入。"
            f"有人一開始有點害羞，但在同學鼓勵下也願意嘗試，現場看得到孩子們{observations}。"
            f"這些小小進步都在累積{data['teaching_goal']}。"
            f"{data['parent_message']} {data['cta']}"
        )

    return normalize_text(body)


def render_post(style: str, data: Dict[str, Any]) -> Dict[str, Any]:
    body = render_body(style, data)
    hashtags = " ".join(data["hashtags"])
    return {
        "post_style": style,
        "title": render_title(style, data),
        "body": body,
        "hashtags": hashtags,
        "char_count": len(body),
    }


def generate_single(payload: Dict[str, Any]) -> Dict[str, Any]:
    errors = validate_common(payload)
    if errors:
        return errors

    style = payload.get("post_style")
    if style not in STYLE_VALUES:
        return fail("post_style 必須是 professional/pain_point/warm", ["post_style"])

    if style == "pain_point" and not payload.get("pain_point_topic"):
        return fail("pain_point 風格缺少 pain_point_topic", ["pain_point_topic"])

    try:
        return render_post(style, payload)
    except ValueError as exc:
        return fail(str(exc), ["pain_point_topic"])


def generate_batch(payload: Dict[str, Any]) -> Dict[str, Any]:
    styles = payload.get("generate_styles")
    shared = payload.get("shared_input")
    overrides = payload.get("style_overrides", {})

    if not isinstance(styles, list) or not styles:
        return fail("generate_styles 必須是非空陣列", ["generate_styles"])
    if not isinstance(shared, dict):
        return fail("shared_input 必須是物件", ["shared_input"])

    common_errors = validate_common(shared)
    if common_errors:
        return common_errors

    results = []
    for style in styles:
        if style not in STYLE_VALUES:
            return fail(f"不支援的風格: {style}", ["generate_styles"])

        merged = dict(shared)
        if isinstance(overrides.get(style), dict):
            merged.update(overrides[style])

        merged["post_style"] = style
        post = generate_single(merged)
        if post.get("error"):
            return post
        results.append(post)

    return {"results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate FB posts for after-school program.")
    parser.add_argument("-i", "--input", required=True, help="Input JSON file path")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        result = fail(f"找不到輸入檔案: {args.input}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    except json.JSONDecodeError:
        result = fail("輸入 JSON 格式錯誤")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    if "generate_styles" in payload:
        result = generate_batch(payload)
    else:
        result = generate_single(payload)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)

    return 0 if not result.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())

