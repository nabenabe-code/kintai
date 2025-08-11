＃概要

従業員の出勤/退勤打刻、勤怠一覧・検索、web上とエクセルでの従業員・シフトの登録　Excelダウンロードを備えたシンプルな勤怠管理アプリです。
タイムカードでの勤怠入力、エクセルでの手入力を行ってる場合、このアプリで
-各従業員の出勤・退勤時刻の記録
- 各従業員の勤務時間、シフトの管理を一元管理出来ます。
それにより、今までの煩雑な作業を全て自動化**させて勤怠管理にかかっていた時間やコスト削減を実現できます。


＃主な機能

・打刻（出勤・しごとをはじめる / 退勤・しごとをおわる） <img width="1920" height="1008" alt="Image" src="https://github.com/user-attachments/assets/8ffd109a-bc36-4f09-8368-42fcacfb513d" />

・勤怠一覧・検索（社員番号/氏名/備考で絞り込み）

・従業員登録（社員番号・氏名・時給）/ Excelインポート

・シフト登録・一覧（YYYY-MM 指定 & 従業員検索）/ Excelインポート

・Excelダウンロード（従業員 / シフト / 勤怠）






使用技術
Backend: Python / Django（SQLite ローカル、Render では Postgres も可）

UI: Django Template + Bulma（CDN）

Excel: openpyxl（取込/出力）
