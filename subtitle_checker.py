# subtitle_checker.py (ver.6 表示文言の改善版)

import sys
import re
from datetime import datetime, timedelta

# --- デフォルトの設定値 ---
DEFAULT_MAX_CHARS_PER_LINE = 25
DEFAULT_MAX_LINES = 2
DEFAULT_MIN_DURATION_MS = 100
DEFAULT_MAX_CPS = 20

def parse_time(time_str, format_type):
    """タイムスタンプ文字列をtimedeltaオブジェクトに変換する"""
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
    """分かりやすいエラーメッセージを生成する関数"""
    text_preview = f"「{text_lines[0][:30]}...」" if text_lines else "（テキストなし）"
    error_report = (
        f"[行: {start_line} / ブロック: {block_num}] {error_type}: {message}\n"
        f"  -> タイムスタンプ: {timestamp_line}\n"
        f"  -> テキスト: {text_preview}"
    )
    return error_report

def check_subtitle_file(filepath, max_chars, max_lines, min_duration, max_cps, check_content_layout, check_cps_speed):
    """字幕ファイルのチェックを実行するメイン関数"""
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
    except Exception as e:
        return f"ファイルを開けませんでした: {e}"

    # 行番号を維持したままブロックに分割
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

    # 形式判定
    format_type = None
    if blocks:
        first_block_lines = blocks[0]['lines']
        if len(first_block_lines) > 1 and '-->' in first_block_lines[1]:
            format_type = 'srt'
        elif ',' in first_block_lines[0]:
            format_type = 'sbv'
    if not format_type:
        return "字幕ファイルの形式を認識できませんでした (SRTまたはSBV形式)。"

    last_end_time = timedelta(0)

    for i, block_data in enumerate(blocks):
        block_num = i + 1
        start_line = block_data["start_line"]
        lines = block_data["lines"]
        
        # パース処理
        if format_type == 'srt':
            if not lines[0].isdigit():
                errors.append({'category': '書式エラー', 'details': format_error(start_line, block_num, "書式エラー", "SRTの1行目は連番である必要があります。", "(不明)", lines)})
                continue
            if len(lines) < 2:
                errors.append({'category': '書式エラー', 'details': format_error(start_line, block_num, "書式エラー", "タイムスタンプ行またはテキストがありません。", "(不明)", lines)})
                continue
            timestamp_line = lines[1]
            text_lines = lines[2:]
            time_parts = timestamp_line.split('-->')
        else: # sbv
            timestamp_line = lines[0]
            text_lines = lines[1:]
            time_parts = timestamp_line.split(',')
        
        start_time_str, end_time_str = (time_parts[0], time_parts[1]) if len(time_parts) > 1 else ("", "")
        start_time = parse_time(start_time_str, format_type)
        end_time = parse_time(end_time_str, format_type)

        # 必須エラーのチェック
        if start_time is None or end_time is None:
            errors.append({'category': '書式エラー', 'details': format_error(start_line, block_num, "書式エラー", "タイムスタンプのフォーマットが不正です。", timestamp_line, text_lines)})
            continue
        if start_time >= end_time:
            errors.append({'category': '時間エラー', 'details': format_error(start_line, block_num, "時間エラー", "終了時間が開始時間と同じか、それより早いです。", timestamp_line, text_lines)})
        duration = end_time - start_time
        if duration.total_seconds() * 1000 < min_duration:
            errors.append({'category': '時間エラー', 'details': format_error(start_line, block_num, "時間エラー", f"表示時間が短すぎます ({duration.total_seconds():.3f}秒)。", timestamp_line, text_lines)})
        if start_time < last_end_time:
            errors.append({'category': '時間エラー', 'details': format_error(start_line, block_num, "時間エラー", "前の字幕と表示時間が重複しています。", timestamp_line, text_lines)})
        if not text_lines:
            errors.append({'category': '書式エラー', 'details': format_error(start_line, block_num, "書式エラー", "字幕テキストがありません。", timestamp_line, text_lines)})
            continue

        # 任意エラーのチェック
        if check_content_layout:
            if len(text_lines) > max_lines:
                errors.append({'category': '内容エラー', 'details': format_error(start_line, block_num, "内容エラー", f"字幕の行数が多すぎます ({len(text_lines)}行)。", timestamp_line, text_lines)})
            for line_text in text_lines:
                char_count = sum(2 if len(char.encode('utf-8')) > 1 else 1 for char in line_text)
                if char_count > max_chars * 2:
                     errors.append({'category': '内容エラー', 'details': format_error(start_line, block_num, "内容エラー", f"1行の文字数が上限({max_chars}文字)を超えています。「{line_text[:15]}...」", timestamp_line, text_lines)})

        if check_cps_speed:
            total_chars = sum(len(line) for line in text_lines)
            if duration.total_seconds() > 0:
                cps = total_chars / duration.total_seconds()
                if cps > max_cps:
                    errors.append({'category': '内容エラー', 'details': format_error(start_line, block_num, "内容エラー", f"CPSが高すぎます (読むのが速すぎます)。計算値: {cps:.1f}", timestamp_line, text_lines)})

        last_end_time = end_time
    
    return errors

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"--- 字幕ファイルチェックツール (ver.6 表示文言の改善版) ---")
        print(f"ファイル: {filepath}\n")

        # ユーザーにチェック項目を選択してもらう
        user_input_chars = input(f"1行の文字数上限(全角)を入力してください (デフォルト: {DEFAULT_MAX_CHARS_PER_LINE}, 変更しない場合はEnter): ")
        try:
            max_chars = int(user_input_chars) if user_input_chars else DEFAULT_MAX_CHARS_PER_LINE
        except ValueError:
            max_chars = DEFAULT_MAX_CHARS_PER_LINE
            print(f"-> 不正な入力のため、デフォルト値「{max_chars}文字」を使用します。")

        user_input_layout = input(f"内容エラー(文字数/行数)をチェックしますか？ (Y/N, デフォルト: Y): ").upper()
        check_content_layout = False if user_input_layout == 'N' else True
        
        # ★質問文を修正
        user_input_cps = input(f"字幕が速すぎて読めない可能性をチェックしますか？ (Y/N, デフォルト: Y): ").upper()
        check_cps_speed = False if user_input_cps == 'N' else True
        
        print("\n--- チェック設定 ---")
        print(f"1行の文字数上限: {max_chars} 文字")
        print(f"文字数/行数チェック: {'ON' if check_content_layout else 'OFF'}")
        print(f"読む速さチェック: {'ON' if check_cps_speed else 'OFF'}") # 表示も分かりやすく変更
        print("--------------------\n")

        results = check_subtitle_file(filepath, max_chars, DEFAULT_MAX_LINES, DEFAULT_MIN_DURATION_MS, DEFAULT_MAX_CPS, check_content_layout, check_cps_speed)

        # 結果表示
        if isinstance(results, str):
            print(results)
        elif not results:
            print("✅ チェック完了: エラーは見つかりませんでした。")
        else:
            summary = {}
            for error in results:
                cat = error['category']
                summary[cat] = summary.get(cat, 0) + 1
            
            print(f"⚠️ チェック完了: 合計 {len(results)}件のエラーが見つかりました。")
            print("\n--- チェック結果サマリー ---")
            for category, count in sorted(summary.items()):
                print(f"- {category}: {count}件")
            print("--------------------------")

            for category in ['書式エラー', '時間エラー', '内容エラー']:
                errors_in_category = [e for e in results if e['category'] == category]
                if errors_in_category:
                    print(f"\n--- {category} ({len(errors_in_category)}件) ---")
                    for error in errors_in_category:
                        print(error['details'])

    else:
        print("使用方法: チェックしたい字幕ファイルをこのプログラムのアイコンにドラッグ＆ドロップしてください。")
    
    print("\n----------------------------------")
    input("何かキーを押すと終了します...")