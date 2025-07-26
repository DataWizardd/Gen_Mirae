# clova_config.py
# -*- coding: utf-8 -*-

import re

# 1) 기본 system prompt (필요에 따라 덮어쓰기 가능)
SYSTEM_PROMPT = "당신은 친절한 도우미입니다."

# 2) Clova API 호출 파라미터
#    - 실제 사용 가능한 모델 ID로 바꿔주세요 (예: "clova-chat-v1" 등)
MODEL_PARAMS = {
    "model":        "clova-chat-v1",
    "temperature":  0.7,
    "top_p":        0.9,
    "max_tokens":   2048,
    "stream":       True,
}

def get_persona_agent(table_data: list[dict]) -> str:
    """
    주식 보유 현황(table_data)을 받아
    '페르소나' 형태의 설명문을 생성합니다.
    """
    lines = ["사용자는 다음과 같은 주식을 보유하고 있습니다:"]
    for row in table_data:
        lines.append(
            f"- {row['종목명']} {row['수량']}주 (평균단가 {row['평균단가']})"
        )
    return "\n".join(lines)

def remove_duplicate_sentences(text: str) -> str:
    """
    응답 텍스트에서 중복 문장 제거.
    문장을 마침표(.), 물음표(?), 느낌표(!) 로 분할한 뒤
    중복을 걸러내고 재조합합니다.
    """
    # 문장 경계 기준으로 분할
    parts = re.split(r'(?<=[\.\?\!])\s*', text)
    seen = set()
    result = []
    for part in parts:
        p = part.strip()
        if not p or p in seen:
            continue
        seen.add(p)
        result.append(p)
    return " ".join(result)
