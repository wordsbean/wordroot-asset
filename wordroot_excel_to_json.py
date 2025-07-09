import pandas as pd
import os
import json
from tqdm import tqdm # 진행률 표시 라이브러리 (설치 필요: pip install tqdm)
import re # 정규 표현식 모듈 추가

# --- 설정 (이 부분을 당신의 환경에 맞게 수정하세요) ---
XLSX_FILE = 'final_structured_data_with_all_info_중급예문_최종.xlsx' # 원본 엑셀 파일명
OUTPUT_JSON_FILE = 'wordroot_data.json' # 생성될 JSON 파일명
OUTPUT_DIR = 'D:/WordsRoot/wordroot-asset/wordroot-project/data' # JSON 파일이 저장될 디렉토리 (★ 경로 수정)

# --- GitHub Pages 기본 URL (매우 중요! 반드시 당신의 URL로 변경하세요) ---
# wordroot-asset 리포지토리의 wordroot-project 폴더까지 포함해야 합니다.
GITHUB_PAGES_ASSETS_BASE_URL = 'https://wordsbean.github.io/wordroot-asset/wordroot-project/' # ★ URL 수정

# GitHub 저장소 내 이미지 및 오디오 폴더 경로 (슬래시로 끝나는지 확인)
IMAGE_PATH_IN_REPO = 'images/' # images/ 폴더 안에 이미지 파일이 있다면
AUDIO_PATH_IN_REPO = 'audios/' # audios/ 폴더 안에 오디오 파일이 있다면

# --- 엑셀 컬럼명 정의 (당신의 엑셀 파일 컬럼명과 정확히 일치해야 합니다. 대소문자 구분) ---
COLUMN_NO = 'No' # 'No' 컬럼 추가
COLUMN_TYPE = 'type' # 'type' 컬럼 추가
COLUMN_ELEMENT = 'element' # 'element' 컬럼 추가
COLUMN_MEANING_ELEMENT = 'meaning' # 'meaning' 컬럼 (element의 의미)

COLUMN_DISPLAY_TEXT_ROOT = 'pre_suf_root_korean_meaning' # 'pre_suf_root_korean_meaning' 컬럼
COLUMN_EXAMPLE_WORD = 'english_word' # 'english_word' 컬럼
COLUMN_IPA_TRANSCRIPTION = 'ipa_transcription' # 'ipa_transcription' 컬럼
COLUMN_EXAMPLE_WORD_KOREAN_MEANING = 'korean_meaning' # 'korean_meaning' 컬럼 (example_word의 의미)
COLUMN_MORPHOLOGICAL_BREAKDOWN = 'morphological_breakdown_with_meaning' # 'morphological_breakdown_with_meaning' 컬럼
COLUMN_SYNONYM = 'synonym' # 'synonym' 컬럼
COLUMN_ANTONYM = 'antonym' # 'antonym' 컬럼
COLUMN_WORD_ANALYSIS = 'word_analysis' # 'word_analysis' 컬럼

# 예문 컬럼 (여러 개일 수 있으므로 리스트로 정의)
COLUMN_ENGLISH_EXAMPLES = ['english_example_sentence1', 'english_example_sentence2'] # ★ 예문 컬럼명 수정
COLUMN_KOREAN_EXAMPLES = ['korean_example_translation1', 'korean_example_translation2'] # ★ 예문 컬럼명 수정


# 이 컬럼들은 wordroot 엑셀에 없는 것으로 보이지만, 이미지/오디오 파일명이 있다면 추가해야 합니다.
# COLUMN_WORD_IMAGE = 'image_filename' # 이미지 파일명은 엑셀 컬럼에서 직접 가져옴 (현재 엑셀에 없음)
# COLUMN_THEME = 'theme' # 현재 엑셀에 없음
# COLUMN_LEVEL = 'Level' # 현재 엑셀에 없음
# COLUMN_DAY = 'Day' # 현재 엑셀에 없음

# --- 함수: 파일명으로 사용할 텍스트 클리닝 (기존 함수 재활용) ---
def clean_for_filename(text_input):
    if pd.isna(text_input): # NaN 값 처리
        return ""
    cleaned_text = str(text_input).lower()
    cleaned_text = cleaned_text.replace(' ', '_')
    cleaned_text = cleaned_text.replace("'", '')
    cleaned_text = cleaned_text.replace('"', '_')
    # 특수 문자 제거 (URL에 부적합한 모든 문자) - 영문, 숫자, 언더스코어, 하이픈, 점만 허용
    cleaned_text = re.sub(r'[^a-z0-9_.-]', '', cleaned_text)
    return cleaned_text

# --- 스크립트 시작 ---
def generate_wordroot_json():
    # 출력 디렉토리 생성
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: '{OUTPUT_DIR}'")

    # 엑셀 파일 로드
    try:
        df = pd.read_excel(XLSX_FILE)
        print(f"Successfully loaded '{XLSX_FILE}'. Total rows: {len(df)}")
    except FileNotFoundError:
        print(f"Error: XLSX file '{XLSX_FILE}' not found. Please ensure it's in the same directory as the script.")
        print("If you're using .xlsx, make sure 'openpyxl' is installed: `pip install openpyxl`")
        return
    except Exception as e:
        print(f"An error occurred while reading the XLSX: {e}")
        return

    # 필수 컬럼 존재 여부 확인 (wordroot 프로젝트에 맞게 수정)
    # 엑셀 스크린샷에 보이는 컬럼들을 기준으로 필수 컬럼 정의
    required_columns = [
        COLUMN_NO, COLUMN_TYPE, COLUMN_ELEMENT, COLUMN_MEANING_ELEMENT,
        COLUMN_DISPLAY_TEXT_ROOT, COLUMN_EXAMPLE_WORD, COLUMN_IPA_TRANSCRIPTION,
        COLUMN_EXAMPLE_WORD_KOREAN_MEANING, COLUMN_MORPHOLOGICAL_BREAKDOWN,
        COLUMN_SYNONYM, COLUMN_ANTONYM, COLUMN_WORD_ANALYSIS
    ] + COLUMN_ENGLISH_EXAMPLES + COLUMN_KOREAN_EXAMPLES # 예문 컬럼들도 포함

    missing_required_columns = [col for col in required_columns if col not in df.columns]
    if missing_required_columns:
        print(f"Error: Missing required columns in XLSX: {', '.join(missing_required_columns)}")
        print(f"Available columns: {df.columns.tolist()}")
        print("Please ensure the column names in your Excel file match the variables in the script exactly (case-sensitive).")
        return

    print(f"\nGenerating Wordroot JSON data into '{OUTPUT_DIR}'...")

    all_wordroot_data = [] # 모든 wordroot 데이터를 담을 리스트

    # 모든 행을 순회하며 각 항목에 대한 데이터 딕셔너리 생성
    for index, row_data in tqdm(df.iterrows(), total=len(df), desc="Processing wordroot entries for JSON"):
        # --- 1. 고유 ID 생성 (가장 중요!) ---
        # element와 No를 조합하여 ID 생성. 예: "un-접두사_1" -> "un-jeopdusa_1" 또는 "un_prefix_001"
        element_cleaned = clean_for_filename(row_data.get(COLUMN_ELEMENT, '')).replace('-', '') # 'un-'에서 '-' 제거
        type_cleaned = clean_for_filename(row_data.get(COLUMN_TYPE, '')).replace('사', '') # '접두사'에서 '사' 제거
        unique_id = f"{element_cleaned}_{type_cleaned}_{row_data.get(COLUMN_NO, index + 1):03d}" # 3자리 번호 (001, 002)
        
        # --- 2. 데이터 추출 및 정리 (NaN 값 처리 포함) ---
        item_no = int(row_data.get(COLUMN_NO, index + 1)) # 번호는 정수형으로
        item_type = str(row_data.get(COLUMN_TYPE, '')).strip()
        item_element = str(row_data.get(COLUMN_ELEMENT, '')).strip()
        item_meaning_element = str(row_data.get(COLUMN_MEANING_ELEMENT, '')).strip()
        item_display_text_root = str(row_data.get(COLUMN_DISPLAY_TEXT_ROOT, '')).strip()
        item_example_word = str(row_data.get(COLUMN_EXAMPLE_WORD, '')).strip()
        item_ipa_transcription = str(row_data.get(COLUMN_IPA_TRANSCRIPTION, '')).strip()
        item_example_word_korean_meaning = str(row_data.get(COLUMN_EXAMPLE_WORD_KOREAN_MEANING, '')).strip()
        item_morphological_breakdown = str(row_data.get(COLUMN_MORPHOLOGICAL_BREAKDOWN, '')).strip()
        item_synonym = str(row_data.get(COLUMN_SYNONYM, '')).strip()
        item_antonym = str(row_data.get(COLUMN_ANTONYM, '')).strip()
        item_word_analysis = str(row_data.get(COLUMN_WORD_ANALYSIS, '')).strip()

        # --- 3. 예시 문장 배열 생성 ---
        example_sentences_list = []
        for i in range(len(COLUMN_ENGLISH_EXAMPLES)):
            eng_sentence = str(row_data.get(COLUMN_ENGLISH_EXAMPLES[i], '')).strip()
            kor_sentence = str(row_data.get(COLUMN_KOREAN_EXAMPLES[i], '')).strip()
            if eng_sentence or kor_sentence: # 둘 중 하나라도 내용이 있으면 추가
                example_sentences_list.append({
                    "english": eng_sentence,
                    "korean": kor_sentence
                })

        # --- 4. 오디오 및 이미지 URL 생성 (clean_for_filename 함수 활용) ---
        # element 발음 오디오 (예: un.mp3)
        audio_url_element = f"{GITHUB_PAGES_ASSETS_BASE_URL}{AUDIO_PATH_IN_REPO}{clean_for_filename(item_element)}.mp3" if item_element else ""
        
        # example_word 발음 오디오 (예: unhappy.mp3)
        audio_url_example_word = f"{GITHUB_PAGES_ASSETS_BASE_URL}{AUDIO_PATH_IN_REPO}{clean_for_filename(item_example_word)}.mp3" if item_example_word else ""

        # 이미지 URL (example_word 기반)
        image_url = f"{GITHUB_PAGES_ASSETS_BASE_URL}{IMAGE_PATH_IN_REPO}{clean_for_filename(item_example_word)}.png" if item_example_word else ""
        # 만약 엑셀에 image_filename 컬럼이 있다면 아래처럼 사용:
        # image_filename = str(row_data.get(COLUMN_WORD_IMAGE, '')).strip()
        # image_url = f"{GITHUB_PAGES_ASSETS_BASE_URL}{IMAGE_PATH_IN_REPO}{image_filename}" if image_filename else ""


        # --- 단일 Wordroot 항목 딕셔너리 생성 ---
        wordroot_entry = {
            "id": unique_id,
            "no": item_no,
            "type": item_type,
            "element": item_element,
            "meaning": item_meaning_element,
            "display_text_root": item_display_text_root,
            "example_word": item_example_word,
            "ipa_transcription": item_ipa_transcription,
            "example_word_korean_meaning": item_example_word_korean_meaning,
            "morphological_breakdown_with_meaning": item_morphological_breakdown,
            "synonym": item_synonym,
            "antonym": item_antonym,
            "word_analysis": item_word_analysis,
            "example_sentences": example_sentences_list, # 배열로 저장
            "image_url": image_url, # 이미지 URL 추가
            "audio_url_element": audio_url_element, # element 오디오 URL
            "audio_url_example_word": audio_url_example_word # example_word 오디오 URL
        }
        all_wordroot_data.append(wordroot_entry)

    # 모든 Wordroot 데이터를 단일 JSON 파일로 저장
    json_output_full_path = os.path.join(OUTPUT_DIR, OUTPUT_JSON_FILE)
    try:
        with open(json_output_full_path, "w", encoding="utf-8") as f:
            json.dump(all_wordroot_data, f, ensure_ascii=False, indent=2) # indent=2로 보기 좋게 포맷팅
        print(f"\nSuccessfully generated Wordroot JSON file: '{json_output_full_path}'.")
        print(f"Total {len(all_wordroot_data)} wordroot entries converted.")
        print(f"Remember to upload '{OUTPUT_JSON_FILE}' to your GitHub Pages repository's {OUTPUT_DIR} folder and ensure all audio/image files exist at their specified URLs.")
    except Exception as e:
        print(f"An error occurred while writing the JSON file: {e}")

if __name__ == "__main__":
    generate_wordroot_json()