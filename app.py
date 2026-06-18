import streamlit as st
import sqlite3
import requests
import os
import time
import urllib.request
import urllib.parse
import re
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi

# --- 1. సెటప్ ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# డైనమిక్ UI టెక్స్ట్
UI_TEXT = {
    "Telugu": {
        "title": "🎓 ఏఐ డైనమిక్ ట్యూటర్",
        "login_title": "లాగిన్ / రిజిస్టర్",
        "name": "మీ పేరు (Name):",
        "language": "మీకు ఇష్టమైన భాష (Language):",
        "start_btn": "యాప్ లోకి వెళ్ళండి 🚀",
        "profile": "ప్రొఫైల్",
        "level": "లెవెల్",
        "search_title": "🔍 ఈ రోజు ఏం నేర్చుకుందాం?",
        "search_hint": "ఏదైనా టాపిక్ టైప్ చేయండి (ఉదా: C language for loop, Algebra...)",
        "search_btn": "వీడియో వెతకండి",
        "lesson": "పాఠం",
        "watch_video": "ముందుగా ఈ వీడియో చూసి కాన్సెప్ట్ అర్థం చేసుకోండి.",
        "want_summary_btn": "వీడియో చూశాను. నాకు పూర్తి నోట్స్ ఇవ్వండి!",
        "summary_title": "📝 డీటెయిల్డ్ కాన్సెప్ట్ నోట్స్",
        "download_notes": "ఈ నోట్స్ డౌన్‌లోడ్ చేసుకోండి (.txt)",
        "ready_for_test_btn": "చదివేశాను, టెస్ట్ కి రెడీ! 👍",
        "task": "టెస్ట్ టైమ్! (Task)",
        "go_back_search": "⬅️ వేరే టాపిక్ వెతుకుతాను",
        "go_back_video": "⬅️ మళ్ళీ వీడియో చూస్తాను",
        "type_answer": "మీ ఆన్సర్ ఇక్కడ టైప్ చేయండి:",
        "submit_btn": "ఆన్సర్ సబ్మిట్ చేయండి",
        "success": "✅ సూపర్! కరెక్ట్ ఆన్సర్.",
        "fail": "❌ తప్పు ఆన్సర్!",
        "logout": "లాగౌట్",
        "saved_lessons": "📚 నేను నేర్చుకున్న టాపిక్స్"
    },
    "English": {
        "title": "🎓 AI Dynamic Tutor",
        "login_title": "Login / Register",
        "name": "Your Name:",
        "language": "Preferred Language:",
        "start_btn": "Enter App 🚀",
        "profile": "Profile",
        "level": "Level",
        "search_title": "🔍 What do you want to learn today?",
        "search_hint": "Type any topic (e.g., C language for loop, Algebra...)",
        "search_btn": "Search Video",
        "lesson": "Lesson",
        "watch_video": "Watch the video below to understand the concept.",
        "want_summary_btn": "I watched the video. Give me Full Notes!",
        "summary_title": "📝 Detailed Concept Notes",
        "download_notes": "Download Notes (.txt)",
        "ready_for_test_btn": "I read it, Ready for the Test! 👍",
        "task": "Test Time! (Task)",
        "go_back_search": "⬅️ Search another topic",
        "go_back_video": "⬅️ Watch Video Again",
        "type_answer": "Type your answer here:",
        "submit_btn": "Submit Answer",
        "success": "✅ Awesome! Correct Answer.",
        "fail": "❌ Wrong Answer!",
        "logout": "Logout",
        "saved_lessons": "📚 My Learned Topics"
    }
}

def t(key):
    lang = st.session_state.get("current_language", "English")
    ui_lang = "Telugu" if lang == "Telugu" else "English" 
    return UI_TEXT[ui_lang].get(key, key)

st.set_page_config(page_title="AI Dynamic Tutor", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .main-title { font-size: 45px; color: #4A90E2; text-align: center; font-weight: 800; text-transform: uppercase; margin-bottom: 20px;}
    .login-box { background-color: #f8f9fa; padding: 30px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); }
    .stButton>button { background-color: #4A90E2; color: white; border-radius: 8px; width: 100%; font-weight: bold; border: none; padding: 10px;}
    .stButton>button:hover { background-color: #357ABD; color: white; }
    .summary-box { background-color: #f9f9f9; padding: 25px; border-left: 6px solid #4A90E2; border-radius: 8px; font-size: 16px; margin-bottom: 20px; line-height: 1.6;}
</style>
""", unsafe_allow_html=True)

# --- 2. AI & యూట్యూబ్ ఫంక్షన్స్ ---
def call_groq_api(system_prompt, user_prompt, temperature=0.5):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {"model": "llama-3.1-8b-instant", "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": temperature}
    try:
        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 200: return res.json()['choices'][0]['message']['content'].strip()
        return "ERROR: API Connection Failed."
    except Exception as e: return f"ERROR: {e}"

def fetch_transcript(video_url):
    try:
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", video_url)
        if not video_ids: return ""
        transcript_list = YouTubeTranscriptApi.get_transcript(video_ids[0], languages=['te', 'en', 'hi', 'ta', 'ml'])
        return " ".join([t['text'] for t in transcript_list])[:5000] 
    except Exception: return ""

def generate_summary(topic, video_url, lang):
    transcript = fetch_transcript(video_url)
    sys_prompt = f"You are an expert educator. Provide a highly detailed and well-structured study material in {lang} language. If the topic includes math or science, format formulas properly using $ for inline and $$ for block equations. Make sure it covers the entire concept completely."
    
    if transcript:
        user_prompt = f"Topic: '{topic}'. Here is the video transcript: '{transcript}'. \nProvide a VERY DETAILED and COMPREHENSIVE summary covering ALL the concepts, examples, and important details mentioned in the video. Do not just write 4 lines. Write a full study note with headings and explanations."
    else:
        user_prompt = f"Provide a VERY DETAILED and COMPREHENSIVE study guide covering ALL the key concepts, formulas (if any), and important details for the topic: '{topic}'. Use appropriate headings and deep explanations."
        
    return call_groq_api(sys_prompt, user_prompt, temperature=0.3)

def generate_question_from_summary(topic, summary_text):
    sys_prompt = "You are an expert examiner. Generate ONLY the exact question text. Do NOT give answers."
    user_prompt = f"""Topic: '{topic}'. 
    Here are the detailed notes the student just read:
    "{summary_text[:3000]}"
    
    CRITICAL RULE: Ask ONE practical or problem-solving question based EXACTLY on the notes above. If it's math, give an equation to solve. If it's coding, give a task.
    Output ONLY the question text."""
    return call_groq_api(sys_prompt, user_prompt, temperature=0.4)

def evaluate_answer(topic, question, answer):
    sys_prompt = f"You are an examiner evaluating a student on '{topic}'. If the answer makes logical sense or the calculation is correct, output ONLY 'PASS'. If completely wrong, output 'FAIL: [1-line simple reason]'."
    return call_groq_api(sys_prompt, f"Question: {question}\nStudent Answer:\n{answer}", temperature=0.1)

# 💡 ఇది అసలైన మ్యాజిక్ ఫంక్షన్ (Specific topic filter)
def search_dynamic_video(topic, language):
    # -course -full ane tags vaadam valla pedda pedda 10 hours videos raavu
    search_query = f"{topic} in {language} language specific tutorial -course -full"
    query_string = urllib.parse.quote(search_query)
    url = f"https://www.youtube.com/results?search_query={query_string}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req).read().decode('utf-8')
        video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)
        for vid in video_ids:
            if len(vid) == 11: return f"https://www.youtube.com/watch?v={vid}"
    except Exception: pass
    return "https://www.youtube.com/watch?v=k9TUPpGqYTo" 

# --- 3. డేటాబేస్ లాజిక్ ---
def init_db():
    conn = sqlite3.connect("learning_platform.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT UNIQUE, language TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, hp INTEGER DEFAULT 100)''')
    c.execute('''CREATE TABLE IF NOT EXISTS video_history (id INTEGER PRIMARY KEY AUTOINCREMENT, student_name TEXT, topic TEXT, url TEXT)''')
    conn.commit()
    return conn

def get_user(name, language):
    conn = init_db(); c = conn.cursor()
    c.execute('SELECT * FROM students WHERE name = ?', (name,))
    user = c.fetchone()
    if not user:
        c.execute('INSERT INTO students (name, language) VALUES (?, ?)', (name, language))
        conn.commit(); user = (c.lastrowid, name, language, 1, 0, 100)
    else:
        c.execute('UPDATE students SET language = ? WHERE name = ?', (language, name))
        conn.commit()
    conn.close(); return {"name": user[1], "language": user[2], "level": user[3], "xp": user[4], "hp": user[5]}

def update_user(name, level, xp, hp):
    conn = init_db(); c = conn.cursor()
    c.execute('UPDATE students SET level = ?, xp = ?, hp = ? WHERE name = ?', (level, xp, hp, name))
    conn.commit(); conn.close()

def save_video(name, topic, url):
    conn = init_db(); c = conn.cursor()
    c.execute('INSERT INTO video_history (student_name, topic, url) VALUES (?, ?, ?)', (name, topic, url))
    conn.commit(); conn.close()

def get_all_saved_videos(name):
    conn = init_db(); c = conn.cursor()
    c.execute('SELECT topic, url FROM video_history WHERE student_name = ?', (name,))
    res = c.fetchall(); conn.close(); return res

# --- 4. వెబ్‌సైట్ UI ---
st.markdown(f"<div class='main-title'>{t('title')}</div>", unsafe_allow_html=True)

if "current_user" not in st.session_state: st.session_state.current_user = None
if "learning_phase" not in st.session_state: st.session_state.learning_phase = "search"
if "current_topic" not in st.session_state: st.session_state.current_topic = None
if "current_summary" not in st.session_state: st.session_state.current_summary = None
if "current_question" not in st.session_state: st.session_state.current_question = None
if "current_video_url" not in st.session_state: st.session_state.current_video_url = None
if "current_language" not in st.session_state: st.session_state.current_language = "English"

if not st.session_state.current_user:
    st.markdown("<div class='login-box'>", unsafe_allow_html=True)
    st.subheader(t('login_title'))
    col1, col2 = st.columns(2)
    with col1: user_name = st.text_input(t('name'))
    with col2: language = st.selectbox(t('language'), ["Telugu", "English", "Hindi", "Tamil", "Malayalam"])
    st.session_state.current_language = language 
    
    if st.button(t("start_btn")):
        if user_name:
            st.session_state.current_user = get_user(user_name, language)
            st.session_state.learning_phase = "search"
            st.rerun()
        else: st.warning("Please enter your name!")
    st.markdown("</div>", unsafe_allow_html=True)

else:
    user = st.session_state.current_user
    
    st.sidebar.header(f"👤 {user['name']}'s {t('profile')}")
    st.sidebar.metric(f"🏆 {t('level')}", user['level'])
    st.sidebar.metric("⭐ XP", f"{user['xp']} / 100")
    st.sidebar.metric(f"{'🟢' if user['hp'] > 50 else '🔴'} HP", f"{user['hp']} / 100")

    st.sidebar.markdown("---")
    lang_options = ["Telugu", "English", "Hindi", "Tamil", "Malayalam"]
    selected_language = st.sidebar.selectbox("🌐 " + t("language"), lang_options, index=lang_options.index(st.session_state.current_language))
    if selected_language != st.session_state.current_language:
        st.session_state.current_language = selected_language
        get_user(user['name'], selected_language); st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader(t("saved_lessons"))
    for i, vid in enumerate(get_all_saved_videos(user['name'])):
        with st.sidebar.expander(f"📌 {vid[0]}"): st.video(vid[1]) 

    if st.sidebar.button(t("logout")): st.session_state.current_user = None; st.rerun()

    if user['hp'] <= 0:
        st.error("💀 GAME OVER! Your Health is 0.")
        if st.button("Revive (Restore 100 HP)"):
            user['hp'] = 100; update_user(user['name'], user['level'], user['xp'], user['hp'])
            st.session_state.current_user = user; st.rerun()
            
    else:
        st.markdown("---")
        
        # 1. సెర్చ్ స్క్రీన్
        if st.session_state.learning_phase == "search":
            st.subheader(t('search_title'))
            user_topic = st.text_input(t('search_hint'))
            if st.button(t('search_btn')):
                if user_topic:
                    st.session_state.current_topic = user_topic
                    st.session_state.learning_phase = "lesson"
                    st.session_state.current_video_url = None
                    st.rerun()
                else: st.warning("దయచేసి టాపిక్ టైప్ చేయండి.")

        # 2. వీడియో స్క్రీన్
        elif st.session_state.learning_phase == "lesson":
            st.subheader(f"📚 {t('lesson')}: {st.session_state.current_topic}")
            if st.button(t('go_back_search')): st.session_state.learning_phase = "search"; st.rerun()

            if st.session_state.current_video_url is None:
                with st.spinner("🔍 వెతుకుతోంది..."):
                    st.session_state.current_video_url = search_dynamic_video(st.session_state.current_topic, st.session_state.current_language)
            
            st.info(t('watch_video'))
            st.video(st.session_state.current_video_url)
            
            if st.button(t("want_summary_btn")):
                st.session_state.learning_phase = "summary"
                st.session_state.current_summary = None 
                st.rerun()

        # 3. డీటెయిల్డ్ నోట్స్ & డౌన్‌లోడ్ స్క్రీన్
        elif st.session_state.learning_phase == "summary":
            st.subheader(t('summary_title'))
            if st.button(t("go_back_video")): st.session_state.learning_phase = "lesson"; st.rerun()
            
            if st.session_state.current_summary is None:
                with st.spinner("AI is analyzing the video and creating comprehensive notes for you..."):
                    st.session_state.current_summary = generate_summary(st.session_state.current_topic, st.session_state.current_video_url, st.session_state.current_language)
            
            st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
            st.markdown(st.session_state.current_summary)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.download_button(
                label="📥 " + t("download_notes"),
                data=st.session_state.current_summary,
                file_name=f"{st.session_state.current_topic}_Notes.txt",
                mime="text/plain"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button(t("ready_for_test_btn")):
                st.session_state.learning_phase = "test"
                st.session_state.current_question = None
                st.rerun()

        # 4. టెస్ట్ స్క్రీన్
        elif st.session_state.learning_phase == "test":
            st.subheader(f"📝 {t('task')}: {st.session_state.current_topic}")
            
            if st.session_state.current_question is None:
                with st.spinner("AI is making a question from the notes..."):
                    st.session_state.current_question = generate_question_from_summary(st.session_state.current_topic, st.session_state.current_summary)
            
            st.info(st.session_state.current_question)
            student_answer = st.text_area(t("type_answer"), height=150)
            
            if st.button(t("submit_btn")):
                if student_answer:
                    with st.spinner("AI is checking your answer..."):
                        result = evaluate_answer(st.session_state.current_topic, st.session_state.current_question, student_answer)
                    
                    if result == "PASS":
                        st.success(t("success")); st.balloons()
                        save_video(user['name'], st.session_state.current_topic, st.session_state.current_video_url)
                        
                        user['xp'] += 50
                        if user['xp'] >= 100: user['level'] += 1; user['xp'] -= 100; user['hp'] = 100; st.sidebar.success(f"🎉 Level Up!")
                        update_user(user['name'], user['level'], user['xp'], user['hp'])
                        st.session_state.current_user = user
                        
                        time.sleep(2.5)
                        st.session_state.learning_phase = "search"
                        st.session_state.current_topic = None
                        st.rerun()
                        
                    elif result.startswith("FAIL"):
                        st.error(f"{t('fail')} Penalty: -20 HP")
                        st.warning(f"Reason: {result.replace('FAIL:', '').strip()}")
                        user['hp'] -= 20
                        update_user(user['name'], user['level'], user['xp'], user['hp']); st.session_state.current_user = user
                else: st.warning("దయచేసి ఆన్సర్ రాసి సబ్మిట్ చేయండి.")