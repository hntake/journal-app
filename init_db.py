import sqlite3

# データベース作成
conn = sqlite3.connect('journal.db')
cur = conn.cursor()

# ユーザーテーブル
cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    name TEXT
)
''')

# 記録テーブル
cur.execute('''
CREATE TABLE IF NOT EXISTS journals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    name TEXT NOT NULL,
    content TEXT NOT NULL
)
''')

# サンプルユーザー追加
users = [
    ('staff1', 'pass123', '職員', None),
    ('yamada_mother', 'yamada', '家族', '山田 太郎'),
    ('yamakawa_mother', 'yamakawa', '家族', '山川 太郎'),
    ('yamamoto_mother', 'yamamoto', '家族', '山本 太郎'),
    ('suzuki_father', 'suzuki', '家族', '鈴木 花子'),
]

for u in users:
    try:
        cur.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)", u)
    except sqlite3.IntegrityError:
        pass  # すでに登録済みなら無視

conn.commit()
conn.close()
