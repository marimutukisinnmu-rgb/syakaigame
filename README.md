# 超大規模HTML経済社会ゲーム

日本の法令データを参照しながら、商品販売、店舗・企業運営、製造、供給網、価格形成、企業グループ、買収・合併、競争政策、倒産などを扱う経済社会シミュレーションを目指すプロジェクトです。


## Demo版（v0.1）

- [ブラウザーで試す（index.html）](https://marimutukisinnmu-rgb.github.io/syakaigame/) — GitHub Pages が有効な場合の公開URLです。
- [HTMLソースを見る](https://github.com/marimutukisinnmu-rgb/syakaigame/blob/main/index.html)

仕入れ・製造・価格設定・日次販売・広告・NPC雇用・法人化・ゲーム内ローンを試せます。外部ライブラリ不要の単一HTMLで、進行状況は使用中ブラウザーの `localStorage` に保存されます。これは試作版で、複数人同時プレイ、サーバー保存、法令の自動適用、合併・倒産処理などはまだ実装していません。通貨は架空の「ミライ円」で、現実のお金や労働とは接続しません。

## Demo版（v0.1）

まずは単一HTMLで遊べる試作版を追加しました。

- **[Demoを開く（GitHub Pages）](https://marimutukisinnmu-rgb.github.io/syakaigame/)** — GitHub Pagesの初回設定とデプロイが完了すると使える公開URLです。
- [自動公開ワークフロー](https://github.com/marimutukisinnmu-rgb/syakaigame/blob/main/.github/workflows/deploy-pages.yml)

**初回公開の設定：** リポジトリの `Settings` → `Pages` → `Build and deployment` → `Source` で `GitHub Actions` を選択してください。Pagesが未設定だと最初のデプロイは失敗します。設定後、`Actions` タブから `Publish Demo to GitHub Pages` を再実行できます。
- [index.html のソースを見る](https://github.com/marimutukisinnmu-rgb/syakaigame/blob/main/index.html)

### できること

- 原材料市場で木材・鉄材・小麦粉・電子部品を仕入れる
- 木製チェア、パン、デスク、ランプを製造する
- 商品価格を設定し、1日進めて需要に応じた販売を精算する
- 屋号の変更、ゲーム内の法人化、広告、架空NPCの雇用
- デモ銀行からの借入と返済、日次の売上・利益・取引履歴の確認
- ブラウザー内への自動セーブとリセット

### 起動方法・制限

HTMLファイルをダウンロードし、ブラウザーで `index.html` を開くと起動します。外部ライブラリやサーバーは不要で、進行状況はそのブラウザーの `localStorage` に保存されます。端末やブラウザーをまたいで同期はされません。

これはDemo 0.1です。マルチプレイ、サーバー保存、プレイヤー間取引、合併・買収、正式な倒産手続、法令データを使った自動判定は未実装です。ゲーム内通貨は架空の「ミライ円」で、現実のお金・商品・金券・労働・報酬との交換は禁止です。会社設立やローンも、ゲーム内の架空ルールとしてのみ動作します。

## 法令データの調査資料

調査レポートは専用の `docs` ブランチにあります。

- [日本法令データ一式の機械的検査・経済社会ゲーム向け制度設計メモ（docsブランチ）](https://github.com/marimutukisinnmu-rgb/syakaigame/blob/docs/japan-law-data-review.md)

この資料では、検査対象 `all_xml.zip` の構造・件数・機械的検査結果、法令データの出典と利用条件への注意、経済社会ゲームに関係する法令分野、検索基盤とゲームルールの設計案をまとめています。

## 重要な注意

法令XMLを保管・検索することと、現実の法律を自動で正確に適用することは別です。ゲームの判定は教育・シミュレーション目的のものであり、法的判断を保証しません。現実法の説明とゲーム独自ルールを区別し、法令の施行時点、附則、経過措置、委任命令、個別の利用条件を確認してください。

学校の生徒が参加する場合は、実名・学籍情報・住所・電話番号などの不要な個人情報を集めず、アカウント権限・通報・異議申立て・ログ保護の設計を優先します。

## データソース候補

- [e-Gov法令検索](https://laws.e-gov.go.jp/)
- [e-Gov利用規約](https://www.e-gov.go.jp/terms/)
- [公共データ利用規約（第1.0版）](https://www.digital.go.jp/resources/open_data/public_data_license_v1.0)
- [e-Gov法令検索API v2](https://laws.e-gov.go.jp/api/2/swagger-ui/)

利用時は公式の最新規約、収録範囲、第三者権利、出典表示条件を確認してください。
