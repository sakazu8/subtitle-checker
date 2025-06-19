# subtitle_checker.py (文字数上限を選択できる最終版)

import sys
import re
from datetime import datetime, timedelta

# --- デフォルトの設定値 ---
# ここにある設定値は、ユーザーが何も入力しなかった場合に適用される
DEFAULT_MAX_CHARS_PER_LINE = 25 # 1行あたりの最大文字数（全角換算）
DEFAULT_MAX_LINES = 2           # 1ブロックあたりの最大行数
DEFAULT_MIN_DURATION_MS = 100   # 最低表示時間（ミリ秒）
DEFAULT_MAX_CPS = 20            # 1秒あたりの最大文字数（読み上げ速度の目安）

def parse_time(time_str, format_type):
    time_str = time_str.strip()
    time_str_for_parse = time_str.replace(',', '.')
    try:
        if time_str_for_parse.count(':') == 2:
            dt_obj = datetime.strptime(time_str_for_parse, '%H:%M:%S.%f')
        elif time_str_for_parse.count(':') == 1:
            dt_obj = datetime.strptime(time_str_for_parse, '%M:%S.%f')
        else:
            raise ValueError("Invalid time format structure")
        return timedelta(hours=dt_obj.hour, minutes=dt_obj.minute, seconds=dt_obj.second, microseconds=dt_obj.microsecond)
    except ValueError:
        return None

def format_error(start_line, block_num, error_type, message, timestamp_line, text_lines):
    text_preview = f"「{text_lines[0][:30]}...」" if text_lines else "（テキストなし）"
    error_report = (
        f"[行: {start_line} / ブロック: {block_num}] {error_type}: {message}\n"
        f"  -> タイムスタンプ: {timestamp_line}\n"
        f"  -> テキスト: {text_preview}"
    )
    return error_report

# ★変更点1：チェック関数が設定値を受け取るように変更
def check_subtitle_file(filepath, max_chars, max_lines, min_duration, max_cps):
    """字幕ファイルのチェックを実行するメイン関数"""
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
    except Exception as e:
        print(f"ファイルを開けませんでした: {e}")
        return

    blocks = []
    current_block_lines = []
    block_start_line = 0
    for i, line in enumerate(all_lines):
        if line.strip():
            if not current_block_lines:
                block_start_line = i + 1
            current_block_lines.append(line.strip())
        else:
            if current_block_lines:
                blocks.append({"start_line": block_start_line, "lines": current_block_lines})
                current_block_lines = []
    if current_block_lines:
        blocks.append({"start_line": block_start_line, "lines": current_block_lines})

    format_type = None
    if blocks:
        first_block_lines = blocks[0]['lines']
        if len(first_block_lines) > 1 and '-->' in first_block_lines[1]:
            format_type = 'srt'
        elif ',' in first_block_lines[0]:
            format_type = 'sbv'
            
    if not format_type:
        print("字幕ファイルの形式を認識できませんでした (SRTまたはSBV形式である必要があります)。")
        return
    print(f"{format_type.upper()}形式のファイルとしてチェックを開始します。\n")

    last_end_time = timedelta(0)

    for i, block_data in enumerate(blocks):
        block_num = i + 1
        start_line = block_data["start_line"]
        lines = block_data["lines"]
        
        if format_type == 'srt':
            # (SRTのパース処理は変更なし)
            if not lines[0].isdigit():
                errors.append(format_error(start_line, block_num, "書式エラー", "SRTの1行目は連番である必要があります。", "(不明)", lines))
                continue
            if len(lines) < 2:
                errors.append(format_error(start_line, block_num, "書式エラー", "タイムスタンプ行またはテキストがありません。", "(不明)", lines))
                continue
            timestamp_line = lines[1]
            text_lines = lines[2:]
            time_parts = timestamp_line.split('-->')
        else: # sbv
            timestamp_line = lines[0]
            text_lines = lines[1:]
            time_parts = timestamp_line.split(',')
        
        start_time_str, end_time_str = time_parts[0], time_parts[1] if len(time_parts) > 1 else ""
        start_time = parse_time(start_time_str, format_type)
        end_time = parse_time(end_time_str, format_type)

        if start_time is None or end_time is None:
            errors.append(format_error(start_line, block_num, "書式エラー", "タイムスタンプのフォーマットが不正です。 (例: H:MM:SS.mmm)", timestamp_line, text_lines))
            continue
        
        if start_time >= end_time:
            errors.append(format_error(start_line, block_num, "時間エラー", "終了時間が開始時間と同じか、それより早いです。", timestamp_line, text_lines))
        
        duration = end_time - start_time
        if duration.total_seconds() * 1000 < min_duration:
            errors.append(format_error(start_line, block_num, "時間エラー", f"表示時間が短すぎます ({duration.total_seconds():.3f}秒)。", timestamp_line, text_lines))

        if start_time < last_end_time:
            errors.append(format_error(start_line, block_num, "時間エラー", "前の字幕と表示時間が重複しています。", timestamp_line, text_lines))

        if not text_lines:
            errors.append(format_error(start_line, block_num, "書式エラー", "字幕テキストがありません。", timestamp_line, text_lines))
        
        if len(text_lines) > max_lines:
            errors.append(format_error(start_line, block_num, "内容エラー", f"字幕の行数が多すぎます ({len(text_lines)}行)。", timestamp_line, text_lines))
        
        # ★変更点2：引数で渡された上限値でチェックする
        for line_text in text_lines:
            char_count = sum(2 if len(char.encode('utf-8')) > 1 else 1 for char in line_text)
            if char_count > max_chars * 2:
                 errors.append(format_error(start_line, block_num, "内容エラー", f"1行の文字数が上限({max_chars}文字)を超えています。「{line_text[:15]}...」", timestamp_line, text_lines))

        total_chars = sum(len(line) for line in text_lines)
        if duration.total_seconds() > 0:
            cps = total_chars / duration.total_seconds()
            if cps > max_cps:
                errors.append(format_error(start_line, block_num, "内容エラー", f"CPSが高すぎます (読むのが速すぎます)。計算値: {cps:.1f}", timestamp_line, text_lines))

        last_end_time = end_time

    if not errors:
        print("✅ チェック完了: エラーは見つかりませんでした。")
    else:
        print(f"⚠️ チェック完了: {len(errors)}件のエラーが見つかりました。")
        for error in errors:
            print("-" * 20)
            print(error)

# ★★★ここからが今回のメインの変更箇所★★★
if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"--- 字幕ファイルチェックツール (ver.3) ---")
        print(f"ファイル: {filepath}\n")

        # ユーザーに文字数上限を入力してもらう
        user_input_chars = input(f"1行の文字数上限(全角)を入力してください (デフォルト: {DEFAULT_MAX_CHARS_PER_LINE}文字, 変更しない場合はEnter): ")
        
        try:
            # 入力があればその数値を、なければデフォルト値を使う
            if user_input_chars:
                max_chars = int(user_input_chars)
                print(f"-> 上限を「{max_chars}文字」に設定しました。\n")
            else:
                max_chars = DEFAULT_MAX_CHARS_PER_LINE
                print(f"-> デフォルト値「{max_chars}文字」を使用します。\n")
        except ValueError:
            # 数字以外が入力されたらデフォルト値を使う
            max_chars = DEFAULT_MAX_CHARS_PER_LINE
            print(f"-> 不正な入力です。デフォルト値「{max_chars}文字」を使用します。\n")
        
        # 他の設定も同様に追加可能だが、今回は文字数のみ
        max_lines = DEFAULT_MAX_LINES
        min_duration = DEFAULT_MIN_DURATION_MS
        max_cps = DEFAULT_MAX_CPS

        # 設定した上限値を渡してチェックを実行
        check_subtitle_file(filepath, max_chars, max_lines, min_duration, max_cps)

    else:
        print("使用方法: チェックしたい字幕ファイルをこのプログラムのアイコンにドラッグ＆ドロップしてください。")
    
    print("\n----------------------------------")
    input("何かキーを押すと終了します...")