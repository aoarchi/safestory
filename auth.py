import streamlit as st
import db


def login_page():
    st.markdown("""
    <style>
    .auth-header { text-align:center; padding: 2rem 0 1rem; }
    </style>
    <div class="auth-header">
        <h1>📚 SafeStory</h1>
        <p style="color:#666;">부모가 검증한 동화만 보는 어린이 영상 플랫폼</p>
    </div>
    """, unsafe_allow_html=True)

    col = st.columns([1, 1.6, 1])[1]
    with col:
        tab_in, tab_up = st.tabs(["로그인", "회원가입"])

        with tab_in:
            with st.form("login"):
                username = st.text_input("아이디")
                password = st.text_input("비밀번호", type="password")
                if st.form_submit_button("로그인", use_container_width=True, type="primary"):
                    user = db.verify_login(username, password)
                    if user:
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("아이디 또는 비밀번호가 틀렸습니다.")

        with tab_up:
            with st.form("register"):
                u = st.text_input("아이디 (영문·숫자)")
                p1 = st.text_input("비밀번호", type="password")
                p2 = st.text_input("비밀번호 확인", type="password")
                name = st.text_input("닉네임")
                age = st.selectbox("자녀 연령대", ["", "0-2세", "3-5세", "6-8세", "9-12세"])
                bio = st.text_area("한 줄 소개 (선택)", height=68)
                if st.form_submit_button("회원가입", use_container_width=True, type="primary"):
                    if not u or not p1:
                        st.error("아이디와 비밀번호를 입력해주세요.")
                    elif p1 != p2:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif len(p1) < 4:
                        st.error("비밀번호는 4자 이상이어야 합니다.")
                    elif db.create_user(u, p1, name, age, bio):
                        st.success("가입 완료! 로그인해주세요.")
                    else:
                        st.error("이미 사용 중인 아이디입니다.")


def logout():
    for k in ("user", "child_auth", "cur_video", "preview"):
        st.session_state.pop(k, None)
    st.rerun()
