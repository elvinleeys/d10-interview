from pathlib import Path

import pandas as pd
import streamlit as st

import coach
from llm import LLMError, ask_json
from prompts import CONTEXT, INTERVIEWER, INTERVIEWER_SCHEMA, PERSONAS

st.set_page_config(page_title="AI 면접 코치")
s = st.session_state


@st.cache_data
def load_questions():
    return pd.read_csv(Path(__file__).parent / "data" / "questions.csv")


def start(name, job, company, experience):
    s.update(name=name, job=job, company=company, experience=experience,
             questions=coach.pick_questions(load_questions(), job), idx=0, follow_ups=0,
             understanding=None, stage="interview")
    first = s.questions[0]["질문"]
    s.messages = [("assistant", f"안녕하세요, {name}님. 면접을 시작할게요."), ("assistant", first)]
    s.turns = [("면접관", first)]


def answer(text):
    q = s.questions[s.idx]
    turns = s.turns + [("지원자", text)]
    instructions = INTERVIEWER.format(
        persona=PERSONAS[s.job],
        context=CONTEXT.format(company=s.company, job=s.job, experience=s.experience),
        question=q["질문"], point=q["보는 점"], experience=s.experience)
    try:
        with st.spinner("면접관이 생각 중이에요..."):
            r = ask_json(instructions, coach.format_turns(turns, s.understanding),
                         INTERVIEWER_SCHEMA, "interviewer")
    except LLMError as e:
        st.error(str(e))
        return False
    s.understanding = coach.clamp(r["understanding"], 0, 100)
    s.messages.append(("user", text))
    if coach.can_follow_up(r["follow_up"], s.follow_ups):
        s.follow_ups += 1
        s.messages.append(("assistant", r["reply"]))
        s.turns = turns + [("면접관", r["reply"])]
        return True
    # 꼬리 질문이 필요하다고 해도 한도를 넘었으면 reply 는 버리고 넘어간다
    s.messages.append(("assistant", "알겠습니다. 다음 질문으로 넘어갈게요." if r["follow_up"] else r["reply"]))
    s.idx += 1
    s.follow_ups = 0
    if s.idx < coach.TOTAL_QUESTIONS:
        nxt = s.questions[s.idx]["질문"]
        s.messages.append(("assistant", nxt))
        s.turns = [("면접관", nxt)]
    else:
        s.messages.append(("assistant", "면접이 끝났어요. 수고하셨습니다."))
        s.stage = "done"
    return True


with st.sidebar:
    st.header("상태창")
    if s.get("stage") in ("interview", "done"):
        n = min(s.idx + 1, coach.TOTAL_QUESTIONS)
        st.progress(n / coach.TOTAL_QUESTIONS, text=f"질문 {n}/{coach.TOTAL_QUESTIONS}")
        st.metric("면접관이 본 이해도", "-" if s.understanding is None else f"{s.understanding}점")
    if st.button("처음부터 다시"):
        s.clear()
        st.rerun()

if s.get("stage") not in ("interview", "done"):
    st.title("AI 면접 코치")
    with st.form("start"):
        name = st.text_input("이름")
        job = st.selectbox("직군", list(PERSONAS))
        company = st.text_input("회사")
        experience = st.text_area("내 경험 (30자 이상)")
        go = st.form_submit_button("면접 시작")
    if go:
        if not name.strip() or not company.strip():
            st.warning("이름과 회사를 적어 주세요.")
        elif len(experience.strip()) < 30:
            st.warning("내 경험을 30자 이상 적어 주세요.")
        else:
            start(name.strip(), job, company.strip(), experience.strip())
            st.rerun()
else:
    for role, text in s.messages:
        st.chat_message(role).write(text)
    if s.stage == "interview" and (text := st.chat_input("답변을 입력하세요")):
        if text.strip() and answer(text.strip()):
            st.rerun()
