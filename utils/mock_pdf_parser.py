from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import List, Optional, Tuple

try:
    # pdfminer.six (preferred)
    from pdfminer.high_level import extract_pages, extract_text
    from pdfminer.layout import LTChar, LTTextContainer

    _PDFMINER_AVAILABLE = True
except Exception:
    extract_pages = None  # type: ignore
    extract_text = None  # type: ignore
    LTChar = None  # type: ignore
    LTTextContainer = None  # type: ignore
    _PDFMINER_AVAILABLE = False

from PyPDF2 import PdfReader


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
    if _PDFMINER_AVAILABLE and extract_text is not None:
        text = extract_text(pdf_path) or ""
    else:
        # Fallback to PyPDF2 (less reliable layout, but keeps app usable)
        reader = PdfReader(pdf_path)
        text_parts = []
        for page in reader.pages:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:
                text_parts.append("")
        text = "\n".join(text_parts)
    lines = [ln.strip() for ln in text.splitlines()]
    return [ln for ln in lines if ln]


def extract_correct_option_ids_from_pdf(pdf_path: str) -> List[str]:
    """
    Some IITM PDFs embed correct options by coloring the option-id text (green).
    This reuses the same technique as `pages/3_Response_Sheet_Evaluator_[Beta].py`.
    Returns a list of option IDs like '6406531562151' that are marked correct.
    """
    if not _PDFMINER_AVAILABLE or extract_pages is None:
        # Without pdfminer we cannot reliably inspect colors.
        return []

    correct_ids: List[str] = []
    # Colors seen in the existing codebase:
    # - green: (0, 0.50196, 0)
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                is_correct = False
                for text_line in element:
                    # `text_line` is usually LTTextLineHorizontal, but be defensive:
                    # some layout objects may not be iterable in certain pdfminer versions.
                    try:
                        iterator = iter(text_line)  # type: ignore[arg-type]
                    except TypeError:
                        continue

                    for character in iterator:
                        if isinstance(character, LTChar):
                            try:
                                if character.graphicstate.ncolor == (0, 0.50196, 0):
                                    is_correct = True
                                    break
                            except Exception:
                                # If color info isn't available, skip.
                                pass
                    if is_correct:
                        break

                if is_correct:
                    txt = (element.get_text() or "").strip()
                    if "640653" in txt and "." in txt:
                        correct_ids.append(txt.split(".")[0].strip())

    # Deduplicate, keep order
    seen = set()
    out = []
    for cid in correct_ids:
        if cid not in seen:
            seen.add(cid)
            out.append(cid)
    return out


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


_IITM_QNO_RE = re.compile(r"^Question\s+Number\s*:\s*(\d{1,4})\b", re.IGNORECASE)
_IITM_OPT_ID_RE = re.compile(r"^(640653\d+)\.$")


def parse_iitm_question_paper(
    lines: List[str], correct_option_ids: Optional[List[str]] = None
) -> Tuple[List[ParsedQuestion], dict]:
    """
    Parser for IITM exam PDFs like the one in your debug output:
      - 'Question Number : 152 ...'
      - 'Options :' then option-id lines like '6406531562151.' followed by option text lines.

    If `correct_option_ids` is provided (from green-colored IDs), we compute the correct option index.
    """
    correct_set = set(correct_option_ids or [])
    debug = {
        "total_lines": len(lines),
        "detected_questions": 0,
        "questions_missing_answers": 0,
        "questions_missing_options": 0,
        "notes": [],
        "used_parser": "iitm_question_paper",
        "correct_ids_detected": len(correct_option_ids or []),
    }

    questions: List[ParsedQuestion] = []

    cur_q_no: Optional[int] = None
    cur_q_text: List[str] = []
    cur_options: List[str] = []
    cur_option_ids: List[str] = []

    in_options = False
    awaiting_opt_text = False

    def flush():
        nonlocal cur_q_no, cur_q_text, cur_options, cur_option_ids, in_options, awaiting_opt_text
        if cur_q_no is None:
            return

        correct_index = None
        if cur_option_ids and correct_set:
            for idx, oid in enumerate(cur_option_ids, start=1):
                if oid in correct_set:
                    # For MCQ there should be one; for MSQ we currently pick the first.
                    correct_index = idx
                    break

        questions.append(
            ParsedQuestion(
                q_no=cur_q_no,
                question=" ".join(cur_q_text).strip(),
                options=[o.strip() for o in cur_options if o.strip()],
                correct_index=correct_index,
            )
        )

        cur_q_no = None
        cur_q_text = []
        cur_options = []
        cur_option_ids = []
        in_options = False
        awaiting_opt_text = False

    for ln in lines:
        m_q = _IITM_QNO_RE.match(ln)
        if m_q:
            flush()
            cur_q_no = int(m_q.group(1))
            cur_q_text = []
            cur_options = []
            cur_option_ids = []
            in_options = False
            awaiting_opt_text = False
            continue

        if cur_q_no is None:
            continue

        if ln.strip().lower() == "options :".lower() or ln.strip().lower().startswith("options :"):
            in_options = True
            awaiting_opt_text = False
            continue

        if in_options:
            m_oid = _IITM_OPT_ID_RE.match(ln.strip())
            if m_oid:
                cur_option_ids.append(m_oid.group(1))
                cur_options.append("")  # placeholder to fill
                awaiting_opt_text = True
                continue

            # Option text can span multiple lines. Attach to last option.
            if awaiting_opt_text and cur_options:
                if cur_options[-1]:
                    cur_options[-1] += " " + ln.strip()
                else:
                    cur_options[-1] = ln.strip()
                continue

        # Build question body. Skip noisy metadata lines.
        if not in_options:
            if any(
                ln.startswith(prefix)
                for prefix in (
                    "Question Id",
                    "Question Type",
                    "Is Question",
                    "Mandatory",
                    "Calculator",
                    "Response Time",
                    "Think Time",
                    "Minimum Instruction",
                    "Correct Marks",
                    "Question Label",
                    "Sub-Section",
                    "Section",
                )
            ):
                continue
            cur_q_text.append(ln.strip())

    flush()

    debug["detected_questions"] = len(questions)
    debug["questions_missing_options"] = sum(1 for q in questions if not q.options)
    debug["questions_missing_answers"] = sum(1 for q in questions if q.correct_index is None)
    if debug["questions_missing_options"]:
        debug["notes"].append("Some questions are missing options (extraction/layout issue).")
    if debug["questions_missing_answers"]:
        debug["notes"].append(
            "Correct answers were not detected. If this is an answer-key PDF, ensure correct options are visible (often in green) or present as text."
        )
    return questions, debug


def questions_to_pretty_json(questions: List[ParsedQuestion], debug: dict) -> str:
    payload = {
        "debug": debug,
        "questions": [q.to_dict() for q in questions],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)

