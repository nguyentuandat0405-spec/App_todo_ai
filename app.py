import streamlit as st
import json
import os
import uuid
import random
import streamlit.components.v1 as components
from datetime import datetime, timedelta, date, time
from google import genai
from google.genai import types
import typing
from pydantic import BaseModel, Field
import plotly.express as px
import plotly.graph_objects as go
import calendar
import requests
from PIL import Image

# ==========================================
# CONFETTI & CELEBRATION
# ==========================================
PRAISE_MESSAGES = [
    ("🎉 Xuất sắc! Một deadline đã bay màu!", "🎉"),
    ("💪 Chiến thần cày cuốc là đây!", "💪"),
    ("🔥 Bùng cháy! Tiếp tục phá đảo nào!", "🔥"),
    ("🚀 Vũ trụ ghi nhận thành tích của bạn!", "🚀"),
    ("😎 Lạnh lùng và hiệu quả — bạn làm được rồi!", "😎"),
    ("⚡ Nhanh như chớp! Deadline sợ bạn lắm đó!", "⚡"),
    ("🏆 Thêm một chiến công vào hồ sơ!", "🏆"),
    ("✨ Tuyệt vời! Bạn đang làm rất tốt!", "✨"),
]

def fire_confetti():
    """Inject canvas-confetti JS để bắn pháo hoa toàn màn hình."""
    components.html("""
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.2/dist/confetti.browser.min.js"></script>
    <script>
    (function() {
        var duration = 2800;
        var animationEnd = Date.now() + duration;
        var defaults = { startVelocity: 30, spread: 360, ticks: 70, zIndex: 9999 };
        function randomInRange(min, max) { return Math.random() * (max - min) + min; }
        var interval = setInterval(function() {
            var timeLeft = animationEnd - Date.now();
            if (timeLeft <= 0) { clearInterval(interval); return; }
            var particleCount = 60 * (timeLeft / duration);
            confetti(Object.assign({}, defaults, {
                particleCount: particleCount,
                origin: { x: randomInRange(0.1, 0.4), y: Math.random() - 0.2 },
                colors: ['#ff6b6b','#ffd93d','#6bcb77','#4d96ff','#ff922b','#cc5de8']
            }));
            confetti(Object.assign({}, defaults, {
                particleCount: particleCount,
                origin: { x: randomInRange(0.6, 0.9), y: Math.random() - 0.2 },
                colors: ['#ff6b6b','#ffd93d','#6bcb77','#4d96ff','#ff922b','#cc5de8']
            }));
        }, 220);
    })();
    </script>
    <div style="height:0px;"></div>
    """, height=0)

# ==========================================
# CẤU HÌNH TRANG STREAMLIT
# ==========================================
st.set_page_config(page_title="Assignment Todo App", page_icon="📚", layout="wide")

if "show_confetti" not in st.session_state:
    st.session_state.show_confetti = False

DATA_FILE = "database_todos.json"
SCHEDULE_FILE = "database_schedule.json"
BUSY_FILE = "database_busy.json"
CONFIG_FILE = "config.json"
POMODORO_MINUTES = 25

if not os.path.exists(CONFIG_FILE):
    st.error("⚠️ Không tìm thấy file `config.json`! Ứng dụng đã bị dừng.")
    st.warning("Vui lòng tạo file `config.json` (bạn có thể copy từ `config.example.json`) và điền API Key của bạn trước khi chạy.")
    st.stop()

# ==========================================
# CUSTOM CSS
# ==========================================
st.markdown("""
<style>
.urgency-badge {
    padding: 4px 12px; border-radius: 6px; font-weight: 600;
    font-size: 0.82em; display: inline-block; margin-bottom: 4px;
}
.urgency-red { background: rgba(255,68,68,0.15); color: #e53935; border-left: 4px solid #e53935; }
.urgency-orange { background: rgba(255,152,0,0.15); color: #ef6c00; border-left: 4px solid #ef6c00; }
.urgency-green { background: rgba(76,175,80,0.15); color: #2e7d32; border-left: 4px solid #2e7d32; }
.urgency-done { background: rgba(158,158,158,0.15); color: #757575; border-left: 4px solid #9e9e9e; }
.urgency-overdue { background: rgba(183,28,28,0.2); color: #b71c1c; border-left: 4px solid #b71c1c; }
.pomodoro-box {
    background: linear-gradient(135deg, #ff6b6b22, #ee535322);
    border: 1px solid #ff6b6b44; border-radius: 12px;
    padding: 18px 24px; text-align: center; margin: 8px 0;
}
.pomodoro-time {
    font-size: 2.8em; font-weight: 700; color: #e53935;
    font-family: 'Courier New', monospace; letter-spacing: 3px;
}
.pomodoro-label { font-size: 0.9em; color: #999; }

/* Styles for Timetable (Dark Mode Optimized) */
.timetable-container {
    width: 100%;
    overflow-x: auto;
    margin-top: 20px;
    margin-bottom: 20px;
}
.timetable {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    min-width: 800px;
    background-color: transparent;
}
.timetable th, .timetable td {
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 8px;
    text-align: center;
    vertical-align: middle;
    font-size: 0.85em;
    width: 12.5%;
}
.timetable th {
    background-color: #111217;
    font-weight: 600;
    color: #e0e0e0;
    position: sticky;
    top: 0;
    z-index: 1;
}
.cell-time {
    font-weight: bold;
    background-color: #111217;
    color: #e0e0e0;
}
.cell-study {
    background-color: rgba(21, 101, 192, 0.3);
    color: #64b5f6;
    border-left: 4px solid #64b5f6;
    font-weight: 600;
}
.cell-busy {
    background-color: rgba(239, 108, 0, 0.25);
    color: #ffb74d;
    border-left: 4px solid #ffb74d;
}
.cell-deadline {
    background-color: rgba(198, 40, 40, 0.3);
    color: #ff8a80;
    border-left: 5px solid #ff8a80;
    font-weight: 800;
    font-size: 0.88em;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    box-shadow: inset 0 0 10px rgba(198,40,40,0.5);
    animation: deadline-pulse-dark 1.5s ease-in-out infinite;
}
@keyframes deadline-pulse-dark {
    0%   { box-shadow: inset 0 0 10px rgba(198,40,40,0.5); }
    50%  { box-shadow: inset 0 0 15px rgba(255,138,128,0.4); }
    100% { box-shadow: inset 0 0 10px rgba(198,40,40,0.5); }
}
.cell-free {
    background-color: rgba(46, 125, 50, 0.25);
    color: #81c784;
    border-left: 4px solid #81c784;
    font-size: 0.8em;
}
.cell-mixed {
    background: linear-gradient(135deg, rgba(198, 40, 40, 0.2) 50%, rgba(21, 101, 192, 0.2) 50%);
    color: #ffffff;
    font-weight: bold;
}
@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.8; }
    100% { opacity: 1; }
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# PYDANTIC MODEL CHO GEMINI API
# ==========================================
class TaskPriority(BaseModel):
    id: str = Field(description="ID của bài tập")
    priority_score: int = Field(description="Điểm số ưu tiên từ 1 đến 10. Điểm càng cao nghĩa là bài tập càng cần làm gấp.")
    ai_reason: str = Field(description="Một câu giải thích ngắn gọn bằng tiếng Việt tại sao bài tập này lại cần mức độ ưu tiên này.")

# ==========================================
# HÀM XỬ LÝ DỮ LIỆU LOCAL
# ==========================================
def load_json(filepath):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except json.JSONDecodeError:
        return []
    except Exception as e:
        st.error(f"Lỗi đọc {filepath}: {e}")
        return []

def save_json(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Lỗi lưu {filepath}: {e}")

def load_data(): return load_json(DATA_FILE)
def save_data(data): save_json(DATA_FILE, data)
def load_schedule(): return load_json(SCHEDULE_FILE)
def save_schedule(data): save_json(SCHEDULE_FILE, data)
def load_busy(): return load_json(BUSY_FILE)
def save_busy(data): save_json(BUSY_FILE, data)

def load_config() -> dict:
    try:
        if not os.path.exists(CONFIG_FILE):
            return {"gemini_api_key": "", "backup_api_key": "", "telegram_token": "", "telegram_chat_id": "", "telegram_schedule_time": "06:30"}
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"gemini_api_key": "", "backup_api_key": "", "telegram_token": "", "telegram_chat_id": "", "telegram_schedule_time": "06:30"}
            data = json.loads(content)
            
            # Tự động đồng bộ hóa từ khóa cũ (Zalo) sang khóa mới (Telegram) nếu có
            if "zalo_token" in data and "telegram_token" not in data:
                data["telegram_token"] = data.pop("zalo_token")
            if "zalo_user_id" in data and "telegram_chat_id" not in data:
                data["telegram_chat_id"] = data.pop("zalo_user_id")
                
            if "telegram_token" not in data: data["telegram_token"] = ""
            if "telegram_chat_id" not in data: data["telegram_chat_id"] = ""
            if "telegram_schedule_time" not in data: data["telegram_schedule_time"] = "06:30"
            if "backup_api_key" not in data: data["backup_api_key"] = ""
            return data
    except Exception:
        return {"gemini_api_key": "", "backup_api_key": "", "telegram_token": "", "telegram_chat_id": "", "telegram_schedule_time": "06:30"}

def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Lỗi lưu config: {e}")

# ==========================================
# HÀM TIỆN ÍCH
# ==========================================
def format_countdown(deadline_str):
    try:
        deadline = datetime.fromisoformat(deadline_str)
        now = datetime.now()
        diff = deadline - now
        if diff.total_seconds() < 0:
            return "⚠️ Đã quá hạn!"
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        parts = []
        if days > 0: parts.append(f"{days} ngày")
        if hours > 0: parts.append(f"{hours} tiếng")
        if minutes > 0: parts.append(f"{minutes} phút")
        return "Còn " + " ".join(parts)
    except Exception:
        return "N/A"

def deadline_seconds(task) -> float:
    try:
        return (datetime.fromisoformat(task.get("deadline", "")) - datetime.now()).total_seconds()
    except Exception:
        return float("inf")

def sort_tasks(tasks: list) -> list:
    return sorted(tasks, key=lambda x: (x.get("completed", False), deadline_seconds(x)))

def get_urgency_info(task):
    if task.get("completed", False): return "urgency-done", "✅ Hoàn thành"
    secs = deadline_seconds(task)
    hours = secs / 3600
    if secs < 0: return "urgency-overdue", "⚠️ QUÁ HẠN"
    elif hours < 24: return "urgency-red", "🔴 Khẩn cấp — Dưới 24h"
    elif hours < 72: return "urgency-orange", "🟠 Cần chú ý — Dưới 3 ngày"
    else: return "urgency-green", "🟢 Thong thả — Trên 3 ngày"

# ==========================================
# SIDEBAR - THANH BÊN
# ==========================================
st.sidebar.title("⚙️ Cài đặt & Thêm mới")

_cfg = load_config()
_saved_api_key = _cfg.get("gemini_api_key", "")
_saved_backup_key = _cfg.get("backup_api_key", "")

api_key = st.sidebar.text_input(
    "Gemini API Key", value=_saved_api_key, type="password",
    placeholder="Nhập Gemini API Key tại đây...",
    help="API Key chính của Google Gemini."
)
backup_api_key = st.sidebar.text_input(
    "Backup API Key (Groq/OpenAI)", value=_saved_backup_key, type="password",
    placeholder="Nhập API Key dự phòng...",
    help="Sử dụng API Key dự phòng (Groq Llama3 hoặc OpenAI) nếu Gemini quá tải."
)

if api_key != _saved_api_key or backup_api_key != _saved_backup_key:
    _cfg["gemini_api_key"] = api_key.strip()
    _cfg["backup_api_key"] = backup_api_key.strip()
    save_config(_cfg)
    st.toast("✅ Đã lưu cấu hình API thành công!", icon="🔑")

with st.sidebar.expander("💬 Cài đặt Telegram Bot", expanded=False):
    st.markdown("<small>1. Tìm `@BotFather` trên Telegram tạo Bot lấy **Bot Token**.<br>2. Tìm `@userinfobot` lấy **Chat ID** của bạn.</small>", unsafe_allow_html=True)
    t_token = st.text_input("Telegram Bot Token", value=_cfg.get("telegram_token", ""), type="password", placeholder="Ví dụ: 123456:ABC-DEF...")
    t_chatid = st.text_input("Telegram Chat ID", value=_cfg.get("telegram_chat_id", ""), placeholder="Ví dụ: 123456789")
    
    try:
        current_sched_time = datetime.strptime(_cfg.get("telegram_schedule_time", "06:30"), "%H:%M").time()
    except:
        current_sched_time = time(6, 30)
        
    t_time = st.time_input("Giờ tự động gửi thông báo hằng ngày", value=current_sched_time)

    if st.button("Lưu Cấu Hình Telegram", use_container_width=True):
        formatted_time = t_time.strftime("%H:%M")
        _cfg["telegram_token"] = t_token.strip()
        _cfg["telegram_chat_id"] = t_chatid.strip()
        _cfg["telegram_schedule_time"] = formatted_time
        save_config(_cfg)
        
        st.toast(f"✅ Đã lưu cấu hình & hẹn giờ gửi lúc {formatted_time}!", icon="💬")
        st.rerun()

st.sidebar.markdown("---")
_editing_task_id = st.session_state.get("editing_task_id")
tasks_data = load_data()
editing_task = next((t for t in tasks_data if t["id"] == _editing_task_id), None) if _editing_task_id else None

if editing_task:
    st.sidebar.subheader("📝 Sửa bài tập")
    with st.sidebar.form("edit_task_form"):
        e_title = st.text_input("Tên bài tập", value=editing_task["title"])
        e_subject = st.text_input("Tên môn học", value=editing_task["subject"])
        e_link = st.text_input("🔗 Link tài liệu/LMS (tuỳ chọn)", value=editing_task.get("link", ""))
        
        try:
            dl_dt = datetime.fromisoformat(editing_task["deadline"])
            default_date = dl_dt.date()
            default_time = dl_dt.time()
        except:
            default_date = date.today()
            default_time = time(23, 59)
            
        e_deadline_date = st.date_input("Ngày hạn nộp", value=default_date)
        e_deadline_time = st.time_input("Giờ hạn nộp", value=default_time)
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            save_btn = st.form_submit_button("Lưu thay đổi", use_container_width=True)
        with col_e2:
            cancel_btn = st.form_submit_button("Hủy", use_container_width=True)
            
        if save_btn:
            if not e_title.strip() or not e_subject.strip():
                st.sidebar.error("Vui lòng nhập đủ tên bài tập và môn học!")
            else:
                new_deadline = datetime.combine(e_deadline_date, e_deadline_time).isoformat()
                for t in tasks_data:
                    if t["id"] == _editing_task_id:
                        t["title"] = e_title.strip()
                        t["subject"] = e_subject.strip()
                        t["link"] = e_link.strip()
                        t["deadline"] = new_deadline
                        break
                save_data(tasks_data)
                del st.session_state["editing_task_id"]
                st.toast("✅ Đã cập nhật bài tập!")
                st.rerun()
        if cancel_btn:
            del st.session_state["editing_task_id"]
            st.rerun()
else:
    st.sidebar.subheader("➕ Thêm bài tập mới")
    with st.sidebar.form("add_task_form", clear_on_submit=True):
        title = st.text_input("Tên bài tập")
        subject = st.text_input("Tên môn học")
        link = st.text_input("🔗 Link tài liệu/LMS (tuỳ chọn)", placeholder="https://...")
        deadline_date = st.date_input("Ngày hạn nộp")
        deadline_time = st.time_input("Giờ hạn nộp")
        submit_btn = st.form_submit_button("Thêm bài tập", use_container_width=True)

        if submit_btn:
            if not title.strip() or not subject.strip():
                st.sidebar.error("Vui lòng nhập đủ tên bài tập và môn học!")
            else:
                deadline_dt = datetime.combine(deadline_date, deadline_time)
                new_task = {
                    "id": str(uuid.uuid4()),
                    "title": title.strip(),
                    "subject": subject.strip(),
                    "deadline": deadline_dt.isoformat(),
                    "completed": False,
                    "link": link.strip(),
                    "pomodoros_completed": 0
                }
                tasks_data.append(new_task)
                save_data(tasks_data)
                st.sidebar.success("Đã thêm thành công!")
                st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("📅 Quản lý Lịch học", expanded=False):
    schedule_data = load_schedule()
    
    st.markdown("**🤖 AI Trích Xuất Lịch Học**")
    uploaded_file = st.file_uploader("Tải ảnh TKB lên", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        if st.button("Quét Ảnh Bằng Gemini", use_container_width=True):
            if not api_key:
                st.warning("Vui lòng cấu hình Gemini API Key trước!")
            else:
                with st.spinner("Đang quét ảnh..."):
                    try:
                        image = Image.open(uploaded_file)
                        client = genai.Client(api_key=api_key)
                        prompt_ocr = "Hãy quét ảnh thời khóa biểu này và trích xuất danh sách môn học dưới dạng JSON array, trong đó mỗi môn học là 1 object có các trường: 'subject' (Tên môn), 'day' (Thứ trong tuần, ví dụ 'Thứ 2', 'Thứ 3'... 'Chủ Nhật'), 'start' (Giờ bắt đầu định dạng HH:mm), 'end' (Giờ kết thúc định dạng HH:mm). Chỉ trả về JSON array, không giải thích gì thêm."
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[image, prompt_ocr]
                        )
                        raw_json = response.text.strip().removeprefix("```json").removesuffix("```").strip()
                        parsed_data = json.loads(raw_json)
                        st.session_state.ocr_pending_schedule = parsed_data
                        st.success("Đã trích xuất ảnh thành công! Xem review bên dưới.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi khi quét ảnh: {e}")
                        
    txt_schedule = st.text_area("Hoặc dán văn bản TKB vào đây", height=80)
    if st.button("Quét Text Bằng Groq (Fallback)", use_container_width=True):
        if not txt_schedule.strip():
            st.warning("Vui lòng nhập văn bản TKB!")
        elif not backup_api_key:
            st.warning("Vui lòng cấu hình Backup API Key (Groq) trước!")
        else:
            with st.spinner("Đang quét văn bản bằng Groq..."):
                try:
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    headers = {"Authorization": f"Bearer {backup_api_key}", "Content-Type": "application/json"}
                    prompt_txt = f"Trích xuất môn học từ văn bản sau thành JSON array (với các trường: 'subject', 'day', 'start', 'end' (HH:mm)). Chỉ trả về JSON array hợp lệ.\n\n{txt_schedule}"
                    payload = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt_txt}]}
                    resp = requests.post(url, headers=headers, json=payload, timeout=15)
                    resp_data = resp.json()
                    if "choices" in resp_data:
                        content = resp_data["choices"][0]["message"]["content"]
                        raw_json = content.strip().removeprefix("```json").removesuffix("```").strip()
                        parsed_data = json.loads(raw_json)
                        st.session_state.ocr_pending_schedule = parsed_data
                        st.success("Đã trích xuất Text thành công! Xem review bên dưới.")
                        st.rerun()
                    else:
                        st.error("Lỗi từ Groq API!")
                except Exception as e:
                    st.error(f"Lỗi xử lý Groq: {e}")

    # OCR Preview & Quick Edit UI
    if st.session_state.get("ocr_pending_schedule"):
        st.markdown("---")
        st.markdown("**🔍 Review & Chỉnh Sửa AI OCR**")
        pending_list = st.session_state.ocr_pending_schedule
        updated_pending = []
        for index, item in enumerate(pending_list):
            st.markdown(f"**Môn học {index + 1}:**")
            p_subject = st.text_input(f"Tên môn", value=item.get("subject", ""), key=f"ocr_sub_{index}")
            try:
                day_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(item.get("day", "Thứ 2"))
            except ValueError:
                day_idx = 0
            p_day = st.selectbox(f"Thứ", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"], index=day_idx, key=f"ocr_day_{index}")
            
            col_t1, col_t2 = st.columns(2)
            with col_t1: p_start = st.text_input(f"Bắt đầu", value=item.get("start", "08:00"), key=f"ocr_st_{index}")
            with col_t2: p_end = st.text_input(f"Kết thúc", value=item.get("end", "09:30"), key=f"ocr_en_{index}")
            
            updated_pending.append({
                "subject": p_subject,
                "day": p_day,
                "start": p_start,
                "end": p_end
            })
            if st.button("Xóa môn này khỏi preview", key=f"ocr_del_one_{index}"):
                pending_list.pop(index)
                st.session_state.ocr_pending_schedule = pending_list
                st.rerun()
                
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Lưu Tất Cả", type="primary", key="ocr_save_all", use_container_width=True):
                for new_item in updated_pending:
                    new_item["id"] = str(uuid.uuid4())
                    schedule_data.append(new_item)
                save_schedule(schedule_data)
                del st.session_state["ocr_pending_schedule"]
                st.success("Đã lưu tất cả vào thời khóa biểu!")
                st.rerun()
        with col_act2:
            if st.button("Hủy bỏ tất cả", key="ocr_discard_all", use_container_width=True):
                del st.session_state["ocr_pending_schedule"]
                st.rerun()

    st.markdown("---")
    
    # Schedule Edit Form vs Add Form
    _editing_sched_id = st.session_state.get("editing_sched_id")
    editing_sched = next((s for s in schedule_data if s["id"] == _editing_sched_id), None) if _editing_sched_id else None
    
    if editing_sched:
        st.markdown("**📝 Sửa Lịch Học**")
        with st.form("edit_schedule_form"):
            es_subject = st.text_input("Tên môn học", value=editing_sched["subject"])
            try:
                day_idx = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(editing_sched["day"])
            except ValueError:
                day_idx = 0
            es_day = st.selectbox("Thứ trong tuần", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"], index=day_idx)
            
            try:
                sh_val = datetime.strptime(editing_sched.get("start", "08:00"), "%H:%M").time()
                eh_val = datetime.strptime(editing_sched.get("end", "09:30"), "%H:%M").time()
            except:
                sh_val = time(8, 0)
                eh_val = time(9, 30)
                
            col_s1, col_s2 = st.columns(2)
            with col_s1: es_start = st.time_input("Giờ bắt đầu", value=sh_val)
            with col_s2: es_end = st.time_input("Giờ kết thúc", value=eh_val)
            
            col_esb1, col_esb2 = st.columns(2)
            with col_esb1: save_sched_btn = st.form_submit_button("Lưu", use_container_width=True)
            with col_esb2: cancel_sched_btn = st.form_submit_button("Hủy", use_container_width=True)
            
            if save_sched_btn:
                if not es_subject.strip():
                    st.error("Tên môn học không được để trống!")
                elif es_end <= es_start:
                    st.error("Giờ kết thúc phải sau giờ bắt đầu!")
                else:
                    for s in schedule_data:
                        if s["id"] == _editing_sched_id:
                            s["subject"] = es_subject.strip()
                            s["day"] = es_day
                            s["start"] = es_start.strftime("%H:%M")
                            s["end"] = es_end.strftime("%H:%M")
                            break
                    save_schedule(schedule_data)
                    del st.session_state["editing_sched_id"]
                    st.toast("Đã cập nhật lịch học!")
                    st.rerun()
            if cancel_sched_btn:
                del st.session_state["editing_sched_id"]
                st.rerun()
    else:
        st.markdown("**✏️ Thêm Thủ Công**")
        with st.form("add_schedule_form", clear_on_submit=True):
            sched_subject = st.text_input("Tên môn học")
            sched_day = st.selectbox("Thứ trong tuần", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
            col_s1, col_s2 = st.columns(2)
            with col_s1: sched_start = st.time_input("Giờ bắt đầu")
            with col_s2: sched_end = st.time_input("Giờ kết thúc")
            sched_submit = st.form_submit_button("Thêm lịch học", use_container_width=True)
            if sched_submit:
                if not sched_subject.strip():
                    st.error("Vui lòng nhập tên môn học!")
                elif sched_end <= sched_start:
                    st.error("Giờ kết thúc phải sau giờ bắt đầu!")
                else:
                    new_sched = {
                        "id": str(uuid.uuid4()),
                        "subject": sched_subject.strip(),
                        "day": sched_day,
                        "start": sched_start.strftime("%H:%M"),
                        "end": sched_end.strftime("%H:%M")
                    }
                    schedule_data.append(new_sched)
                    save_schedule(schedule_data)
                    st.success("Đã thêm lịch học!")
                    st.rerun()
                    
    if schedule_data:
        st.markdown("**Danh sách Lịch học:**")
        for sched in schedule_data:
            col1, col2, col3 = st.columns([3, 0.8, 0.8])
            with col1:
                s_st = sched.get('start', sched.get('time', '00:00'))
                s_en = sched.get('end', '..')
                st.caption(f"**{sched['subject']}** - {sched['day']} ({s_st}-{s_en})")
            with col2:
                if st.button("📝", key=f"edit_sched_{sched['id']}", help="Sửa lịch học"):
                    st.session_state.editing_sched_id = sched['id']
                    st.rerun()
            with col3:
                if st.button("🗑", key=f"del_sched_{sched['id']}", help="Xóa lịch"):
                    schedule_data = [s for s in schedule_data if s['id'] != sched['id']]
                    save_schedule(schedule_data)
                    st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("🏃 Lịch bận cá nhân (Việc khác)", expanded=False):
    busy_data = load_busy()
    
    _editing_busy_id = st.session_state.get("editing_busy_id")
    editing_busy = next((b for b in busy_data if b["id"] == _editing_busy_id), None) if _editing_busy_id else None
    
    if editing_busy:
        st.markdown("**📝 Sửa Lịch Bận**")
        with st.form("edit_busy_form"):
            eb_title = st.text_input("Tên hoạt động (vd: Làm thêm)", value=editing_busy["title"])
            eb_day = st.selectbox("Thứ", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"], index=["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"].index(editing_busy["day"]))
            
            try:
                sh_val = datetime.strptime(editing_busy["start"], "%H:%M").time()
                eh_val = datetime.strptime(editing_busy["end"], "%H:%M").time()
            except:
                sh_val = time(8, 0)
                eh_val = time(10, 0)
                
            col_t1, col_t2 = st.columns(2)
            with col_t1: eb_start = st.time_input("Từ giờ", value=sh_val)
            with col_t2: eb_end = st.time_input("Đến giờ", value=eh_val)
            
            col_ebb1, col_ebb2 = st.columns(2)
            with col_ebb1: save_busy_btn = st.form_submit_button("Lưu", use_container_width=True)
            with col_ebb2: cancel_busy_btn = st.form_submit_button("Hủy", use_container_width=True)
            
            if save_busy_btn:
                if not eb_title.strip():
                    st.error("Tên hoạt động không được để trống!")
                elif eb_end <= eb_start:
                    st.error("Giờ kết thúc phải sau giờ bắt đầu!")
                else:
                    for b in busy_data:
                        if b["id"] == _editing_busy_id:
                            b["title"] = eb_title.strip()
                            b["day"] = eb_day
                            b["start"] = eb_start.strftime("%H:%M")
                            b["end"] = eb_end.strftime("%H:%M")
                            break
                    save_busy(busy_data)
                    del st.session_state["editing_busy_id"]
                    st.toast("Đã cập nhật lịch bận!")
                    st.rerun()
            if cancel_busy_btn:
                del st.session_state["editing_busy_id"]
                st.rerun()
    else:
        with st.form("add_busy_form", clear_on_submit=True):
            busy_title = st.text_input("Tên hoạt động (vd: Làm thêm)")
            busy_day = st.selectbox("Thứ", ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"])
            col_t1, col_t2 = st.columns(2)
            with col_t1: busy_start = st.time_input("Từ giờ")
            with col_t2: busy_end = st.time_input("Đến giờ")
            busy_submit = st.form_submit_button("Thêm lịch bận", use_container_width=True)
            if busy_submit:
                if not busy_title.strip():
                    st.error("Vui lòng nhập tên hoạt động!")
                elif busy_end <= busy_start:
                    st.error("Giờ kết thúc phải sau giờ bắt đầu!")
                else:
                    new_busy = {
                        "id": str(uuid.uuid4()),
                        "title": busy_title.strip(),
                        "day": busy_day,
                        "start": busy_start.strftime("%H:%M"),
                        "end": busy_end.strftime("%H:%M")
                    }
                    busy_data.append(new_busy)
                    save_busy(busy_data)
                    st.success("Đã thêm lịch bận!")
                    st.rerun()
    if busy_data:
        st.markdown("**Danh sách Lịch bận:**")
        for b in busy_data:
            col1, col2, col3 = st.columns([3, 0.8, 0.8])
            with col1:
                st.caption(f"**{b['title']}** - {b['day']} ({b['start']}-{b['end']})")
            with col2:
                if st.button("📝", key=f"edit_busy_{b['id']}", help="Sửa lịch bận"):
                    st.session_state.editing_busy_id = b['id']
                    st.rerun()
            with col3:
                if st.button("🗑", key=f"del_busy_{b['id']}", help="Xóa lịch bận"):
                    busy_data = [x for x in busy_data if x['id'] != b['id']]
                    save_busy(busy_data)
                    st.rerun()

# ==========================================
# TIMETABLE GENERATION LOGIC
# ==========================================
def generate_timetable_html(tasks, schedule, busy):
    days = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]

    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    week_dates = [(start_of_week + timedelta(days=i)).date() for i in range(7)]

    hours = list(range(6, 23))   # 06:00 → 22:00  (17 khung giờ)
    n_hours = len(hours)
    n_days  = len(days)

    # ── Bước 1: Xây lưới dữ liệu (sig, content_html, css_class) ──────────────
    # sig  : chuỗi đại diện trạng thái ô – dùng để so sánh khi gộp ô liền kề
    # content_html: nội dung hiển thị bên trong ô
    # css_class   : lớp CSS quyết định màu nền
    grid = []
    for hour in hours:
        row = []
        for d_idx, day in enumerate(days):
            sigs, contents, classes = [], [], []

            # Lịch học
            for s in schedule:
                if s["day"] == day:
                    ssh = int(s.get("start", s.get("time", "00:00")).split(":")[0])
                    seh_str = s.get("end", s.get("time", "00:00"))
                    seh = int(seh_str.split(":")[0])
                    sem = int(seh_str.split(":")[1]) if ":" in seh_str else 0
                    end_excl = seh if sem == 0 else seh + 1
                    
                    if "end" not in s: end_excl = ssh + 1

                    if ssh <= hour < end_excl:
                        sigs.append(f"study:{s['subject']}:{s['id']}")
                        contents.append(f"📚 {s['subject']}")
                        classes.append("cell-study")

            # Lịch bận
            for b in busy:
                if b["day"] == day:
                    bsh = int(b["start"].split(":")[0])
                    beh = int(b["end"].split(":")[0])
                    bem = int(b["end"].split(":")[1])
                    end_excl = beh if bem == 0 else beh + 1
                    if bsh <= hour < end_excl:
                        sigs.append(f"busy:{b['title']}:{b['id']}")
                        contents.append(f"🏃 {b['title']}")
                        classes.append("cell-busy")

            # Deadline — mỗi ô deadline dùng sig chứa hour để không bị gộp rowspan
            # Nếu deadline có giờ nằm ngoài khung hiển thị (trước 06:00), hiển thị ở ô 06:00
            for t in tasks:
                if not t.get("completed", False):
                    dl = datetime.fromisoformat(t["deadline"])
                    dl_display_hour = dl.hour if dl.hour >= 6 else 6
                    if dl.date() == week_dates[d_idx] and dl_display_hour == hour:
                        sigs.append(f"deadline:{t['id']}:{hour}")
                        contents.append(f"🚨 DEADLINE: {t['title']} ({t.get('subject', '')})")
                        classes.append("cell-deadline")

            if not sigs:
                row.append(("free", "🌱 Thời gian rảnh", "cell-free"))
            else:
                sig = "|".join(sorted(sigs))
                if "cell-deadline" in classes:
                    css = "cell-deadline"
                elif len(set(classes)) == 1:
                    css = classes[0]
                else:
                    css = "cell-mixed"
                row.append((sig, "<br/>".join(contents), css))
        grid.append(row)

    # ── Bước 2: Tính rowspan theo chiều dọc từng cột ─────────────────────────
    # span_grid[h][d] = số hàng cần gộp (≥1), hoặc 0 nếu ô này đã bị gộp bởi ô trên
    span_grid = [[1] * n_days for _ in range(n_hours)]
    for d_idx in range(n_days):
        h = 0
        while h < n_hours:
            cur_sig = grid[h][d_idx][0]
            span = 1
            while h + span < n_hours and grid[h + span][d_idx][0] == cur_sig:
                span += 1
            span_grid[h][d_idx] = span
            for k in range(1, span):
                span_grid[h + k][d_idx] = 0   # đánh dấu bỏ qua
            h += span

    # ── Bước 3: Render HTML ───────────────────────────────────────────────────
    html = '<div class="timetable-container"><table class="timetable">'
    html += '<tr><th>Giờ \\ Thứ</th>'
    for i, d in enumerate(days):
        html += f'<th>{d}<br/><small>{week_dates[i].strftime("%d/%m")}</small></th>'
    html += '</tr>'

    for h_idx, hour in enumerate(hours):
        time_str = f"{hour:02d}:00"
        html += f'<tr><td class="cell-time">{time_str}</td>'
        for d_idx in range(n_days):
            rowspan = span_grid[h_idx][d_idx]
            if rowspan == 0:
                continue   # ô này đã bị gộp bởi ô phía trên → bỏ qua
            _, content, css = grid[h_idx][d_idx]
            rs   = f' rowspan="{rowspan}"' if rowspan > 1 else ''
            vstyle = ' style="vertical-align:middle; text-align:center;"' if rowspan > 1 else ''
            html += f'<td class="{css}"{rs}{vstyle}>{content}</td>'
        html += '</tr>'

    html += '</table></div>'
    return html

# ==========================================
# TELEGRAM NOTIFICATION BOT & BACKGROUND JOB
# ==========================================
def send_telegram_notification(message: str, token: str, chat_id: str):
    if not token or not chat_id:
        return False, "Chưa cấu hình Telegram Bot Token hoặc Chat ID"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            return True, "Gửi tin nhắn Telegram thành công!"
        else:
            return False, f"Lỗi từ Telegram: HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Lỗi kết nối Telegram API: {str(e)}"

def generate_notification_reminder(tasks_under_48h, free_time_slots, gemini_api_key):
    if not gemini_api_key: return "Bạn có bài tập sắp đến hạn nhưng chưa cấu hình Gemini API."
    try:
        client = genai.Client(api_key=gemini_api_key)
        prompt = f'''
        Bạn là trợ lý học tập. Viết một tin nhắn ngắn gọn, thân thiện bằng tiếng Việt (tối đa 150 từ) để gửi qua Telegram, nhắc nhở sinh viên về các bài tập sắp đến hạn (<48h) và gợi ý khoảng thời gian rảnh trong ngày hôm nay để họ làm bài. Dùng các icon như ⚠️, ⏰, 📅.
        Bài tập sắp đến hạn: {json.dumps(tasks_under_48h, ensure_ascii=False)}
        Thời gian rảnh hôm nay: {free_time_slots}
        '''
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        return response.text.strip()
    except Exception as e:
        return f"Lỗi tạo nội dung từ AI: {e}"

def job_daily_notification_reminder():
    cfg = load_config()
    t_token = cfg.get("telegram_token", "")
    t_uid = cfg.get("telegram_chat_id", "")
    g_key = cfg.get("gemini_api_key", "")
    if not t_token or not t_uid:
        return False, "Chưa cấu hình Telegram Bot Token hoặc Chat ID. Vui lòng thiết lập ở thanh bên."

    tasks = load_data()
    schedule_data = load_schedule()
    busy_data = load_busy()
    now = datetime.now()
    
    tasks_under_48h = []
    for t in tasks:
        if not t.get("completed", False):
            dl = datetime.fromisoformat(t["deadline"])
            diff = (dl - now).total_seconds()
            if 0 < diff <= 48 * 3600:
                tasks_under_48h.append({"title": t["title"], "deadline": t["deadline"]})
                
    if not tasks_under_48h: return True, "Hôm nay không có bài tập nào sắp đến hạn dưới 48h."

    days_str = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
    today_day_str = days_str[now.weekday()]
    free_hours = []
    for hour in range(6, 23):
        is_busy = False
        for s in schedule_data:
            if s["day"] == today_day_str:
                ssh = int(s.get("start", s.get("time", "00:00")).split(":")[0])
                seh_str = s.get("end", s.get("time", "00:00"))
                seh = int(seh_str.split(":")[0])
                sem = int(seh_str.split(":")[1]) if ":" in seh_str else 0
                end_excl = seh if sem == 0 else seh + 1
                if "end" not in s: end_excl = ssh + 1
                if ssh <= hour < end_excl:
                    is_busy = True; break
        if not is_busy:
            for b in busy_data:
                if b["day"] == today_day_str:
                    sh = int(b["start"].split(":")[0])
                    eh = int(b["end"].split(":")[0])
                    if sh <= hour <= eh:
                        is_busy = True; break
        if not is_busy: free_hours.append(f"{hour}:00")
            
    msg = generate_notification_reminder(tasks_under_48h, free_hours, g_key)
    success, result_msg = send_telegram_notification(msg, t_token, t_uid)
    return success, result_msg

# ==========================================
# MAIN CONTENT - VÙNG CHÍNH
# ==========================================
st.title("📚 Assignment Todo App")

# Render confetti if flag is set
if st.session_state.get("show_confetti"):
    is_big = st.session_state.show_confetti == "big"
    banner_text = "🏆 XUẤT SẮC! BẠN ĐÃ DỌN SẠCH TOÀN BỘ DEADLINE TUẦN NÀY!" if is_big else "CONGRATULATIONS"
    font_size = "3rem" if is_big else "5.5rem"
    duration_s = 4.5 if is_big else 2.0
    side_particles = 9 if is_big else 3
    center_particles = 300 if is_big else 120

    html_code = f"""
    <script>
        (function() {{
            var parentDoc = window.parent.document;
            var loadConfetti = function() {{
                var overlay = parentDoc.createElement('div');
                overlay.innerHTML = '{banner_text}';
                overlay.style.position = 'fixed';
                overlay.style.top = '45%';
                overlay.style.left = '50%';
                overlay.style.transform = 'translate(-50%, -50%) scale(0.7)';
                overlay.style.zIndex = '999999';
                overlay.style.background = 'linear-gradient(135deg, #bf953f 0%, #fcf6ba 25%, #b38728 50%, #fbf5b7 75%, #aa771c 100%)';
                overlay.style.webkitBackgroundClip = 'text';
                overlay.style.webkitTextFillColor = 'transparent';
                overlay.style.fontSize = '{font_size}';
                overlay.style.fontWeight = '900';
                overlay.style.letterSpacing = '5px';
                overlay.style.textAlign = 'center';
                overlay.style.width = '100%';
                overlay.style.fontFamily = "'Outfit', 'Inter', 'Arial Black', sans-serif";
                overlay.style.pointerEvents = 'none';
                overlay.style.opacity = '0';
                overlay.style.transition = 'all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                overlay.style.textShadow = '0 10px 30px rgba(186,135,40,0.2)';
                
                parentDoc.body.appendChild(overlay);
                
                requestAnimationFrame(function() {{
                    overlay.style.transform = 'translate(-50%, -50%) scale(1)';
                    overlay.style.opacity = '1';
                }});
                
                setTimeout(function() {{
                    overlay.style.opacity = '0';
                    overlay.style.transform = 'translate(-50%, -50%) scale(1.1)';
                    setTimeout(function() {{
                        if (overlay.parentNode) {{
                            overlay.parentNode.removeChild(overlay);
                        }}
                    }}, 500);
                }}, {duration_s * 1000 - 500});

                window.parent.confetti({{
                    particleCount: {center_particles},
                    spread: 90,
                    origin: {{ y: 0.5 }},
                    colors: ['#bf953f', '#fcf6ba', '#b38728', '#fbf5b7', '#ffc107', '#ff6b6b', '#4d96ff']
                }});
                
                var duration = {duration_s} * 1000;
                var end = Date.now() + duration;

                (function frame() {{
                    window.parent.confetti({{
                        particleCount: {side_particles},
                        angle: 60,
                        spread: 55,
                        origin: {{ x: 0, y: 0.85 }},
                        colors: ['#ffd93d', '#ffc107', '#ffb300', '#ff9800', '#ff6b6b']
                    }});
                    window.parent.confetti({{
                        particleCount: {side_particles},
                        angle: 120,
                        spread: 55,
                        origin: {{ x: 1, y: 0.85 }},
                        colors: ['#ffd93d', '#ffc107', '#ffb300', '#ff9800', '#4d96ff']
                    }});

                    if (Date.now() < end) {{
                        requestAnimationFrame(frame);
                    }}
                }}());
            }};
            if (!window.parent.confetti) {{
                var script = parentDoc.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.5.1/dist/confetti.browser.min.js';
                script.onload = loadConfetti;
                parentDoc.head.appendChild(script);
            }} else {{
                loadConfetti();
            }}
        }})();
    </script>
    """
    components.html(html_code, height=0)
    st.session_state.show_confetti = False
st.markdown("Quản lý bài tập thông minh với **Google Gemini API** & **Lịch trình trực quan**.")

col_title1, col_title2 = st.columns([3, 1])
with col_title2:
    if st.button("Gửi thử thông báo Telegram 🚀", use_container_width=True):
        with st.spinner("Đang xử lý AI & gửi Telegram..."):
            success, msg = job_daily_notification_reminder()
            # Khắc phục lỗi in dài của DeltaGenerator do tính năng magic của Streamlit
            if success:
                st.success(msg)
            else:
                st.error(msg)

data = sort_tasks(load_data())
schedule_data = load_schedule()
busy_data = load_busy()

total_tasks = len(data)
completed_tasks = sum(1 for t in data if t.get("completed", False))
progress_rate = completed_tasks / total_tasks if total_tasks > 0 else 0.0
st.progress(progress_rate, text=f"Tiến độ hoàn thành: {completed_tasks}/{total_tasks} ({progress_rate*100:.1f}%)")

if total_tasks > 0 and completed_tasks == total_tasks:
    st.markdown(
        """
        <div style="background: linear-gradient(135deg, #fffde6 0%, #fff9db 100%); border: 2px solid #f5d033; border-left: 8px solid #ffb300; padding: 20px; border-radius: 12px; margin: 15px 0; box-shadow: 0 4px 15px rgba(255,193,7,0.15); animation: pulse 2s infinite;">
            <h3 style="color: #b38728; margin: 0; font-weight: 900; font-size: 1.3em; display: flex; align-items: center; gap: 10px;">
                🏆 XUẤT SẮC! BẠN ĐÃ DỌN SẠCH TOÀN BỘ DEADLINE TUẦN NÀY!
            </h3>
            <p style="color: #e65100; margin: 8px 0 0 0; font-size: 0.95em; font-weight: bold;">
                Tất cả bài tập đã hoàn thành xuất sắc. Hãy tận hưởng thời gian rảnh của bạn! 🌟🎈
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("---")

# TABS
tab_list, tab_timetable, tab_stats = st.tabs(["📋 Danh sách bài tập", "📅 Thời khóa biểu", "📊 Biểu đồ & Thống kê"])

with tab_timetable:
    st.subheader("Thời khóa biểu & Dự báo thời gian rảnh (Tuần này)")
    st.markdown("Hệ thống tự động tô màu **Xanh nhạt** cho các khoảng thời gian rảnh rỗi dựa trên lịch học, lịch bận và thời gian trống trong tuần (06:00 - 22:00).")
    
    # Hiển thị chú thích
    st.markdown("""
    <div style="display: flex; gap: 15px; margin-bottom: 10px; flex-wrap: wrap; color: #e0e0e0;">
        <div><span style="display:inline-block; width:15px; height:15px; background-color:rgba(21, 101, 192, 0.3); border:1px solid #64b5f6;"></span> 📚 Lịch học cố định</div>
        <div><span style="display:inline-block; width:15px; height:15px; background-color:rgba(239, 108, 0, 0.25); border:1px solid #ffb74d;"></span> 🏃 Việc cá nhân</div>
        <div><span style="display:inline-block; width:15px; height:15px; background-color:rgba(198, 40, 40, 0.3); border:1px solid #ff8a80;"></span> 🎯 Hạn nộp bài</div>
        <div><span style="display:inline-block; width:15px; height:15px; background-color:rgba(46, 125, 50, 0.25); border:1px solid #81c784;"></span> 🌱 Thời gian rảnh</div>
    </div>
    """, unsafe_allow_html=True)
    
    html_timetable = generate_timetable_html(data, schedule_data, busy_data)
    st.markdown(html_timetable, unsafe_allow_html=True)

with tab_list:
    if st.button("🧠 AI Sắp Xếp Thông Minh", type="primary", use_container_width=True):
        if not api_key:
            st.warning("Vui lòng nhập Gemini API Key ở thanh bên để sử dụng tính năng này.")
        else:
            uncompleted = [t for t in data if not t.get("completed", False)]
            if not uncompleted:
                st.info("Tuyệt vời! Bạn không có bài tập nào chưa hoàn thành để sắp xếp.")
            else:
                with st.spinner("AI đang phân tích và đánh giá mức độ ưu tiên..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        current_time = datetime.now().isoformat()
                        
                        prompt = f"""
                        Bạn là trợ lý học tập nghiêm túc. Nhiệm vụ của bạn là chấm điểm ưu tiên (priority_score từ 1–10) cho từng bài tập chưa hoàn thành.
                        
                        ## QUY TẮC CHẤM ĐIỂM ƯU TIÊN:
                        1. **Thời gian thực tế còn lại đến deadline là yếu tố quyết định điểm số.**
                        2. **Đối chiếu lịch học & bận:** Nếu môn học có lịch học định kỳ trong tuần, hạn hoàn thành thực tế phải được tính là TRƯỚC BUỔI HỌC GẦN NHẤT CỦA MÔN ĐÓ ÍT NHẤT 1 NGÀY.
                        
                        ## DỮ LIỆU ĐẦU VÀO:
                        - Thời gian hiện tại: {current_time}
                        - Lịch học cố định: {json.dumps(schedule_data, ensure_ascii=False)}
                        - Danh sách bài tập chưa hoàn thành: {json.dumps(uncompleted, ensure_ascii=False)}
                        
                        ## YÊU CẦU OUTPUT:
                        Với mỗi bài tập, hãy trả về: id, priority_score (1–10), và ai_reason (1 câu tiếng Việt giải thích).
                        """
                        
                        try:
                            config = types.GenerateContentConfig(
                                response_mime_type="application/json",
                                response_schema=list[TaskPriority],
                                temperature=0.2
                            )
                            response = client.models.generate_content(
                                model='gemini-2.5-flash', contents=prompt, config=config
                            )
                            priority_data = json.loads(response.text)
                        except Exception as e:
                            if not backup_api_key:
                                st.error("❌ Gọi AI thất bại và chưa thiết lập Backup API Key.")
                                st.stop()
                            
                            st.toast("⚠️ Gemini đang lỗi, tự động chuyển sang AI Dự phòng...", icon="⚠️")
                            
                            # Cấu hình gọi qua API Groq (OpenAI Compatible)
                            headers = {
                                "Authorization": f"Bearer {backup_api_key}",
                                "Content-Type": "application/json"
                            }
                            backup_prompt = prompt + "\n\nBẮT BUỘC: Output chỉ bao gồm danh sách JSON mảng (Array). Không giải thích thêm, không bọc trong thẻ markdown."
                            data_payload = {
                                "model": "llama-3.3-70b-versatile",
                                "messages": [{"role": "user", "content": backup_prompt}],
                                "temperature": 0.2
                            }
                            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data_payload, timeout=20)
                            resp.raise_for_status()
                            content = resp.json()["choices"][0]["message"]["content"]
                            import re
                            json_match = re.search(r'\[.*\]', content, re.DOTALL)
                            if json_match:
                                content = json_match.group(0)
                            priority_data = json.loads(content)

                        priority_map = {item['id']: item for item in priority_data}
                        
                        for task in data:
                            if task['id'] in priority_map:
                                ai_eval = priority_map[task['id']]
                                task['priority_score'] = ai_eval['priority_score']
                                task['ai_reason'] = ai_eval['ai_reason']
                        
                        data = sort_tasks(data)
                        save_data(data)
                        st.success("✅ Phân tích và sắp xếp hoàn tất!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Đã xảy ra lỗi hệ thống AI: {str(e)}")

    if "pomodoro_task_id" not in st.session_state:
        st.session_state.pomodoro_task_id = None
        st.session_state.pomodoro_end_time = None

    if st.session_state.pomodoro_task_id is not None:
        end_time = st.session_state.pomodoro_end_time
        now = datetime.now()
        remaining = (end_time - now).total_seconds()
        focus_name = next((t["title"] for t in data if t["id"] == st.session_state.pomodoro_task_id), "Bài tập")
        if remaining <= 0:
            for t in data:
                if t["id"] == st.session_state.pomodoro_task_id:
                    t["pomodoros_completed"] = t.get("pomodoros_completed", 0) + 1
                    break
            save_data(data)
            st.session_state.pomodoro_task_id = None
            st.session_state.pomodoro_end_time = None
            st.toast(f"🍅 Hoàn thành 1 phiên Pomodoro cho \"{focus_name}\"!", icon="🎉")
            st.rerun()
        else:
            mins, secs = divmod(int(remaining), 60)
            st.markdown(f"""
            <div class="pomodoro-box">
                <div class="pomodoro-label">🍅 Đang tập trung: <b>{focus_name}</b></div>
                <div class="pomodoro-time">{mins:02d}:{secs:02d}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("⏹️ Dừng Pomodoro", use_container_width=True):
                st.session_state.pomodoro_task_id = None
                st.session_state.pomodoro_end_time = None
                st.rerun()

    if not data:
        st.info("Chưa có bài tập nào. Hãy thêm bài tập mới ở thanh bên trái!")
    else:
        for i, task in enumerate(data):
            is_completed = task.get("completed", False)
            urgency_class, urgency_badge = get_urgency_info(task)
            with st.container(border=True):
                st.markdown(f'<div class="urgency-badge {urgency_class}">{urgency_badge}</div>', unsafe_allow_html=True)
                col_chk, col_info, col_pomo, col_link, col_edit, col_del = st.columns([0.5, 5.0, 1.2, 0.8, 0.6, 0.6], vertical_alignment="center")
                with col_chk:
                    completed_status = st.checkbox("Xong", value=is_completed, key=f"chk_{task['id']}", label_visibility="collapsed")
                    if completed_status != is_completed:
                        task["completed"] = completed_status
                        save_data(data)
                        if completed_status:
                            curr_completed_count = sum(1 for t in data if t.get("completed", False))
                            total_curr_tasks = len(data)
                            
                            if total_curr_tasks > 0 and curr_completed_count == total_curr_tasks:
                                st.session_state.show_confetti = "big"
                                st.toast("🏆 XUẤT SẮC! Đã dọn sạch deadline!", icon="🌟")
                            else:
                                st.session_state.show_confetti = "normal"
                                msg, icon = random.choice(PRAISE_MESSAGES)
                                st.toast(msg, icon=icon)
                        st.rerun()
                with col_info:
                    title_styled = f"~~{task['title']}~~" if is_completed else f"**{task['title']}**"
                    subject_styled = f"~~{task['subject']}~~" if is_completed else task['subject']
                    pomo_count = task.get("pomodoros_completed", 0)
                    pomo_str = f" • 🍅 ×{pomo_count}" if pomo_count > 0 else ""
                    st.markdown(f"📖 {title_styled} - *{subject_styled}*{pomo_str}")
                    countdown_str = format_countdown(task['deadline'])
                    deadline_display = task['deadline'].replace('T', ' ')
                    if "ai_reason" in task and not is_completed:
                        st.caption(f"⏰ Hạn nộp: {deadline_display} • ⏳ {countdown_str}\n\n💡 **AI nhận xét (Điểm {task.get('priority_score', 0)}/10):** {task['ai_reason']}")
                    else:
                        st.caption(f"⏰ Hạn nộp: {deadline_display} • ⏳ {countdown_str}")
                with col_pomo:
                    if not is_completed:
                        if st.button("🍅 Tập trung", key=f"pomo_{task['id']}"):
                            st.session_state.pomodoro_task_id = task['id']
                            st.session_state.pomodoro_end_time = datetime.now() + timedelta(minutes=POMODORO_MINUTES)
                            st.rerun()
                with col_link:
                    task_link = task.get("link", "")
                    if task_link: st.link_button("🔗", task_link, help="Mở link tài liệu")
                with col_edit:
                    if st.button("📝", key=f"edit_{task['id']}", help="Sửa bài tập này"):
                        st.session_state.editing_task_id = task['id']
                        st.rerun()
                with col_del:
                    if st.button("🗑️", key=f"del_{task['id']}", help="Xóa bài tập này"):
                        data = [t for t in data if t['id'] != task['id']]
                        save_data(data)
                        st.rerun()

with tab_stats:
    if not data:
        st.info("Chưa có dữ liệu để thống kê. Hãy thêm bài tập trước!")
    else:
        st.subheader("📈 Tổng quan")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Tổng bài tập", total_tasks)
        m2.metric("Đã hoàn thành", completed_tasks)
        m3.metric("Chưa hoàn thành", total_tasks - completed_tasks)
        total_pomos = sum(t.get("pomodoros_completed", 0) for t in data)
        m4.metric("🍅 Tổng Pomodoro", total_pomos)
        st.markdown("---")
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("##### 📊 Số lượng bài tập chưa hoàn thành theo Môn học")
            subject_counts = {}
            for t in data:
                if not t.get("completed", False):
                    s = t.get("subject", "Khác")
                    subject_counts[s] = subject_counts.get(s, 0) + 1
            
            if not subject_counts:
                st.info("Không có bài tập nào chưa hoàn thành! 🎉")
            else:
                fig_bar = px.bar(
                    x=list(subject_counts.keys()), y=list(subject_counts.values()),
                    labels={"x": "Môn học", "y": "Số lượng bài tập"},
                    color=list(subject_counts.keys()), color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_bar.update_layout(
                    showlegend=False, 
                    margin=dict(t=10, b=10, l=10, r=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e0e0e0"),
                    xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", dtick=1)
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        with chart_col2:
            st.markdown("##### 🥧 Tỷ lệ hoàn thành")
            fig_pie = px.pie(
                names=["Hoàn thành", "Chưa hoàn thành"], values=[completed_tasks, total_tasks - completed_tasks],
                color_discrete_sequence=["#81c784", "#ff8a80"], hole=0.4
            )
            fig_pie.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                legend=dict(font=dict(color="#e0e0e0"))
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        if total_pomos > 0:
            st.markdown("---")
            st.markdown("##### 🍅 Chi tiết Pomodoro theo bài tập")
            pomo_data = [{"Bài tập": t["title"], "Môn": t["subject"], "Phiên 🍅": t.get("pomodoros_completed", 0)} for t in data if t.get("pomodoros_completed", 0) > 0]
            pomo_data.sort(key=lambda x: x["Phiên 🍅"], reverse=True)
            st.dataframe(pomo_data, use_container_width=True, hide_index=True)