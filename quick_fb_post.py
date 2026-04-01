import argparse
import json
import sys
from typing import Dict, List

from generate_fb_post import generate_batch, generate_single


def split_list(value: str) -> List[str]:
    text = (value or "").strip()
    if not text:
        return []
    normalized = text.replace("，", ",").replace("、", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def prompt_input(label: str, default: str = "", required: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default else ""
        value = input(f"{label}{suffix}: ").strip()
        if not value:
            value = default
        if required and not value:
            print("此欄位必填，請重新輸入。")
            continue
        return value


def run_interactive() -> Dict:
    print("請輸入活動資訊，直接按 Enter 可使用預設值。")
    activity_name = prompt_input("活動名稱", required=True)
    course_type = prompt_input("課程類型", "美語課")
    class_group = prompt_input("班別", "中年級班")
    highlights_raw = prompt_input("活動亮點（用逗號分隔）", "分組闖關,句型配對,角色對話")
    observations_raw = prompt_input("孩子表現（用逗號分隔）", "主動舉手回答,願意完整說句子,同組互相提醒發音")
    teaching_goal = prompt_input("教學目標", "提升口說勇氣與句型熟悉度")
    parent_message = prompt_input("給家長的訊息", "回家可用今天的 3 個句型做 5 分鐘口說練習。")
    cta = prompt_input("CTA", "想了解課程安排，歡迎私訊我們。")
    hashtags_raw = prompt_input("Hashtags（用逗號分隔）", "#安親班,#美語課,#英文口說,#學習日常")
    pain_point_topic = prompt_input("痛點主題", "孩子背了單字卻不敢開口說英文")

    payload = {
        "generate_styles": ["professional", "pain_point", "warm"],
        "shared_input": {
            "activity_name": activity_name,
            "course_type": course_type,
            "class_group": class_group,
            "activity_highlights": split_list(highlights_raw),
            "child_observations": split_list(observations_raw),
            "teaching_goal": teaching_goal,
            "parent_message": parent_message,
            "cta": cta,
            "hashtags": split_list(hashtags_raw),
        },
        "style_overrides": {
            "pain_point": {
                "pain_point_topic": pain_point_topic,
            }
        },
    }
    return payload


def build_payload_from_args(args: argparse.Namespace) -> Dict:
    shared = {
        "activity_name": args.activity_name,
        "course_type": args.course_type,
        "class_group": args.class_group,
        "activity_highlights": split_list(args.highlights),
        "child_observations": split_list(args.observations),
        "teaching_goal": args.goal,
        "parent_message": args.parent_message,
        "cta": args.cta,
        "hashtags": split_list(args.hashtags),
    }

    if args.style:
        payload = dict(shared)
        payload["post_style"] = args.style
        if args.style == "pain_point":
            payload["pain_point_topic"] = args.pain_point_topic
        return payload

    return {
        "generate_styles": ["professional", "pain_point", "warm"],
        "shared_input": shared,
        "style_overrides": {
            "pain_point": {
                "pain_point_topic": args.pain_point_topic,
            }
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="One-command FB post generator (interactive or args mode).")
    parser.add_argument("--activity-name", help="活動名稱")
    parser.add_argument("--course-type", default="美語課", help="課程類型")
    parser.add_argument("--class-group", default="中年級班", help="班別")
    parser.add_argument("--highlights", default="分組闖關,句型配對,角色對話", help="活動亮點（逗號分隔）")
    parser.add_argument("--observations", default="主動舉手回答,願意完整說句子,同組互相提醒發音", help="孩子表現（逗號分隔）")
    parser.add_argument("--goal", default="提升口說勇氣與句型熟悉度", help="教學目標")
    parser.add_argument("--parent-message", default="回家可用今天的 3 個句型做 5 分鐘口說練習。", help="給家長的訊息")
    parser.add_argument("--cta", default="想了解課程安排，歡迎私訊我們。", help="CTA")
    parser.add_argument("--hashtags", default="#安親班,#美語課,#英文口說,#學習日常", help="Hashtags（逗號分隔）")
    parser.add_argument("--pain-point-topic", default="孩子背了單字卻不敢開口說英文", help="痛點主題")
    parser.add_argument("--style", choices=["professional", "pain_point", "warm"], help="只產生單一風格")
    parser.add_argument("-o", "--output", help="輸出檔案路徑")
    args = parser.parse_args()

    if args.activity_name:
        payload = build_payload_from_args(args)
    else:
        payload = run_interactive()
        if args.style:
            # Interactive mode defaults to batch; if style is passed, convert to single.
            single_payload = dict(payload["shared_input"])
            single_payload["post_style"] = args.style
            if args.style == "pain_point":
                single_payload["pain_point_topic"] = payload["style_overrides"]["pain_point"]["pain_point_topic"]
            payload = single_payload

    result = generate_batch(payload) if "generate_styles" in payload else generate_single(payload)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
    else:
        print(output)

    return 0 if not result.get("error") else 1


if __name__ == "__main__":
    sys.exit(main())

