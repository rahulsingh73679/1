from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import List, Optional, Tuple

from pdfminer.high_level import extract_text


@dataclass
class ParsedQuestion:
    q_no: int
    question: str
    options: List[str]
    # For MCQ we store 1-based index of correct option (1..len(options))
    correct_index: Optional[int] = None
    correct_text: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "q_no": self.q_no,
            "question": self.question,
            "options": self.options,
            "correct_index": self.correct_index,
            "correct_text": self.correct_text,
        }


def extract_pdf_text_to_lines(pdf_path: str) -> List[str]:
    """
    Extract text with pdfminer (better layout handling than PyPDF2 in many cases).
    Returns cleaned non-empty lines.
    """
    text = extract_text(pdf_path) or ""
    lines = [ln.strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln]


_Q_START_RE = re.compile(
    r"^(?:Q(?:uestion)?\s*)?(\d{1,3})\s*[\.\)\:]\s*(.+)$",
    flags=re.IGNORECASE,
)

_Q_START_FALLBACK_RE = re.compile(
    r"^Question\s+Number\s*[:\-]\s*(\d{1,3})\s*$",
    flags=re.IGNORECASE,
)

_OPT_RE = re.compile(
    r"^\(?([A-Da-d]|[1-8])\)?\s*[\.\)\:]\s*(.+)$"
)

_ANSWER_RE_LIST = [
    re.compile(r"^(?:Answer|Ans|Correct\s*Answer)\s*[:\-]\s*(.+)$", re.IGNORECASE),
    re.compile(r"^Correct\s*option\s*[:\-]\s*(.+)$", re.IGNORECASE),
]


def _normalize_answer_token(s: str) -> str:
    s = s.strip()
    # Remove brackets like (B), [B], etc.
    s = re.sub(r"^[\(\[\{]\s*", "", s)
    s = re.sub(r"\s*[\)\]\}]$", "", s)
    # Take first token before whitespace/comma
    s = re.split(r"[\s,;/]+", s)[0].strip()
    return s


def parse_questions_from_lines(lines: List[str]) -> Tuple[List[ParsedQuestion], dict]:
    """
    Heuristic parser for IITM-style PDFs or similar.
    Supports MCQ where options are A-D or 1..N.
    Detects answer lines like:
      - Answer: B
      - Correct Answer: (2)
      - Ans: A
    Returns (questions, debug_info).
    """
    debug = {
        "total_lines": len(lines),
        "detected_questions": 0,
        "questions_missing_answers": 0,
        "questions_missing_options": 0,
        "notes": [],
    }

    questions: List[ParsedQuestion] = []

    cur_q_no: Optional[int] = None
    cur_q_text_parts: List[str] = []
    cur_opts: List[str] = []
    cur_correct: Optional[int] = None
    cur_correct_text: Optional[str] = None

    def flush():
        nonlocal cur_q_no, cur_q_text_parts, cur_opts, cur_correct, cur_correct_text
        if cur_q_no is None:
            return

        q_text = " ".join(cur_q_text_parts).strip()
        q = ParsedQuestion(
            q_no=cur_q_no,
            question=q_text,
            options=[o.strip() for o in cur_opts if o.strip()],
            correct_index=cur_correct,
            correct_text=cur_correct_text,
        )
        questions.append(q)

        cur_q_no = None
        cur_q_text_parts = []
        cur_opts = []
        cur_correct = None
        cur_correct_text = None

    in_question_body = False

    for ln in lines:
        m_q = _Q_START_RE.match(ln)
        if m_q:
            flush()
            cur_q_no = int(m_q.group(1))
            cur_q_text_parts = [m_q.group(2)]
            cur_opts = []
            cur_correct = None
            cur_correct_text = None
            in_question_body = True
            continue

        # Some PDFs have a separate "Question Number: X" line, then the label later.
        m_q2 = _Q_START_FALLBACK_RE.match(ln)
        if m_q2:
            flush()
            cur_q_no = int(m_q2.group(1))
            cur_q_text_parts = []
            cur_opts = []
            cur_correct = None
            cur_correct_text = None
            in_question_body = True
            continue

        if cur_q_no is None:
            continue

        # Detect answer lines
        ans_hit = None
        for ans_re in _ANSWER_RE_LIST:
            ma = ans_re.match(ln)
            if ma:
                ans_hit = ma.group(1)
                break
        if ans_hit is not None:
            token = _normalize_answer_token(ans_hit)
            # Map token to index if possible
            if re.fullmatch(r"[A-Da-d]", token):
                cur_correct = ord(token.upper()) - ord("A") + 1
            elif re.fullmatch(r"\d{1,2}", token):
                cur_correct = int(token)
            else:
                # If answer is a literal option text, we can resolve later
                cur_correct_text = ans_hit.strip()
            continue

        # Detect options
        m_opt = _OPT_RE.match(ln)
        if m_opt:
            opt_token = m_opt.group(1).strip()
            opt_text = m_opt.group(2).strip()
            # Normalize option ordering: we store just texts in order encountered.
            cur_opts.append(opt_text)
            in_question_body = True
            continue

        # Otherwise, treat as question body continuation until options begin.
        if in_question_body:
            cur_q_text_parts.append(ln)

    flush()

    # Post-process: resolve correct_text to index if possible
    for q in questions:
        if q.correct_index is None and q.correct_text and q.options:
            try:
                idx = next(
                    (i + 1 for i, opt in enumerate(q.options) if q.correct_text.lower() in opt.lower()),
                    None,
                )
                q.correct_index = idx
            except Exception:
                pass

    debug["detected_questions"] = len(questions)
    debug["questions_missing_answers"] = sum(1 for q in questions if q.correct_index is None)
    debug["questions_missing_options"] = sum(1 for q in questions if not q.options)
    if debug["questions_missing_answers"] > 0:
        debug["notes"].append(
            "Some questions are missing answers (PDF may not include answers, or format differs)."
        )
    if debug["questions_missing_options"] > 0:
        debug["notes"].append(
            "Some questions are missing options (PDF format may differ or text extraction failed)."
        )
    return questions, debug


def questions_to_pretty_json(questions: List[ParsedQuestion], debug: dict) -> str:
    payload = {
        "debug": debug,
        "questions": [q.to_dict() for q in questions],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

