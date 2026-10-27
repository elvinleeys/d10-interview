TOTAL_QUESTIONS = 5
MAX_FOLLOW_UPS = 1


def pick_questions(df, job):
    """자기소개 1 + 공통 1 + 직무 1 + 경험 1 + 상황 1"""
    common = df[df["직군"] == "공통"]
    intro = common[common["질문"].str.contains("자기소개")].iloc[0]
    rest = common.drop(intro.name).sample(1).iloc[0]
    mine = df[df["직군"] == job]
    rows = [intro, rest] + [mine[mine["유형"] == t].sample(1).iloc[0] for t in ("직무", "경험", "상황")]
    return [{"질문": r["질문"], "보는 점": r["보는 점"]} for r in rows]


def can_follow_up(ai_wants, done_count):
    """AI 가 더 묻자고 해도 질문당 MAX_FOLLOW_UPS 까지만"""
    return ai_wants and done_count < MAX_FOLLOW_UPS


def clamp(n, lo, hi):
    return max(lo, min(hi, n))


def format_turns(turns, understanding):
    """현재 질문의 대화 기록(+직전 이해도)을 AI 입력 글로 만든다"""
    lines = [f"{who}: {text}" for who, text in turns]
    if understanding is not None:
        lines.append(f"직전 understanding: {understanding}")
    return "\n".join(lines)
