import json
import pandas as pd
import os
import shutil
import csv

# --- 設定 ---
# 実行場所に応じてパスを調整
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))  # src/converters -> src -> root
# ※注意: 実行環境のフォルダ構成に合わせて PROJECT_ROOT を適切に設定してください
# 今回は src/converters から2つ上のディレクトリをルートとします

INPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'drafts_json')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'output_csv')
TEMPLATE_FILE = os.path.join(PROJECT_ROOT, 'templates', 'header_template.csv')

def get_virtual_date_id(unit_num, prefix, counter):
    """Unit番号に基づいて仮想日付IDを生成"""
    virtual_date = f"2501{str(unit_num).zfill(2)}"
    return f"{prefix}{virtual_date}{str(counter).zfill(4)}"

def generate_csv_final(json_filename):
    # ファイルパス解決の強化
    json_path = os.path.join(INPUT_DIR, json_filename)
    if not os.path.exists(json_path):
        # カレントディレクトリからの相対パスも試行
        json_path = os.path.join('data/drafts_json', json_filename)

    if not os.path.exists(json_path):
        print(f"エラー: {json_path} が見つかりません。パスを確認してください。")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    unit_num = data.get('unit_number', 1)
    print(f"処理中: Unit {unit_num} ({json_filename})")

    cnt = {'S': 0, 'L': 0, 'I': 0, 'Q': 0}
    rows = []

    # --- データの構築 ---
    for section in data['sections']:
        cnt['S'] += 1
        sec_id = get_virtual_date_id(unit_num, 'S', cnt['S'])

        for lesson in section['lessons']:
            cnt['L'] += 1
            les_id = get_virtual_date_id(unit_num, 'L', cnt['L'])

            for page in lesson['pages']:
                cnt['I'] += 1
                input_id = get_virtual_date_id(unit_num, 'I', cnt['I'])

                # 行データの初期化
                row = {}

                # 1. Section Info
                row['section_code'] = sec_id
                row['section_name'] = section['title']
                row['section_status'] = section.get('status', 'public')
                row['section_published_at'] = ''

                # 2. Lesson Info
                row['lesson_code'] = les_id
                row['lesson_pattern'] = ''
                row['lesson_name'] = lesson['title']
                row['lesson_teaser'] = ''
                row['lesson_tags'] = ''
                row['lesson_status'] = lesson.get('status', 'public')
                row['lesson_published_at'] = ''

                # 3. Input Info
                row['input_code'] = input_id
                row['input_page_no'] = page['page_no']
                row['input_type'] = page.get('type', 'input_quiz')
                row['input_body_text'] = page['input'].get('body', '')
                row['input_image_url'] = ''
                row['input_supplement_text'] = page['input'].get('supplement', '')

                # 4. Input Quiz Info
                row['input_question_text'] = page['input'].get('question_text', '')
                row['input_question_image_url'] = ''
                row['input_question_type'] = '2_choice' if row['input_question_text'] else ''
                opts = page['input'].get('options', [])
                row['input_question_choices'] = ';'.join(opts) if isinstance(opts, list) else opts
                row['input_question_correct'] = page['input'].get('correct_option', '')
                row['input_correct_explanation'] = page['input'].get('result_comment', '')
                row['input_wrong_explanation'] = ''

                # 5. Quiz Info
                quiz_data = page.get('quiz')
                if quiz_data:
                    cnt['Q'] += 1
                    quiz_id = get_virtual_date_id(unit_num, 'Q', cnt['Q'])

                    row['quiz_code'] = quiz_id
                    row['quiz_page_no'] = ''
                    row['quiz_type'] = quiz_data.get('type', '4_choice')
                    row['quiz_question_text'] = quiz_data.get('question', '')
                    row['quiz_image_url'] = ''
                    q_opts = quiz_data.get('options', [])
                    row['quiz_choices'] = ';'.join(q_opts) if isinstance(q_opts, list) else q_opts
                    row['quiz_correct'] = quiz_data.get('correct_value', '')
                    row['quiz_pair_1'] = ''
                    row['quiz_pair_2'] = ''
                    row['quiz_pair_3'] = ''
                    row['quiz_pair_4'] = ''
                    row['quiz_correct_explanation'] = quiz_data.get('explanation', '')
                    row['quiz_wrong_explanation'] = ''
                    row['quiz_result_explanation'] = ''
                else:
                    for k in ['quiz_code', 'quiz_page_no', 'quiz_type', 'quiz_question_text',
                              'quiz_image_url', 'quiz_choices', 'quiz_correct', 'quiz_pair_1',
                              'quiz_pair_2', 'quiz_pair_3', 'quiz_pair_4', 'quiz_correct_explanation',
                              'quiz_wrong_explanation', 'quiz_result_explanation']:
                        row[k] = ''

                rows.append(row)

    # --- CSV出力 ---
    # 全38列の定義
    column_order = [
        'section_code', 'section_name', 'section_status', 'section_published_at',
        'lesson_code', 'lesson_pattern', 'lesson_name', 'lesson_teaser', 'lesson_tags', 'lesson_status', 'lesson_published_at',
        'input_code', 'input_page_no', 'input_type', 'input_body_text', 'input_image_url', 'input_supplement_text',
        'input_question_text', 'input_question_image_url', 'input_question_type', 'input_question_choices', 'input_question_correct', 'input_correct_explanation', 'input_wrong_explanation',
        'quiz_code', 'quiz_page_no', 'quiz_type', 'quiz_question_text', 'quiz_image_url', 'quiz_choices', 'quiz_correct',
        'quiz_pair_1', 'quiz_pair_2', 'quiz_pair_3', 'quiz_pair_4',
        'quiz_correct_explanation', 'quiz_wrong_explanation', 'quiz_result_explanation'
    ]

    df = pd.DataFrame(rows)
    for col in column_order:
        if col not in df.columns:
            df[col] = ''

    df_sorted = df[column_order]

    # 出力パス調整
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    output_filename = f"unit{str(unit_num).zfill(2)}.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)

    # テンプレート使用
    template_path = TEMPLATE_FILE
    if not os.path.exists(template_path):
         template_path = os.path.join('templates', 'header_template.csv')

    if os.path.exists(template_path):
        shutil.copy(template_path, output_path)
        df_sorted.to_csv(output_path, mode='a', index=False, header=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    else:
        print("警告: テンプレートが見つかりません。ヘッダー行のみで出力します。")
        df_sorted.to_csv(output_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)

    print(f"✅ 変換完了: {output_filename}")

if __name__ == "__main__":
    # drafts_json フォルダ内の全ファイルを対象にする
    # パスが見つからない場合はカレントディレクトリ基準も試す
    search_dir = INPUT_DIR
    if not os.path.exists(search_dir):
        search_dir = os.path.join('data', 'drafts_json')

    if os.path.exists(search_dir):
        target_files = [f for f in os.listdir(search_dir) if f.endswith('.json')]
        if not target_files:
            print(f"{search_dir} にJSONファイルがありません。")
        for json_file in target_files:
            generate_csv_final(json_file)
    else:
        print(f"ディレクトリが見つかりません: {INPUT_DIR} または data/drafts_json")
