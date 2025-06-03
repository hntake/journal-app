import streamlit as st
import sqlite3
from datetime import datetime

#import openai
#from openai import OpenAI
#import os
#from dotenv import load_dotenv

# OpenAI APIキーの設定（安全な方法で環境変数などから取得推奨）
#load_dotenv()  # .envファイルを読み込み
#client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_connection():
    return sqlite3.connect('journal.db', check_same_thread=False)

# ユーザー認証
def authenticate(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role, name FROM users WHERE username=? AND password=?", (username, password))
    result = cur.fetchone()
    conn.close()
    return result if result else None
# --- ユーザー追加（職員のみ） ---
def add_user(username, password, role, name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password, role, name) VALUES (?, ?, ?, ?)",
                    (username, password, role, name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# 記録の追加
def add_entry(name, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO journals (created_at, name, content) VALUES (?, ?, ?)",
                (datetime.now().strftime("%Y-%m-%d %H:%M"), name, content))
    conn.commit()
    conn.close()

# 記録の取得
def get_entries(name=None):
    conn = get_connection()
    cur = conn.cursor()
    if name:
        cur.execute("SELECT rowid, created_at, name, content, reply FROM journals WHERE name=? ORDER BY created_at DESC", (name,))
    else:
        cur.execute("SELECT rowid, created_at, name, content, reply FROM journals ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


# 職員モードの画面
def show_staff_view():
    st.sidebar.write(f"こんにちは、**{st.session_state.name}** さん（職員）")
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.name = None
        st.rerun()

    st.subheader("✏️ 新しい記録を追加")

    # 名前の入力 + 候補表示
    input_text = st.text_input("対象者の名前を入力（1文字以上で候補を表示）")
    matches = []

    if input_text:
        all_names = get_family_names()
        matches = [name for name in all_names if input_text in name]

    selected_name = None
    if matches:
        selected_name = st.selectbox("候補", matches)

    content = st.text_area("記録内容")

    # AIボタン
    # if st.button("✍️ AIで記録文を提案"):
    #     if selected_name:
    #         with st.spinner("AIが記録文を生成中..."):
    #             prompt = f"{selected_name}さんに関する今日の様子を記録する文章を提案してください。"
    #             response = client.chat.completions.create(
    #                 model="gpt-3.5-turbo",
    #                 messages=[
    #                     {"role": "user", "content": "こんにちは、今日の記録文を提案してください"}
    #     ]
    # )
    #         suggested_text = response.choices[0].message.content
    #         st.session_state["suggested_text"] = suggested_text
    #     else:
    #         st.warning("先に対象者の名前を選んでください。")

    if st.button("保存"):
        if selected_name and content:
            add_entry(selected_name, content)
            st.success("記録を保存しました")
        else:
            st.warning("すべての項目を入力してください")

    st.subheader("📋 全記録")
    for _, date, name, content, reply in get_entries():
        st.markdown(f"**{date}** - {name}：{content}")
        if reply:
            st.markdown(f"↪️ **返答：** {reply}")

    st.subheader("👤 ユーザー追加")
    with st.form("add_user_form"):
        new_username = st.text_input("ユーザー名")
        new_password = st.text_input("パスワード", type="password")
        new_role = st.selectbox("権限", ["職員", "家族"])
        new_name = st.text_input("表示名")
        submitted = st.form_submit_button("追加")
        if submitted:
            if add_user(new_username, new_password, new_role, new_name):
                st.success("ユーザーを追加しました")
            else:
                st.error("そのユーザー名はすでに使われています")

# SQLiteから全家族名を取得
def get_family_names():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE role='家族'")
    names = [row[0] for row in cur.fetchall()]
    conn.close()
    return names


# 家族モードの画面
def show_family_view(name):
    st.sidebar.write(f"こんにちは、**{name}** さん（家族）")
    if st.sidebar.button("ログアウト"):
        st.session_state.authenticated = False
        st.session_state.role = None
        st.session_state.name = None
        st.rerun()

    st.subheader(f"👨‍👩‍👧‍👦 {name} さんの記録")

    for rowid, date, _, content, reply in get_entries(name=name):
        st.markdown(f"**{date}**：{content}")
        if reply:
            st.markdown(f"🗨️ **返答：** {reply}")
        else:
            with st.expander("返答を書く"):
                reply_text = st.text_area(f"この記録への返答", key=f"reply_{rowid}")
                if st.button("送信", key=f"send_{rowid}"):
                    save_reply(rowid, reply_text)
                    st.success("返答を送信しました")
                    st.rerun()

# 返答の保存               
def save_reply(journal_id, reply_text):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE journals SET reply=? WHERE rowid=?", (reply_text, journal_id))
    conn.commit()
    conn.close()

# def generate_ai_text(prompt):
#     try:
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",  # 無料プランでも使えるモデル
#             messages=[
#                 {"role": "system", "content": "あなたは介護・家族支援に詳しい記録文作成アシスタントです。"},
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.7,
#             max_tokens=150
#         )
#         return response.choices[0].message["content"].strip()
#     except Exception as e:
#         return f"⚠️ AI生成に失敗しました: {e}"


# アプリ本体
def main():
    st.title("家族・職員 ジャーナルアプリ")

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        username = st.text_input("ユーザー名")
        password = st.text_input("パスワード", type="password")

        if st.button("ログイン"):
            user = authenticate(username, password)
            if user:
                st.session_state.authenticated = True
                st.session_state.role = user[0]  # "家族" または "職員"
                st.session_state.name = user[1]
                st.rerun()
            else:
                st.error("ログイン失敗。ユーザー名またはパスワードが正しくありません。")
    else:
            # ログイン後のメニュー
            st.sidebar.write(f"こんにちは、{st.session_state.name} さん（{st.session_state.role}）")
            page = st.sidebar.selectbox("ページを選択", ["記録", "ユーザー追加（職員専用）"])

            if page == "記録":
                if st.session_state.role == "職員":
                    show_staff_view()
                elif st.session_state.role == "家族":
                    show_family_view(st.session_state.name)
            elif page == "ユーザー追加（職員専用）":
                if st.session_state.role == "職員":
                    add_user_page()  # ← ここでユーザー追加画面へ
                else:
                    st.error("このページにはアクセスできません。")


if __name__ == "__main__":
    main()
