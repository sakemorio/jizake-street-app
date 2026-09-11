# 地酒ストリート2026 公式アプリ（開発版）

清水駅前銀座商店街「地酒ストリート2026」（2026年9月13日開催）向けの来場者用PWA。
ビルド不要の素のHTML/CSS/JSで構成。GitHub Pagesなど静的ホスティングでそのまま公開できる。

## 構成

```
index.html         アプリ本体（タブ切り替えのシングルページ）
css/style.css       スタイル
js/app.js           データ読み込み・タブ切り替え・酒帳ロジック
data/breweries.json 出展蔵元・銘柄（公式サイトより転記、booth番号は会場図入手後に追記）
data/food.json      出展飲食店
data/info.json      開催概要・ルール・タイムテーブル
assets/venue-map.jpg              当日配布MAPの画像（圧縮済み、マップタブに表示・タップで拡大）
assets/venue-map-original.jpg     圧縮前の元画像（地図更新時の差し替え用。.png でも可）
manifest.json       PWA設定
sw.js               Service Worker（オフラインキャッシュ）
icons/              PWAアイコン（プレースホルダー、差し替え可）
scripts/gen_icons.py アイコン生成スクリプト（Python + Pillow）
scripts/compress_map.py 会場マップ画像の圧縮スクリプト（Python + Pillow）
scripts/gen_qr.py   告知用QRコード画像の生成スクリプト（Python + qrcode + Pillow、assets/qr-card.png を出力）
```

## 告知用QRコードを作る

`assets/qr-card.png` は、アプリのURLへのQRコード＋オリジナルキャラクター入りの配布用カード画像。

```bash
python -m pip install qrcode pillow
python scripts/gen_qr.py
```

誤り訂正レベルH（最大約30%まで破損・被覆に耐えられる）で生成しており、中央のロゴ被覆はQR面積の1割未満に抑えているため、印刷して問題なく読み取れる。生成後は以下でスキャン確認できる（要 `opencv-python-headless`）。

```bash
python -c "import cv2; img=cv2.imread('assets/qr-card.png'); print(cv2.QRCodeDetector().detectAndDecode(img)[0])"
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

## 当日の「完売」「お知らせ」をスマホからリアルタイム更新する（Google Apps Script）

会場スタッフが**PC不要・スマホのGoogleスプレッドシートアプリだけ**で「完売」表示とお知らせバーを更新できる仕組み。
来場者側のアプリは1分ごとに自動で最新状態を取得する（`LIVE_POLL_MS`で変更可）。

1. Googleスプレッドシートを新規作成（例：「地酒ストリート2026 ライブ状況」）
2. シート名を1つ目「完売」、2つ目「お知らせ」に変更し、それぞれ1行目に見出しを入れる
   - 「完売」シート：A列＝`番号`、B列＝`完売`、C列＝`残りわずか`（B・Cともチェックボックスにすると現場で扱いやすい：範囲を選択→メニュー「挿入」→「チェックボックス」）。両方チェックした場合は「完売」が優先表示される
   - 「お知らせ」シート：A列＝`内容`（表示したい文章）、B列＝`表示`（チェックボックス）。**A列に文章、B列にチェック**という並びを間違えないこと。複数行書いてもよいが、実際にバーに出るのは「表示」がONの一番上の行だけ
3. メニュー「拡張機能」→「Apps Script」を開き、以下を貼り付けて保存

   ```javascript
   function doGet(e) {
     const ss = SpreadsheetApp.getActiveSpreadsheet();
     const soldSheet = ss.getSheetByName("完売");
     const noticeSheet = ss.getSheetByName("お知らせ");

     const soldRows = soldSheet.getDataRange().getValues().slice(1);
     const soldOut = soldRows
       .filter(row => row[1] === true)
       .map(row => Number(row[0]))
       .filter(n => !isNaN(n));
     const lowStock = soldRows
       .filter(row => row[2] === true)
       .map(row => Number(row[0]))
       .filter(n => !isNaN(n));

     const noticeRows = noticeSheet.getDataRange().getValues().slice(1);
     const activeNotice = noticeRows.find(row => row[1] === true && row[0]);
     const notice = activeNotice ? String(activeNotice[0]) : "";

     return ContentService.createTextOutput(JSON.stringify({ soldOut, lowStock, notice }))
       .setMimeType(ContentService.MimeType.JSON);
   }
   ```

   ※ すでにデプロイ済みで、コードだけ書き換える場合は「デプロイ」→「デプロイを管理」→ 鉛筆（編集）アイコン→ バージョンを「新バージョン」にして「デプロイ」を押さないと、コードの変更が反映されない。

4. 「デプロイ」→「新しいデプロイ」→ 種類「ウェブアプリ」
   - 実行するユーザー：自分
   - アクセスできるユーザー：全員
5. 発行されたウェブアプリのURLを `js/app.js` 冒頭の `LIVE_ENDPOINT` に設定し、再デプロイ（GitHub Pagesの場合は再push）
6. 当日はスマホでこのスプレッドシートを開き（Googleスプレッドシートアプリ、または共有リンクをホーム画面に追加）、完売したブース番号にチェック／お知らせを書いてチェックを入れるだけでよい。来場者のアプリには最大1分以内に反映される

※ 編集させたいスタッフには、スプレッドシートを「編集者」権限で共有しておくこと（Googleアカウントが必要）。

## 現状のスコープ・今後の課題

- **会場マップ**：当日配布MAPの画像（`assets/venue-map.jpg`）をマップタブ上部に表示、タップで拡大（ピンチズーム対応）。あわせて蔵元62件すべてにブース番号・エリア（A/B/C）を反映し、「エリア帯をタップ→蔵元一覧をそのエリアで絞り込み」も利用できる。地図が更新された場合は `assets/venue-map-original.jpg`（または`.png`）を新しい画像で上書きし、`python scripts/compress_map.py` を再実行すればよい（PNG量子化とJPEG圧縮の両方を試し、小さい方を自動選択する）。
- **蔵元データ**：公式サイト記載（2026年8月）＋当日配布MAP（ブース番号）の組み合わせ。当日変更があれば `data/breweries.json` を直接編集して再デプロイ。
- **フードデータ**：配布MAPにのみ記載の「Moi Moon」を追加、昼営業店舗・商店街店舗にマップ記号（A〜N）を反映済み。
- **アイコン**：`scripts/gen_icons.py` によるプレースホルダー。本番前に正式なロゴへの差し替えを推奨。
