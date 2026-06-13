import os
import json
import time
from typing import List
import chromadb
from google import genai
from google.genai import types
from pydantic import BaseModel
import streamlit as st
# ─────────────────────────────────────────────
# 1. API Keys Cluster & Rotating Mechanism
# ─────────────────────────────────────────────
# مجموعة المفاتيح الخاصة بكِ لضمان استمرارية الخدمة وتفادي قيود الطلبات (Rate Limits)
API_KEYS_POOL = st.secrets["API_KEYS_POOL"]

class RotatingGeminiBackend:
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        self.update_client()

    def update_client(self):
        self.client = genai.Client(api_key=self.api_keys[self.current_index])

    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        self.update_client()
        print(f"🔄 [Backend Key Rotation] Switched to Key Index: {self.current_index}")

# تهيئة مدير المفاتيح الدوّار
gemini_manager = RotatingGeminiBackend(API_KEYS_POOL)

# ─────────────────────────────────────────────
# 2. Dynamic Embedding Function linked to Vector DB
# ─────────────────────────────────────────────
class GoogleGeminiEmbeddingFunction(chromadb.EmbeddingFunction):
    """دالة تحويل النصوص إلى متجهات دلالية متوافقة مع ChromaDB عبر نموذج gemini-embedding-2"""
    def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
        embeddings = []
        for text in input:
            for attempt in range(5):
                try:
                    content_payload = types.Content(parts=[types.Part.from_text(text=str(text))])
                    response = gemini_manager.client.models.embed_content(
                        model="gemini-embedding-2",
                        contents=content_payload
                    )
                    for embedding in response.embeddings:
                        embeddings.append(embedding.values)
                    break
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "ResourceExhausted" in err_msg or "Quota" in err_msg:
                        gemini_manager.rotate_key()
                        time.sleep(2 ** attempt)
                    else:
                        raise e
        return embeddings
# الطريقة الأضمن والأصح لكل أنظمة التشغيل


DB_PATH = os.path.join(os.getcwd(), "RAGsystemDB")
# أو ببساطة إذا كنتِ تمرين المسار مباشرة كـ string:
# client = chromadb.PersistentClient(path="RAGsystemDB")

# الاتصال بقاعدة البيانات الدلالية المستقلة المخزنة في مجلد مشروعكِ
google_ef = GoogleGeminiEmbeddingFunction()
chroma_client = chromadb.PersistentClient(path=DB_PATH)
collection = chroma_client.get_or_create_collection(
    name="HajjUmrah",
    embedding_function=google_ef,
    metadata={"hnsw:space": "cosine"}
)

# ─────────────────────────────────────────────
# 3. Structured Output Response Schemas (Pydantic)
# ─────────────────────────────────────────────
class ArabicGuardedResponse(BaseModel):
    answer_found: bool
    topic: str
    main_question: str
    answer: str
    ruling: str

def _error_response(message: str) -> str:
    """دالة مساعدة لصياغة استجابة موحدة في حال حدوث خطأ أو استثناء"""
    return json.dumps({
        "answer_found": False,
        "id": "", "topic": "", "main_question": "",
        "answer": message, "ruling": "", "source": ""
    }, ensure_ascii=False)

# ─────────────────────────────────────────────
# 4. Core Pure-Vector RAG Pipeline
# ─────────────────────────────────────────────
def query_arabic_chatbot(user_question: str) -> str:
    # 1. الاستعلام والبحث الدلالي من كروما ديبي مباشرة
    try:
        results = collection.query(
            query_texts=[user_question],
            n_results=3
        )
    except Exception as e:
        return _error_response(f"فشل الاتصال بقاعدة البيانات الدلالية: {str(e)}")

    if not results["documents"] or not results["documents"][0]:
        return _error_response("لم يتم العثور على نتائج مطابقة في قاعدة البيانات.")

    # 2. فلترة صرامة الاسترجاع لحماية المستخدم من الهلوسة الفقهية
    OPTIMIZED_THRESHOLD = 0.15
    best_distance = results["distances"][0][0]
    print(f"🔍 [ChromaDB Search] أفضل مسافة جيب تمام (Cosine Distance): {best_distance:.4f}")

    if best_distance > OPTIMIZED_THRESHOLD:
        print("⛔ [Rejected] السؤال بعيد دلالياً عن الفتاوى المقيدة — تم تفعيل حاجز الحماية البرمجي.")
        return json.dumps({
            "answer_found": False, "id": "", "topic": "", 
            "main_question": "", "answer": "", "ruling": "", "source": ""
        }, ensure_ascii=False)

    # 3. بناء السياق الفقهي من الميتاداتا المحدثة مباشرة (دون الاستعانة بـ JSON)
    context_blocks = []
    best_fatwa_id = str(results["ids"][0][0])
    best_source_url = ""

    for i in range(len(results["metadatas"][0])):
        if results["distances"][0][i] > OPTIMIZED_THRESHOLD:
            break
        
        meta = results["metadatas"][0][i]
        
        if i == 0:
            best_source_url = str(meta.get("source_url", ""))

        # استخراج الحقول الفقهية المدمجة حديثاً بأمان من الميتاداتا
        f_topic = meta.get("topic") or "عام"
        f_question = meta.get("main_question") or results["documents"][0][i] or "غير محدد"
        f_answer = meta.get("answer") or "غير محدد"
        f_ruling = meta.get("ruling") or "غير محدد"

        block = (
            f"--- فتوى مرجعية موثقة {i+1} ---\n"
            f"الموضوع: {f_topic}\n"
            f"السؤال الشرعي المعتمد: {f_question}\n"
            f"الجواب التفصيلي والأدلة: {f_answer}\n"
            f"الحكم الشرعي المستنبط: {f_ruling}"
        )
        context_blocks.append(block)

    if not context_blocks:
        return json.dumps({
            "answer_found": False, "id": "", "topic": "", 
            "main_question": "", "answer": "", "ruling": "", "source": ""
        }, ensure_ascii=False)

    retrieved_context = "\n\n".join(context_blocks)

    # 4. هندسة الأوامر الحازمة والتوليد الخاضع للرقابة (Guarded Generation) عبر Gemini Flash 2.5
    system_instruction = (
        "أنت باحث ومساعد شرعي معاصر وخبير متخصص وموثق في أحكام الحج والعمرة. "
        "مهمتك الأساسية هي الإجابة عن أسئلة الحجاج والزوار بالاعتماد التام والحصري على السياق المرفق فقط. "
        "أجب بدقة وموثوقية بالغة مستنداً إلى البيانات المرفقة. إذا كان السياق كافياً لتغطية جوانب مسألة المستخدم، "
        "قم بصياغة الإجابة الفقهية المستندة للنص في الحقول المناسبة وعيّن الحقل 'answer_found' إلى true. "
        "يُمنع منعاً باتاً استنتاج أحكام خارج سياق النص أو الاجتهاد الشخصي تفادياً للوقوع في الفتاوى الخاطئة."
    )

    prompt = f"السياق الفقهي المسترجع من قاعدة البيانات:\n{retrieved_context}\n\nسؤال المستخدم الحالي: {user_question}"

    # محاولة توليد الإجابة الهيكلية بصيغة JSON مع تدوير المفاتيح عند الطوارئ
    for attempt in range(len(API_KEYS_POOL) * 2):
        try:
            response = gemini_manager.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,  # صفر لضمان أعلى درجات الثبات والالتزام بالنص المنشور
                    response_mime_type="application/json",
                    response_schema=ArabicGuardedResponse,
                ),
            )

            # تحويل النص المستلم إلى قاموس وحقن المعرف والمصدر الخارجي
            final_data = json.loads(response.text)
            final_data["id"] = best_fatwa_id
            final_data["source"] = best_source_url

            return json.dumps(final_data, ensure_ascii=False)

        except Exception as e:
            err = str(e)
            if "429" in err or "ResourceExhausted" in err or "Quota" in err:
                gemini_manager.rotate_key()
                time.sleep(2)
                continue
            elif "503" in err:
                time.sleep(3)
                continue
            else:
                return _error_response(f"خطأ أثناء معالجة صياغة الإجابة الذكية: {err}")

    return _error_response("الخادم يواجه ضغطاً كبيراً في الطلبات حالياً، يرجى إعادة المحاولة بعد ثوانٍ قليلة.")
