import html
import streamlit as st
import json
from backend import query_arabic_chatbot
from streamlit_javascript import st_javascript

# ─────────────────────────────────────────────
# 1. Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="المساعد الشرعي الذكي",
    page_icon="🕋",
    layout="centered"
)

# ─────────────────────────────────────────────
# 2. Session State Initialization
# ─────────────────────────────────────────────
if "search_history" not in st.session_state:
    st.session_state.search_history = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""
if "local_counter_synced" not in st.session_state:
    st.session_state.local_counter_synced = False
if "session_query_count" not in st.session_state:
    st.session_state.session_query_count = 0

# ─────────────────────────────────────────────
# 3. Robust Browser Local Storage Security Layer
# ─────────────────────────────────────────────
js_get_counter = """
(function() {
    var count = localStorage.getItem('sharia_bot_user_requests');
    if (count === null) {
        localStorage.setItem('sharia_bot_user_requests', '0');
        return 0;
    }
    return parseInt(count);
})();
"""
user_browser_stored_count = st_javascript(js_get_counter)

if isinstance(user_browser_stored_count, int):
    if not st.session_state.local_counter_synced:
        st.session_state.session_query_count = max(st.session_state.session_query_count, user_browser_stored_count)
        st.session_state.local_counter_synced = True
    else:
        if st.session_state.session_query_count > user_browser_stored_count:
            st_javascript(f"localStorage.setItem('sharia_bot_user_requests', '{st.session_state.session_query_count}');")

history_count = len(st.session_state.search_history)
browser_count = user_browser_stored_count if isinstance(user_browser_stored_count, int) else 0

effective_used = max(st.session_state.session_query_count, history_count, browser_count)

USER_LIMIT = 5
has_reached_limit = effective_used >= USER_LIMIT

# ─────────────────────────────────────────────
# 4. Islamic Aesthetic CSS Styling
# ─────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght=300;400;600;700&display=swap');

    html, body, [class*="css"], p, h1, h2, h3, div, span {
        font-family: 'Cairo', sans-serif !important;
        direction: rtl;
        text-align: right;
    }

    .stApp {
        background: linear-gradient(180deg, #fbfaf5 0%, #f4f1e6 100%);
    }

    .header-banner {
        background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
        padding: 40px 25px;
        border-radius: 24px;
        text-align: center !important;
        box-shadow: 0 12px 30px -10px rgba(6, 78, 59, 0.25);
        margin-bottom: 25px;
        border: 2px solid #d97706;
    }
    .header-banner h1 {
        color: #ffffff !important;
        margin: 0;
        font-weight: 700;
        font-size: 2.3em;
        text-align: center !important;
    }
    .header-banner p {
        color: #fcd34d !important;
        margin-top: 14px;
        margin-bottom: 0;
        font-size: 1.1em;
        text-align: center !important;
    }

    .quota-pill-box {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #ffffff;
        padding: 14px 22px;
        border-radius: 14px;
        border: 1px solid #e7e2d2;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(6, 78, 59, 0.03);
    }

    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 2px solid #064e3b !important;
        border-radius: 16px !important;
        padding: 8px 12px !important;
        box-shadow: 0 10px 25px -5px rgba(6, 78, 59, 0.08) !important;
    }
    
    div[data-baseweb="input"]:focus-within {
        border-color: #d97706 !important;
        box-shadow: 0 10px 30px -5px rgba(217, 119, 6, 0.15) !important;
    }
    
    label[data-testid="stWidgetLabel"] p {
        color: #064e3b !important;
        font-weight: 700 !important;
        font-size: 1.2em !important;
        margin-bottom: 10px !important;
    }

    .lock-alert {
        background-color: #fff1f2;
        border-right: 5px solid #dc2626;
        color: #991b1b;
        padding: 16px;
        border-radius: 12px;
        font-weight: 600;
        margin-bottom: 25px;
    }

    .answer-box {
        background-color: #ffffff;
        padding: 35px;
        border-radius: 20px;
        box-shadow: 0 15px 35px -15px rgba(0,0,0,0.06);
        border: 1px solid #e7e2d2;
        border-top: 6px solid #064e3b;
        margin-top: 35px;
        margin-bottom: 20px;
    }
    .answer-row {
        background-color: #fbfbf9;
        padding: 14px 18px;
        border-radius: 12px;
        margin-bottom: 14px;
        border: 1px solid #f0ece0;
        font-size: 1.05em;
        line-height: 1.8;
    }
    .ruling-row {
        background-color: #fffbeb;
        padding: 16px 20px;
        border-radius: 12px;
        margin-bottom: 14px;
        border-right: 5px solid #d97706;
        border-left: 1px solid #fef3c7;
        border-top: 1px solid #fef3c7;
        border-bottom: 1px solid #fef3c7;
        font-size: 1.1em;
        line-height: 1.8;
        color: #b45309;
        font-weight: 700;
    }
    .answer-detail {
        padding: 12px 4px;
        font-size: 1.05em;
        line-height: 1.9;
        color: #27272a;
        text-align: justify;
    }
    
    .source-badge {
        display: inline-block;
        background-color: #f4f1e6;
        color: #064e3b !important;
        padding: 10px 20px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 0.9em;
        text-decoration: none !important;
        margin-top: 12px;
        border: 1px solid #e7e2d2;
    }

    .history-container {
        background-color: #ffffff;
        padding: 16px 22px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.01);
        border: 1px solid #e7e2d2;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge-success {
        background-color: #d1fae5;
        color: #065f46;
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .badge-danger {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.85em;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 5. Header Banner
# ─────────────────────────────────────────────
st.markdown("""
    <div class="header-banner">
        <h1>🕋 الخبير الشرعي الذكي للحج والعمرة</h1>
        <p>منظومة ذكية مدعومة بالذكاء الاصطناعي التوليدي وموثقة بالكامل بالفتاوى الشرعية الهيكلية</p>
    </div>
""", unsafe_allow_html=True)

st.info("💡 **توجيه ذكي:** يمكنك طرح أي سؤال يتعلق بأحكام الحج، العمرة، مواقيت الإحرام، أو النسك.")

# ─────────────────────────────────────────────
# 6. Quota Tracker Rendering
# ─────────────────────────────────────────────
remaining_slots = max(0, USER_LIMIT - effective_used)

if has_reached_limit:
    st.markdown(f"""
        <div class="quota-pill-box" style="border-color: #fca5a5;">
            <span style="color: #dc2626; font-weight: 700;">🔒 استهلاك الحصّة اليومية: {effective_used} / {USER_LIMIT} أسئلة</span>
            <span class="badge-danger">الحساب مقفل مؤقتاً</span>
        </div>
        <div class="lock-alert">
            🛑 عذراً! لقد استهلكت الحد الأقصى المسموح به لك اليوم ({USER_LIMIT} أسئلة) للحفاظ على حصة خادم الـ API المجاني. لا يمكنك إرسال المزيد من الأسئلة حتى لو قمت بإعادة تحميل الصفحة.
        </div>
    """, unsafe_allow_html=True)
else:
    status_badge_html = '<span class="badge-success">🟢 وضع آمن</span>' if remaining_slots > 1 else '<span class="badge-danger">⚠️ سؤال أخير متبقي</span>'
    st.markdown(f"""
        <div class="quota-pill-box">
            <span style="color: #374151; font-weight: 600;">📊 أسئلتك المستخدمة اليوم: <b style="color:#064e3b;">{effective_used}</b> من أصل <b style="color:#064e3b;">{USER_LIMIT}</b></span>
            {status_badge_html}
        </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 7. Input Field
# ─────────────────────────────────────────────
user_query = st.text_input(
    label="أدخل سؤالك الفقهي المباشر هنا:",
    placeholder="🔒 تم قفل المدخلات لتجاوز الحد اليومي" if has_reached_limit else "اكتب سؤالك هنا بوضوح...",
    key="user_input",
    disabled=has_reached_limit
)

# ─────────────────────────────────────────────
# 8. Query Execution
# ─────────────────────────────────────────────
if user_query and user_query != st.session_state.last_query and not has_reached_limit:
    with st.spinner("🔍 جاري البحث الفقهي ومطابقة النصوص الشرعية..."):
        try:
            raw_response = query_arabic_chatbot(user_query)
            response_data = json.loads(raw_response)

            st.session_state.session_query_count += 1
            st.session_state.last_response = response_data
            st.session_state.last_query = user_query

            new_target_count = st.session_state.session_query_count
            st_javascript(f"localStorage.setItem('sharia_bot_user_requests', '{new_target_count}');")

            is_found = response_data.get("answer_found", False)
            status = "تمت الإجابة بنجاح" if is_found else "الإجابة غير متوفرة"

            if not st.session_state.search_history or st.session_state.search_history[0]["query"] != user_query:
                st.session_state.search_history.insert(0, {
                    "query": user_query,
                    "status": status
                })

            st.rerun()

        except Exception as e:
            st.error(f"حدث خطأ غير متوقع أثناء معالجة البيانات: {e}")

# ─────────────────────────────────────────────
# 9. Display Answer Box
# ─────────────────────────────────────────────
if st.session_state.last_response:
    response_data = st.session_state.last_response
    is_found = response_data.get("answer_found", False)

    if is_found:
        topic  = html.escape(response_data.get("topic", "غير محدد"))
        main_q = html.escape(response_data.get("main_question", "غير محدد"))
        ruling = html.escape(response_data.get("ruling", "غير محدد"))
        answer = html.escape(response_data.get("answer", "غير محدد"))
        source = response_data.get("source", "")
        answer_html = answer.replace("\n", "<br>")

        st.markdown(f"""
            <div class="answer-box">
                <h3 style="color:#064e3b; margin-top:0; border-bottom:2px solid #f4f1e6; padding-bottom:12px; font-weight:700;">
                    📋 النتيجة الفقهية الموثقة:
                </h3>
                <div class="answer-row"><strong>📌 الموضوع:</strong> {topic}</div>
                <div class="answer-row"><strong>❓ السؤال الرئيسي للفتوى:</strong> {main_q}</div>
                <div class="ruling-row"><strong>💡 الخلاصة والحكم الشرعي:</strong> {ruling}</div>
                <div style="margin-top:20px; margin-bottom:8px; color:#064e3b; font-weight:700;">📝 الجواب التفصيلي والأدلة:</div>
                <div class="answer-detail">{answer_html}</div>
            </div>
        """, unsafe_allow_html=True)

        if source:
            escaped_source = html.escape(source)
            if source.startswith("http"):
                st.markdown(f'<a href="{escaped_source}" target="_blank" class="source-badge">🔗 المصدر الأصلي</a>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="source-badge">📚 المصدر: {escaped_source}</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ عذراً، الإجابة الدقيقة غير متوفرة ضمن قاعدة البيانات الموثقة لدينا حالياً لحمايتك من التفسيرات الخاطئة.")

# ─────────────────────────────────────────────
# 10. Search History Log
# ─────────────────────────────────────────────
st.markdown("<br><h3 style='color:#022c22; font-size:1.25em; margin-bottom:15px; font-weight:700;'>🕒 سجل الأسئلة السابقة في هذه الجلسة:</h3>", unsafe_allow_html=True)

if st.session_state.search_history:
    for item in st.session_state.search_history:
        badge_class = "badge-success" if item["status"] == "تمت الإجابة بنجاح" else "badge-danger"
        st.markdown(f"""
            <div class="history-container">
                <span style="color:#1f2937; font-weight:500;">❓ {html.escape(item["query"])}</span>
                <span class="{badge_class}">{html.escape(item["status"])}</span>
            </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("<p style='color:#9ca3af; font-size:0.95em;'>لا توجد أسئلة في السجل حالياً.</p>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 11. Footer
# ─────────────────────────────────────────────
st.markdown("""
    <hr style="margin-top:50px; border-color:#e7e2d2;">
    <p style="text-align:center; color:#9ca3af; font-size:0.85em;">مشروع التخرج المطور للعام الدراسي 2026</p>
""", unsafe_allow_html=True)