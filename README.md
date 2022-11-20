## booksns-api
Flaskの練習として作成した、本とそのレビューの情報を扱うREST API。
内部で[楽天ブックス書籍検索API](https://webservice.rakuten.co.jp/documentation/books-book-search)を使用している。

Next.jsで作成したフロントエンドから呼び出す想定で作成した。フロントエンド用のリポジトリは[こちら](https://github.com/toyoce/booksns)。

### 機能一覧
- 本の検索
- レビューの取得
- アカウント作成、ログイン
- レビューの登録、更新、削除
- 他のユーザーのレビューへのいいねの登録、削除

### 使用技術・ライブラリ
- Flask
- Flask-RESTful
- Flask-SQLAlchemy
- Flask-JWT-Extended
- Flask-Cors
- requests
- gunicorn

### 起動方法
`.env`を作成し、環境変数の値を設定
```bash
$ cp .env.example .env
```

依存ライブラリをインストール
```bash
$ pip install -r requirements.txt
```

起動
```bash
$ python app.py
# or
$ gunicorn app:app
```
