# 地酒ストリート2026 公式アプリ（開発版）

清水駅前銀座商店街「地酒ストリート2026」（2026年9月13日開催）向けの来場者用PWA。
ビルド不要の素のHTML/CSS/JSで構成。GitHub Pagesなど静的ホスティングでそのまま公開できる。

## 構成

```
index.html         アプリ本体（タブ切り替えのシングルページ）
css/style.css       スタイル
js/app.js           データ読み込み・タブ切り替え・酒帳・アンケート送信ロジック
data/breweries.json 出展蔵元・銘柄（公式サイトより転記、booth番号は会場図入手後に追記）
data/food.json      出展飲食店
data/info.json      開催概要・ルール・タイムテーブル
assets/venue-map.png          当日配布MAPの画像（圧縮済み、マップタブに表示・タップで拡大）
assets/venue-map-original.png 圧縮前の元画像（地図更新時の差し替え用）
manifest.json       PWA設定
sw.js               Service Worker（オフラインキャッシュ）
icons/              PWAアイコン（プレースホルダー、差し替え可）
scripts/gen_icons.py アイコン生成スクリプト（Python + Pillow）
scripts/compress_map.py 会場マップ画像の圧縮スクリプト（Python + Pillow）
```

## ローカルで確認する

`fetch()` でJSONを読み込むため、`file://` で直接開くとCORSエラーになる。簡易サーバーを立てて確認する。

```bash
cd jizake-street-app
python -m http.server 8080
```

ブラウザで `http://localhost:8080` を開く。

## GitHub Pagesへの公開

1. このフォルダをGitHubリポジトリにする（`git init` → push）
2. リポジトリの Settings → Pages → Branch を `main` / `/(root)` に設定
3. 数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` で公開される
4. スマホでアクセスし「ホーム画面に追加」でPWAとしてインストール可能

## アンケートの送信先を設定する（Google Apps Script）

現状は `js/app.js` の `SURVEY_ENDPOINT` が空のため、回答は各端末のブラウザに保存されるだけ（開発確認用）。
本番では以下の手順でGoogleスプレッドシートに集約できる。

1. Googleスプレッドシートを新規作成（例：「地酒ストリート2026 アンケート」）
2. メニュー「拡張機能」→「Apps Script」を開く
3. 以下のコードを貼り付けて保存

   ```javascript
   // セルの先頭が =+-@ などだとGoogleスプレッドシートに数式として解釈されてしまう
   // （スプレッドシート版CSVインジェクション）ため、自由記述欄はそのまま書き込まず無害化する。
   function sanitizeCell(value) {
     const s = String(value == null ? "" : value);
     return /^[=+\-@\t\r]/.test(s) ? "'" + s : s;
   }

   function doPost(e) {
     const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
     const data = JSON.parse(e.postData.contents);
     sheet.appendRow([
       new Date(),
       sanitizeCell(data.satisfaction),
       sanitizeCell(data.session),
       sanitizeCell(data.visits),
       sanitizeCell(data.good),
       sanitizeCell(data.improve)
     ]);
     return ContentService.createTextOutput(JSON.stringify({ result: "ok" }))
       .setMimeType(ContentService.MimeType.JSON);
   }
   ```

4. 「デプロイ」→「新しいデプロイ」→ 種類「ウェブアプリ」
   - 実行するユーザー：自分
   - アクセスできるユーザー：全員
5. 発行されたウェブアプリのURLを `js/app.js` 冒頭の `SURVEY_ENDPOINT` に設定する
6. 再デプロイ（GitHub Pagesの場合は再push）

※ `fetch` は `mode: "no-cors"` で送信しているため、送信の成否はレスポンス内容では判定できない（Apps Script側のCORS制約による標準的な回避策）。アプリ側は送信リクエストが例外なく完了した時点で成功として扱う。

## 当日の「完売」「お知らせ」をスマホからリアルタイム更新する（Google Apps Script）

会場スタッフが**PC不要・スマホのGoogleスプレッドシートアプリだけ**で「完売」表示とお知らせバーを更新できる仕組み。
来場者側のアプリは1分ごとに自動で最新状態を取得する（`LIVE_POLL_MS`で変更可）。

1. Googleスプレッドシートを新規作成（例：「地酒ストリート2026 ライブ状況」）
2. シート名を1つ目「完売」、2つ目「お知らせ」に変更し、それぞれ1行目に見出しを入れる
   - 「完売」シート：A列＝`番号`、B列＝`完売`（チェックボックスにすると現場で扱いやすい：範囲を選択→メニュー「挿入」→「チェックボックス」）
   - 「お知らせ」シート：A列＝`内容`、B列＝`表示`（同じくチェックボックス推奨）。複数行書いてもよいが、実際にバーに出るのは「表示」がONの最初の1件だけ
3. メニュー「拡張機能」→「Apps Script」を開き、以下を貼り付けて保存

   ```javascript
   function doGet(e) {
     const ss = SpreadsheetApp.getActiveSpreadsheet();
     const soldSheet = ss.getSheetByName("完売");
     const noticeSheet = ss.getSheetByName("お知らせ");

     const soldOut = soldSheet.getDataRange().getValues()
       .slice(1)
       .filter(row => row[1] === true)
       .map(row => Number(row[0]))
       .filter(n => !isNaN(n));

     const noticeRows = noticeSheet.getDataRange().getValues().slice(1);
     const activeNotice = noticeRows.find(row => row[1] === true && row[0]);
     const notice = activeNotice ? String(activeNotice[0]) : "";

     return ContentService.createTextOutput(JSON.stringify({ soldOut, notice }))
       .setMimeType(ContentService.MimeType.JSON);
   }
   ```

4. 「デプロイ」→「新しいデプロイ」→ 種類「ウェブアプリ」
   - 実行するユーザー：自分
   - アクセスできるユーザー：全員
5. 発行されたウェブアプリのURLを `js/app.js` 冒頭の `LIVE_ENDPOINT` に設定し、再デプロイ（GitHub Pagesの場合は再push）
6. 当日はスマホでこのスプレッドシートを開き（Googleスプレッドシートアプリ、または共有リンクをホーム画面に追加）、完売したブース番号にチェック／お知らせを書いてチェックを入れるだけでよい。来場者のアプリには最大1分以内に反映される

※ 編集させたいスタッフには、スプレッドシートを「編集者」権限で共有しておくこと（Googleアカウントが必要）。

## 現状のスコープ・今後の課題

- **会場マップ**：当日配布MAPの画像（`assets/venue-map.png`）をマップタブ上部に表示、タップで拡大（ピンチズーム対応）。あわせて蔵元62件すべてにブース番号・エリア（A/B/C）を反映し、「エリア帯をタップ→蔵元一覧をそのエリアで絞り込み」も利用できる。画像は2.05MB→616KBに圧縮済み（`scripts/compress_map.py`、幅1600pxにリサイズ＋PNG256色量子化）。元画像は `assets/venue-map-original.png` に保存してあるので、地図が更新された場合はそちらを差し替えて同スクリプトを再実行すればよい。
- **蔵元データ**：公式サイト記載（2026年8月）＋当日配布MAP（ブース番号）の組み合わせ。当日変更があれば `data/breweries.json` を直接編集して再デプロイ。
- **フードデータ**：配布MAPにのみ記載の「Moi Moon」を追加、昼営業店舗・商店街店舗にマップ記号（A〜N）を反映済み。
- **アイコン**：`scripts/gen_icons.py` によるプレースホルダー。本番前に正式なロゴへの差し替えを推奨。
