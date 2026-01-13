# Project Context
「マネミー」アプリ向けの投資学習コンテンツを作成するプロジェクトです。
ユーザーから提供される構成案に基づき、**厳格な文字数制限**を守ってJSONデータを作成してください。

# Tone & Manner
- **ターゲット**: 投資超初心者。
- **文体**: 親しみやすい「〜です/〜ます/〜だよ」調。
- **禁止事項**: 専門用語の羅列、上から目線の断定。

# Validation Rules (Strict!)
以下の制限を**絶対に**守ってください。オーバーするとエラーになります。
- **レッスンタイトル**: 全角15文字以内
- **インプット説明文**: 全角80文字以内 (Markdown記号除く)
- **クイズ問題文**: 全角40文字以内
- **クイズ選択肢**: 全角30文字以内
- **クイズ解説**: 全角150文字以内

# Output Format (JSON)
スクリプトでCSVに変換するため、以下のJSON形式で出力してください。

```json
{
  "unit_number": 1,
  "unit_title": "はじめの一歩", // 20文字以内
  "sections": [
    {
      "title": "投資とあなた", // 15文字以内
      "status": "public",      // public または draft
      "lessons": [
        {
          "title": "株を持つ意味", // 15文字以内
          "status": "public",
          "goal": "株は会社の一部を持つことだと理解する", // 内部メモ用
          "pages": [
            {
              "page_no": 1,
              "type": "input_quiz", // input_quiz または challenge
              "input": {
                "body": "株を買うということは、その会社のオーナーの一人になるということです。\n会社が利益を出せば、あなたにも配当として還元されます。", // 80文字以内
                "supplement": "議決権も持てますよ", // 40文字以内
                "question_text": "株主が得られる利益は？", // 簡易質問 40文字以内
                "options": ["配当金", "給料"], // 30文字以内
                "correct_option": "配当金",
                "result_comment": "正解です！会社の利益の一部を受け取れます。" // 80文字以内
              },
              "quiz": {
                 // このページにクイズが無い場合はnull、ある場合は以下
                "question": "株主総会に参加できる？", // 40文字以内
                "type": "2_choice", // 2_choice (ox) または 4_choice
                "options": ["o", "x"], // マルバツは o, x で指定
                "correct_value": "o",
                "explanation": "株主には会社の経営に参加する権利があります。" // 150文字以内
              }
            }
          ]
        }
      ]
    }
  ]
}

### 2. 【ロジック】CSV変換スクリプト (`json_to_csv_v2.py`)

マニュアルの「ID命名規則（YYMMDD+連番）」と「カラム仕様」に完全対応したPythonコードです。

```python
import json
import pandas as pd
import datetime
import os

# --- 設定 ---
INPUT_DIR = '../../data/interm'
OUTPUT_DIR = '../../data/output'
TODAY_STR = datetime.date.today().strftime('%y%m%d') # YYMMDD形式

# ID生成カウンター（実行ごとにリセットされるため、本番運用ではDB管理等が望ましいが今回は簡易実装）
counters = {'S': 0, 'L': 0, 'I': 0, 'Q': 0}

def get_new_id(prefix):
    """マニュアル仕様のIDを生成する (例: S2501130001)"""
    counters[prefix] += 1
    return f"{prefix}{TODAY_STR}{str(counters[prefix]).zfill(4)}"

def generate_csv_v2(json_filename):
    json_path = os.path.join(INPUT_DIR, json_filename)
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    rows = []
    
    # Unit情報はCSV自体には含まれない（ファイル名や別管理）が、ここでは処理の起点とする
    
    # Section ループ
    for section in data['sections']:
        sec_id = get_new_id('S')
        
        # Lesson ループ
        for lesson in section['lessons']:
            les_id = get_new_id('L')
            
            # Page (Input/Quiz) ループ
            # マニュアルの「input_page_no」は同一レッスン内で一意
            for page in lesson['pages']:
                
                # --- 行データの構築 ---
                # マニュアルに従い、必要なカラムをマッピング
                row = {
                    # Section Info (3行目以降の最初の行に必須、以降は空でも可だが今回は埋める方針でもOK)
                    'section_code': sec_id,
                    'section_name': section['title'],
                    'section_status': section.get('status', 'public'),
                    
                    # Lesson Info
                    'lesson_code': les_id,
                    'lesson_name': lesson['title'],
                    'lesson_status': lesson.get('status', 'public'),
                    
                    # Input Info
                    'input_code': get_new_id('I'),
                    'input_page_no': page['page_no'],
                    'input_type': page.get('type', 'normal'), # normal, challenge, warmup等
                    'input_body': page['input'].get('body', ''),
                    'input_supplement': page['input'].get('supplement', ''),
                    
                    # 簡易質問 (Input内のクイズ)
                    'input_question': page['input'].get('question_text', ''),
                    # 選択肢はセミコロン区切り
                    'input_options': ';'.join(page['input'].get('options', [])), 
                    'input_correct': page['input'].get('correct_option', ''),
                    'input_comment': page['input'].get('result_comment', ''),
                    
                    # Quiz Info (このページにクイズがある場合)
                }
                
                quiz_data = page.get('quiz')
                if quiz_data:
                    row['quiz_code'] = get_new_id('Q')
                    row['quiz_type'] = quiz_data.get('type', '4_choice') # 2_choice, 4_choice
                    row['quiz_question'] = quiz_data.get('question', '')
                    
                    # 選択肢の処理
                    options = quiz_data.get('options', [])
                    row['quiz_options'] = ';'.join(options)
                    
                    # 正解の処理 (o/x または 選択肢の文字列)
                    row['quiz_correct'] = quiz_data.get('correct_value', '')
                    
                    row['quiz_explanation'] = quiz_data.get('explanation', '')
                else:
                    # クイズなしの場合
                    row['quiz_code'] = ''
                    row['quiz_type'] = ''
                    row['quiz_question'] = ''
                    row['quiz_options'] = ''
                    row['quiz_correct'] = ''
                    row['quiz_explanation'] = ''

                rows.append(row)

    # DataFrame作成
    df = pd.DataFrame(rows)
    
    # マニュアルのカラム定義（正確なヘッダー名が必要）
    # ※ここはCSV見本の1行目にある正確なカラム名に合わせて調整してください
    # 今回は一般的な英名で仮置きしています
    required_columns = [
        'section_code', 'section_name', 'section_status',
        'lesson_code', 'lesson_name', 'lesson_status',
        'input_code', 'input_page_no', 'input_type', 
        'input_body', 'input_supplement',
        'input_question', 'input_options', 'input_correct', 'input_comment',
        'quiz_code', 'quiz_type', 'quiz_question', 'quiz_options', 'quiz_correct', 'quiz_explanation'
    ]
    
    # 存在しない列を空文字で追加
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
            
    df = df[required_columns]

    # 出力
    unit_str = str(data['unit_number']).zfill(2)
    output_filename = f"unit{unit_str}_v2.csv"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # CSV書き出し (UTF-8)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"変換完了 (マニュアル準拠): {output_path}")

if __name__ == "__main__":
    generate_csv_v2('unit01.json')