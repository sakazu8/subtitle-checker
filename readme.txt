概要
このツールは、字幕ファイル（.srt、.sbv）の品質をチェックし、エラーを検出するためのものです。
書式エラーだけでなく、時間的な矛盾や、視聴者にとっての読みやすさもチェックします。

主なチェック項目

書式エラー: タイムスタンプの形式、連番の有無など、ファイルが壊れていないか。
時間エラー: 時間の重複、表示時間が短すぎるなど、再生時に問題が起きないか。
内容・品質エラー: 1行の文字数、行数、読む速さ（CPS）が適切か。（これらのチェックは実行時にON/OFFを選択可能）
※現状、.vtt形式には対応していません。

使い方（ツール利用者向け）
配布された subtitle_checker.exe のアイコンに、チェックしたい字幕ファイル（.srtまたは.sbv）をドラッグ＆ドロップします。
黒い画面（コンソール）が起動し、いくつか質問が表示されます。
1行の文字数上限: チェック基準となる文字数を半角数字で入力します。（何も入力せずEnterを押すとデフォルト値が適用されます）
内容エラーのチェック有無: 文字数や行数、CPSのチェックを行うか Y / N で選択します。
設定が完了すると、チェックが実行され、結果が画面に表示されます。
開発者向け情報
環境構築（初回のみ）
開発には以下のツールが必要です。

Python (Anaconda)
Git
auto-py-to-exe: 以下のコマンドでインストールします。
Bash

pip install auto-py-to-exe
開発フロー
ソースコードの編集:
subtitle_checker.py を編集して、機能の追加や修正を行います。

バージョン管理 (Git & GitHub):
キリの良いところで、変更履歴を「セーブポイント」として記録し、GitHubにバックアップします。

Bash

# 変更をすべて選択
git add .

# メモを付けてセーブポイントを作成
git commit -m "〇〇機能を修正"

# GitHubにアップロード
git push
ツール（.exe）の更新と配布
.exeファイルの作成:
コマンドプロンプトで auto-py-to-exe を起動し、GUI画面で以下の設定を行い、実行ファイルを作成します。

Script Location: subtitle_checker.py を選択
One File: 「One File」を選択
Console Window: 「Console Based」を選択
配布:
作成された subtitle_checker.exe を配布します。配布方法には2通りあります。

方法A（現在）: PC上にある.exeファイルを、メールやチャットなどで必要な人に直接渡す。
方法B（推奨）: GitHubの「Releases」機能を使って、バージョン情報と共に公開・配布する。


# 作業の流れの確認
git pull

git add

git commit -m ""

git push

【自宅】

PCにGitをインストールし、`git config`で名前とメールアドレスの初期設定を済ませておきます。2. コマンドプロンプト（ターミナル）を開き、プロジェクトを置きたいフォルダに移動します。 ```bash

# 例: ドキュメントフォルダに移動

cd C:\Users\YourName\Documents

```3. 以下のコマンドを実行して、GitHubからプロジェクト全体を自分のPCにコピー（クローン）します。 ```bash

git clone [https://github.com/sakazu8/subtitle-checker.git](https://github.com/sakazu8/subtitle-checker.git)

```

これにより、`subtitle-checker`というフォルダが作成され、開発を開始できます。

以下同じ

git pull

git add

git commit -m ""

git push