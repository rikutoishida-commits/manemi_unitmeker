import json
import pandas as pd
import os
import shutil

# --- 設定 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # src/converters/
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR)) # root/

INPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'drafts_json')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output_csv')
TEMPLATE_FILE = os.path.join(PROJECT_ROOT, 'templates', 'header_template.csv')

def get_virtual_date_id(unit_num, prefix, counter):
    """
    Unit番号に基づいて仮想日付を生成し、IDを作成する
    Unit 1 -> 250101 (25年1月1日)
    Unit 12 -> 250112 (25年1月12日)
    """
    # 仮想日付の生成: 2501 + Unit番号(2桁)
    virtual_date = f"2501{str(unit_num).zfill(2)}"
    # ID生成: Prefix + Date + 連番(4桁)
    return f"{prefix}{virtual_date}{str(counter).zfill(4)}"

def generate_csv_final(json_filename):
    # 1. JSON読み込み
    json_path = os.path.join(INPUT_DIR, json_filename)
    if not os.path.exists(json_path):
        print(f"エラー: {json_path} が見つかりません。")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    unit_num = data.get('unit_number', 1) # JSONに番号がない場合は1とする
    print(f"処理中: Unit {unit_num} ({json_filename})")

    # IDカウンターのリセット
    cnt = {'S': 0, 'L': 0, 'I': 0, 'Q': 0}
    
    rows = []
    
    # 2. データ構築ループ
    for section in data['sections']:
        cnt['S'] += 1
        sec_id = get_virtual_date_id(unit_num, 'S', cnt['S'])
        
        for lesson in section['lessons']:
            cnt['L'] += 1
            les_id = get_virtual_date_id(unit_num, 'L', cnt['L'])
            
            for page in lesson['pages']:
                # Input ID
                cnt['I'] += 1
                input_id = get_virtual_date_id(unit_num, 'I', cnt['I'])
                
                # 行データ作成
                row = {
                    # 見本CSVのカラム順序や名前に依存せず、まずは辞書を作る
                    # 実際の出力時にテンプレートの並びに合わせる
                    'section_code': sec_id,
                    'section_name': section['title'],
                    'section_status': section.get('status', 'public'),
                    
                    'lesson_code': les_id,
                    'lesson_name': lesson['title'],
                    'lesson_status': lesson.get('status', 'public'),
                    
                    'input_code': input_id,
                    'input_page_no': page['page_no'],
                    'input_type': page.get('type', 'normal'),
                    'input_body': page['input'].get('body', ''),
                    'input_supplement': page['input'].get('supplement', ''),
                    
                    'input_question': page['input'].get('question_text', ''),
                    'input_options': ';'.join(page['input'].get('options', [])),
                    'input_correct': page['input'].get('correct_option', ''),
                    'input_comment': page['input'].get('result_comment', ''),
                }
                
                # Quiz処理
                quiz_data = page.get('quiz')
                if quiz_data:
                    cnt['Q'] += 1
                    quiz_id = get_virtual_date_id(unit_num, 'Q', cnt['Q'])
                    
                    row['quiz_code'] = quiz_id
                    row['quiz_type'] = quiz_data.get('type', '4_choice')
                    row['quiz_question'] = quiz_data.get('question', '')
                    row['quiz_options'] = ';'.join(quiz_data.get('options', []))
                    row['quiz_correct'] = quiz_data.get('correct_value', '')
                    row['quiz_explanation'] = quiz_data.get('explanation', '')
                else:
                    # 空白埋め
                    row['quiz_code'] = ''
                    row['quiz_type'] = ''
                    row['quiz_question'] = ''
                    row['quiz_options'] = ''
                    row['quiz_correct'] = ''
                    row['quiz_explanation'] = ''

                rows.append(row)

    # 3. CSV出力処理（テンプレート活用）
    
    # 出力ファイルパス
    output_filename = f"unit{str(unit_num).zfill(2)}.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # 手順A: テンプレートをコピーして出力ファイルを作成（これでヘッダー1-2行目は完璧）
    if not os.path.exists(TEMPLATE_FILE):
        print("エラー: テンプレートファイルが見つかりません。templates/header_template.csv を配置してください。")
        return
        
    shutil.copy(TEMPLATE_FILE, output_path)
    
    # 手順B: テンプレートから「カラム名」を取得する（3行目の列マッピングのため）
    # ヘッダーが2行あるので、pandasで読むときは工夫が必要だが、
    # ここでは「見本CSV」のカラム順序が固定であると仮定し、コード内で定義したリスト順で書き込むのが安全。
    
    # ※重要: ここのリストは、実際のheader_template.csvの並び順と完全に一致させる必要があります！
    # CSV見本ファイルを開いて、A列から順に確認してください。
    column_order = [
        'section_code', 'section_name', 'section_status', # A, B, C
        'lesson_code', 'lesson_name', 'lesson_status',    # D, E, F
        'input_code', 'input_page_no', 'input_type',      # G, H, I
        'input_body', 'input_supplement',                 # J, K
        'input_question', 'input_options', 'input_correct', 'input_comment', # L, M, N, O
        'quiz_code', 'quiz_type', 'quiz_question', 'quiz_options', 'quiz_correct', 'quiz_explanation' # P~
    ]
    
    df = pd.DataFrame(rows)
    
    # 存在しない列を補完
    for col in column_order:
        if col not in df.columns:
            df[col] = ''
            
    # 並び順をテンプレートに合わせる
    df_sorted = df[column_order]
    
    # 手順C: 追記モード('a')で書き込み。ヘッダーは書かない(header=False)
    df_sorted.to_csv(output_path, mode='a', index=False, header=False, encoding='utf-8-sig')
    
    print(f"✅ 変換完了: {output_filename} (ID日付: 2501{str(unit_num).zfill(2)})")

if __name__ == "__main__":
    # 実行例: unit01.json が drafts_json フォルダにある場合
    # 全ファイルを変換したい場合は os.listdir でループさせると良い
    
    target_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.json')]
    
    if not target_files:
        print("変換対象のJSONファイルが data/drafts_json/ にありません。")
    else:
        for json_file in target_files:
            generate_csv_final(json_file)