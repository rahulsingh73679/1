import os
import tempfile
from typing import Dict, List, Optional

import streamlit as st

from utils.mock_pdf_parser import (
    ParsedQuestion,
    extract_correct_option_ids_from_pdf,
    extract_pdf_pages_to_lines,
    parse_iitm_question_paper,
    parse_iitm_question_paper_from_pages,
    parse_questions_from_lines,
    questions_to_pretty_json,
)

try:
    import fitz  # PyMuPDF

    _PYMUPDF_AVAILABLE = True
except Exception:
    fitz = None  # type: ignore
    _PYMUPDF_AVAILABLE = False


st.set_page_config(page_title="Mock Test (PDF)", page_icon="📄")


def _add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://i.imgur.com/n1v7QfM.png);
                background-repeat: no-repeat;
                padding-top: 120px;
                background-position: 20px 20px;
                margin-top: 25px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _ensure_state():
    st.session_state.setdefault("mock_questions", None)
    st.session_state.setdefault("mock_debug", None)
    st.session_state.setdefault("mock_answers", {})
    st.session_state.setdefault("mock_submitted", False)
    st.session_state.setdefault("mock_pdf_bytes", None)


def _reset_exam():
    st.session_state["mock_answers"] = {}
    st.session_state["mock_submitted"] = False


def _score(questions: List[ParsedQuestion], user_answers: Dict[int, int]) -> Dict[str, float]:
    total = 0.0
    correct = 0.0
    attempted = 0

    for q in questions:
        if not q.options:
            continue
        total += 1.0
        ua = user_answers.get(q.q_no)
        if ua is None:
            continue
        attempted += 1
        if q.correct_index is not None and int(ua) == int(q.correct_index):
            correct += 1.0

    pct = (correct * 100.0 / total) if total else 0.0
    return {"total": total, "attempted": attempted, "correct": correct, "percentage": pct}


def main():
    _add_logo()
    _ensure_state()

    st.title("Mock Test from PDF (Mock Test Series Builder)")
    st.caption(
        "Upload a question paper PDF that contains questions + options + answers. "
        "We’ll show questions in order and reveal answers only after you submit."
    )

    with st.expander("PDF format assumptions (important)", expanded=False):
        st.markdown(
            """
This prototype parser works best if your PDF text contains patterns like:
- **Questions**: `Q1. ...` or `Question 1: ...`
- **Options**: `A) ...`, `B) ...` or `1) ...`, `2) ...`
- **Answer** lines: `Answer: B` / `Correct Answer: 2` / `Ans: A`

If your `AppDev2.pdf` uses a different layout, we can tune the parser quickly using the **Debug view** below.
            """
        )

    pdf = st.file_uploader("Upload Question Paper PDF (with answers)", type=["pdf"])

    col_a, col_b, col_c = st.columns([1, 1, 2])
    with col_a:
        parse_btn = st.button("Parse PDF", type="primary", disabled=pdf is None)
    with col_b:
        reset_btn = st.button("Reset Exam")
    with col_c:
        debug_mode = st.toggle("Show debug view", value=False)

    if reset_btn:
        _reset_exam()
        st.session_state["mock_questions"] = None
        st.session_state["mock_debug"] = None

    if parse_btn and pdf is not None:
        # pdfminer wants a file path
        pdf_bytes = pdf.read()
        st.session_state["mock_pdf_bytes"] = pdf_bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        try:
            pages_lines = extract_pdf_pages_to_lines(tmp_path)
            lines = [ln for page in pages_lines for ln in page]
            # Try IITM parser first (matches "Question Number : X" style)
            correct_ids = extract_correct_option_ids_from_pdf(tmp_path)
            questions, debug = parse_iitm_question_paper_from_pages(pages_lines, correct_option_ids=correct_ids)
            if not questions:
                # Fallback to generic parser
                questions, debug = parse_questions_from_lines(lines)

            st.session_state["mock_questions"] = questions
            st.session_state["mock_debug"] = {
                "parser": debug,
                "sample_lines": lines[:200],
                "correct_option_ids_detected": correct_ids[:50],
            }
            _reset_exam()
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    questions: Optional[List[ParsedQuestion]] = st.session_state.get("mock_questions")
    debug = st.session_state.get("mock_debug")

    if questions is None:
        st.info("Upload a PDF and click **Parse PDF** to begin.")
        return

    st.success(f"Parsed **{len(questions)}** questions.")
    if debug and debug.get("parser"):
        missing_a = debug["parser"].get("questions_missing_answers", 0)
        missing_o = debug["parser"].get("questions_missing_options", 0)
        if missing_a or missing_o:
            st.warning(
                f"Parser warnings: missing answers for {missing_a} questions, missing options for {missing_o} questions. "
                "Use Debug view to tune the parser for your PDF."
            )

    st.divider()
    st.subheader("Mock Test")

    st.session_state["mock_submitted"] = st.session_state.get("mock_submitted", False)

    # Render questions in serial order
    for q in sorted(questions, key=lambda x: x.q_no):
        st.markdown(f"### Q{q.q_no}")

        # If the question contains code/images in the PDF, text extraction won't capture it.
        # Show a page snapshot (best-effort) so the user can see embedded code blocks.
        if _PYMUPDF_AVAILABLE and st.session_state.get("mock_pdf_bytes") and q.page_index is not None:
            with st.expander("Show original PDF page (for code/images)", expanded=False):
                try:
                    doc = fitz.open(stream=st.session_state["mock_pdf_bytes"], filetype="pdf")
                    page = doc.load_page(int(q.page_index))
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x for readability
                    st.image(pix.tobytes("png"), caption=f"PDF page {int(q.page_index) + 1}")
                except Exception as e:
                    st.info(f"Could not render PDF page image: {e}")
        elif q.page_index is not None and not _PYMUPDF_AVAILABLE:
            st.caption("PDF page rendering unavailable (missing PyMuPDF).")

        st.write(q.question or "")

        if not q.options:
            st.warning("Options not detected for this question.")
            continue

        # Use radio for MCQ
        opt_labels = [f"{i+1}. {opt}" for i, opt in enumerate(q.options)]
        key = f"mock_q_{q.q_no}"

        if st.session_state["mock_submitted"]:
            # Lock UI after submission
            chosen = st.session_state["mock_answers"].get(q.q_no)
            st.radio("Your answer", opt_labels, index=(chosen - 1) if chosen else 0, key=key, disabled=True)
        else:
            chosen_label = st.radio("Choose an option", ["(unanswered)"] + opt_labels, index=0, key=key)
            if chosen_label != "(unanswered)":
                chosen_idx = int(chosen_label.split(".", 1)[0])
                st.session_state["mock_answers"][q.q_no] = chosen_idx
            else:
                st.session_state["mock_answers"].pop(q.q_no, None)

        # Reveal answers only after submit
        if st.session_state["mock_submitted"]:
            correct = q.correct_index
            if correct is None:
                st.info("Correct answer not found in PDF for this question.")
            else:
                ua = st.session_state["mock_answers"].get(q.q_no)
                if ua == correct:
                    st.success(f"Correct. Answer: **{correct}**")
                else:
                    st.error(f"Wrong. Correct answer: **{correct}**")

        st.markdown("---")

    submit = st.button("Submit Mock Test", type="primary", disabled=st.session_state["mock_submitted"])
    if submit:
        st.session_state["mock_submitted"] = True

    if st.session_state["mock_submitted"]:
        s = _score(questions, st.session_state["mock_answers"])
        st.divider()
        st.subheader("Result")
        st.markdown(
            f"""
**Score:** {int(s['correct'])} / {int(s['total'])}  
**Attempted:** {int(s['attempted'])}  
**Percentage:** {s['percentage']:.1f}%  
            """
        )

    if debug_mode:
        st.divider()
        st.subheader("Debug view (for improving parsing)")
        if debug:
            st.write("Parser summary:")
            st.json(debug.get("parser", {}))
            if debug.get("correct_option_ids_detected"):
                st.write("First detected correct option IDs (max 50):")
                st.code("\n".join(debug.get("correct_option_ids_detected", [])))
            st.write("First ~200 extracted lines:")
            st.code("\n".join(debug.get("sample_lines", [])))
        st.write("Parsed output (JSON):")
        st.code(questions_to_pretty_json(questions, debug.get("parser", {}) if debug else {}))


if __name__ == "__main__":
    main()

