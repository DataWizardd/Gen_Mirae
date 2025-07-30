import logging
import os
from typing import Dict, List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def register_korean_font():
    """한글 폰트를 reportlab에 등록합니다."""
    font_path_win = "c:/Windows/Fonts/malgun.ttf"
    font_path_mac = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
    font_path_linux = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    font_name = "KoreanFont"
    
    try:
        if os.path.exists(font_path_win):
            pdfmetrics.registerFont(TTFont(font_name, font_path_win))
        elif os.path.exists(font_path_mac):
            pdfmetrics.registerFont(TTFont(font_name, font_path_mac))
        elif os.path.exists(font_path_linux):
            pdfmetrics.registerFont(TTFont(font_name, font_path_linux))
        else:
            font_name = "Helvetica"
        return font_name
    except Exception as e:
        logging.error(f"폰트 등록 중 오류 발생: {e}")
        return "Helvetica"

KOREAN_FONT_NAME = register_korean_font()

def generate_pdf_report(report_data: Dict) -> str:
    """
    주어진 리포트 데이터로 PDF 파일을 생성하고 로컬 임시 폴더에 저장합니다.
    
    Returns:
        str: 생성된 PDF 파일의 로컬 경로
    """
    title = report_data.get("title", "Financial Report")
    sections = report_data.get("sections", [])
    
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c.isspace()]).rstrip()
    file_name = f"{safe_title.replace(' ', '_')}.pdf"
    
    os.makedirs("/tmp", exist_ok=True)
    local_path = f"/tmp/{file_name}"

    logging.info(f"'{local_path}'에 PDF 생성을 시작합니다...")

    doc = SimpleDocTemplate(local_path)
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(name='TitleStyle', fontName=KOREAN_FONT_NAME, fontSize=24, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='HeadingStyle', fontName=KOREAN_FONT_NAME, fontSize=18, spaceAfter=10))
    styles.add(ParagraphStyle(name='BodyStyle', fontName=KOREAN_FONT_NAME, fontSize=10, leading=14))

    story = [Paragraph(title, styles['TitleStyle'])]
    
    for section in sections:
        story.append(Spacer(1, 12))
        story.append(Paragraph(section['heading'], styles['HeadingStyle']))
        content_with_br = section['content'].replace('\n', '<br/>')
        story.append(Paragraph(content_with_br, styles['BodyStyle']))
        
    doc.build(story)
    
    logging.info(f"PDF 생성이 완료되었습니다: {local_path}")
    return local_path

if __name__ == '__main__':
    dummy_report = {
        "title": "AAPL 종목 분석 리포트",
        "sections": [
            { "heading": "재무 요약", "content": "이 회사는 매우 돈을 잘 법니다.\n- 매출액: 100조\n- 영업이익: 20조"},
            { "heading": "이벤트 분석", "content": "최근 신제품 발표로 주가가 올랐습니다. 긍정적인 소식입니다."},
        ]
    }
    pdf_path = generate_pdf_report(dummy_report)
    print(f"생성된 PDF 경로: {pdf_path}")
