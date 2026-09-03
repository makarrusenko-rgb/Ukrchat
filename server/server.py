from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import json
import os
import uuid
import urllib.request
import urllib.error

from calculator import calculate
from mass import convert_mass
from length import convert_length
from volume import convert_volume
from time_converter import convert_time
from speed import convert_speed


app = Flask(__name__)

# ============================================================
# НАЛАШТУВАННЯ ЛОКАЛЬНОГО AI
# ============================================================

# llama.cpp llama-server має бути запущений локально на пристрої.
# Для Android фінальний застосунок запускатиме його автоматично.
LLAMA_URL = os.environ.get(
    "UKRCHAT_LLAMA_URL",
    "http://127.0.0.1:8080"
)

LLAMA_CHAT_URL = LLAMA_URL.rstrip("/") + "/v1/chat/completions"

SYSTEM_PROMPT = """Ти — УкрЧат, локальний AI-помічник.
Відповідай українською мовою, якщо користувач не просить іншу мову.
Будь корисним, точним і зрозумілим.
Ти працюєш локально на пристрої користувача.
Не вигадуй фактів, якщо не знаєш відповіді.
"""


# ============================================================
# ФАЙЛИ
# ============================================================

MEMORY_FILE = "memory.json"
KNOWLEDGE_FILE = "knowledge.json"
HISTORY_FILE = "history.json"
CHATS_FILE = "chats.json"
USAGE_FILE = "usage.json"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# ============================================================
# ЛІМІТИ
# ============================================================

FREE_LIMITS = {
    "photos": 4,
    "videos": 2,
    "documents": 3,
    "messages": 20
}

PREMIUM_LIMITS = {
    "photos": 8,
    "videos": 5,
    "documents": 5,
    "messages": 40
}


# ============================================================
# JSON
# ============================================================

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as error:
            print(f"Помилка читання {filename}: {error}")
    return default


def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


memory = load_json(MEMORY_FILE, {})
knowledge = load_json(KNOWLEDGE_FILE, {})
history = load_json(HISTORY_FILE, [])
chats = load_json(CHATS_FILE, {})
usage = load_json(USAGE_FILE, {})


# ============================================================
# КОРИСТУВАЧ
# ============================================================

def get_user_id():
    user_id = request.headers.get("X-UkrChat-User")

    if not user_id:
        user_id = request.args.get("user_id")

    return user_id or "default"


# ============================================================
# ПЛАН І ЛІМІТИ
# ============================================================

def get_plan():
    # Локальний пристрій = Premium для тестування.
    # Пізніше Android застосунок передаватиме реальний план.
    return "premium"


def get_limits():
    if get_plan() == "premium":
        return PREMIUM_LIMITS
    return FREE_LIMITS


def get_usage():
    global usage

    user_id = get_user_id()
    today = datetime.now().strftime("%Y-%m-%d")

    if user_id not in usage:
        usage[user_id] = {
            "date": today,
            "photos": 0,
            "videos": 0,
            "documents": 0,
            "messages": 0
        }

    if usage[user_id].get("date") != today:
        usage[user_id] = {
            "date": today,
            "photos": 0,
            "videos": 0,
            "documents": 0,
            "messages": 0
        }

    save_json(USAGE_FILE, usage)
    return usage[user_id]


def check_limit(kind):
    current = get_usage()
    limits = get_limits()
    return current.get(kind, 0) < limits.get(kind, 0)


def use_limit(kind):
    current = get_usage()
    current[kind] = current.get(kind, 0) + 1
    save_json(USAGE_FILE, usage)


def limit_message(kind):
    names = {
        "photos": "фото",
        "videos": "відео",
        "documents": "документи",
        "messages": "повідомлення"
    }

    plan_name = (
        "Premium"
        if get_plan() == "premium"
        else "Безкоштовного плану"
    )

    return (
        f"⚠️ Ліміт {plan_name} для {names.get(kind, kind)} "
        "на сьогодні вичерпано."
    )


@app.route("/usage", methods=["GET"])
def usage_route():
    current = get_usage()
    limits = get_limits()

    return jsonify({
        "plan": get_plan(),
        "limits": limits,
        "used": {
            "photos": current.get("photos", 0),
            "videos": current.get("videos", 0),
            "documents": current.get("documents", 0),
            "messages": current.get("messages", 0)
        }
    })


@app.route("/plan", methods=["GET"])
def plan_route():
    current = get_usage()
    limits = get_limits()

    return jsonify({
        "plan": get_plan(),
        "limits": limits,
        "used": {
            "photos": current.get("photos", 0),
            "videos": current.get("videos", 0),
            "documents": current.get("documents", 0),
            "messages": current.get("messages", 0)
        }
    })


# ============================================================
# ЧАТИ
# ============================================================

def save_chats():
    save_json(CHATS_FILE, chats)


def create_chat(title):
    chat_id = str(uuid.uuid4())

    chats[chat_id] = {
        "title": title[:40],
        "messages": []
    }

    save_chats()
    return chat_id


def add_to_chat(chat_id, role, text):
    if not chat_id or chat_id not in chats:
        return

    chats[chat_id]["messages"].append({
        "role": role,
        "text": text
    })

    save_chats()


@app.route("/chats", methods=["GET"])
def get_chats():
    result = []

    for chat_id, chat_data in chats.items():
        result.append({
            "id": chat_id,
            "title": chat_data.get("title", "Новий чат")
        })

    return jsonify(result)


@app.route("/chats/create", methods=["POST"])
def create_chat_route():
    data = request.get_json(silent=True) or {}

    title = str(data.get("title", "Новий чат")).strip()

    if not title:
        title = "Новий чат"

    chat_id = create_chat(title)

    return jsonify({
        "id": chat_id,
        "title": title[:40]
    })


@app.route("/chats/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    if chat_id not in chats:
        return jsonify({
            "error": "Чат не знайдено."
        }), 404

    return jsonify(chats[chat_id])


# ============================================================
# ІСТОРІЯ
# ============================================================

def save_history():
    save_json(HISTORY_FILE, history)


def add_history(role, text):
    history.append({
        "role": role,
        "text": text
    })

    # Щоб файл історії не зростав безмежно.
    if len(history) > 2000:
        del history[:-2000]

    save_history()


# ============================================================
# ЛОКАЛЬНИЙ llama.cpp
# ============================================================

def local_ai(messages, max_tokens=512):
    """
    Надсилає запит до локального llama.cpp llama-server.
    Ніякого Gemini/API/cloud тут немає.
    """

    payload = {
        "messages": messages,
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": max_tokens,
        "stream": False
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        LLAMA_CHAT_URL,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as response:
            raw = response.read().decode("utf-8")
            result = json.loads(raw)

        choices = result.get("choices", [])

        if not choices:
            return "Локальний AI не повернув відповідь."

        message = choices[0].get("message", {})
        answer = message.get("content", "")

        if isinstance(answer, list):
            answer = "".join(
                str(item.get("text", ""))
                if isinstance(item, dict)
                else str(item)
                for item in answer
            )

        answer = str(answer).strip()

        return answer or "Локальний AI повернув порожню відповідь."

    except urllib.error.URLError as error:
        print("llama.cpp недоступний:", error)
        return (
            "⚠️ Локальний AI зараз не запущений.\n\n"
            "У фінальній Android-версії УкрЧат запускатиме "
            "AI-сервер автоматично."
        )

    except Exception as error:
        print("Помилка локального AI:", error)
        return "⚠️ Не вдалося отримати відповідь від локального AI."


def build_ai_messages(chat_id, user_text):
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    # Пам'ять
    if memory:
        memory_text = json.dumps(
            memory,
            ensure_ascii=False
        )

        messages.append({
            "role": "system",
            "content": "Пам'ять користувача:\n" + memory_text
        })

    # Вивчені користувачем факти
    if knowledge:
        recent_knowledge = list(knowledge.items())[-100:]

        knowledge_text = "\n".join(
            f"{key}: {value}"
            for key, value in recent_knowledge
        )

        messages.append({
            "role": "system",
            "content": "База знань УкрЧату:\n" + knowledge_text
        })

    # Контекст поточного чату
    if chat_id in chats:
        chat_messages = chats[chat_id].get("messages", [])

        for item in chat_messages[-20:]:
            role = item.get("role")

            if role not in ("user", "assistant"):
                continue

            content = item.get("text", "")

            if not content:
                continue

            messages.append({
                "role": role,
                "content": content
            })

    messages.append({
        "role": "user",
        "content": user_text
    })

    return messages


# ============================================================
# ДОКУМЕНТИ
# ============================================================

def read_text_document(path):
    extension = os.path.splitext(path)[1].lower()

    if extension not in (".txt", ".md", ".csv", ".json", ".py"):
        return None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Захист від надто великого контексту.
    return text[:30000]


# ============================================================
# ГОЛОВНА СТОРІНКА
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# ОСНОВНИЙ ЧАТ
# ============================================================

@app.route("/chat", methods=["POST"])
def chat():
    chat_id = None

    if request.is_json:
        data = request.get_json(silent=True) or {}
        chat_id = data.get("chat_id")
    else:
        chat_id = request.form.get("chat_id")

    # --------------------------------------------------------
    # ДОКУМЕНТ
    # --------------------------------------------------------

    if "document" in request.files:
        if not check_limit("documents"):
            return jsonify({
                "reply": limit_message("documents")
            }), 429

        document = request.files["document"]

        if not document.filename:
            return jsonify({
                "reply": "Документ не вибрано."
            })

        original_name = document.filename
        extension = os.path.splitext(original_name)[1].lower()

        filename = str(uuid.uuid4()) + extension
        document_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        document.save(document_path)
        use_limit("documents")

        prompt = request.form.get(
            "message",
            "Проаналізуй цей документ."
        ).strip()

        document_text = read_text_document(document_path)

        if document_text is None:
            answer = (
                "⚠️ УкрЧат 1 поки що не має вбудованого "
                "читання цього формату документа в локальному режимі.\n\n"
                "Перший локальний реліз підтримує текстовий AI, "
                "а підтримку PDF/DOCX можна додати наступним модулем."
            )
        else:
            combined_prompt = (
                f"{prompt}\n\n"
                f"Назва документа: {original_name}\n\n"
                f"Текст документа:\n{document_text}"
            )

            messages = build_ai_messages(
                chat_id,
                combined_prompt
            )

            answer = local_ai(messages)

        add_to_chat(
            chat_id,
            "user",
            "[Документ] " + original_name
        )

        add_to_chat(
            chat_id,
            "assistant",
            answer
        )

        add_history(
            "user",
            "[Документ] " + original_name
        )

        add_history(
            "assistant",
            answer
        )

        try:
            os.remove(document_path)
        except Exception:
            pass

        return jsonify({
            "reply": answer
        })

    # --------------------------------------------------------
    # ФОТО
    # --------------------------------------------------------

    if "image" in request.files:
        if not check_limit("photos"):
            return jsonify({
                "reply": limit_message("photos")
            }), 429

        image = request.files["image"]

        if not image.filename:
            return jsonify({
                "reply": "Фото не вибрано."
            })

        extension = os.path.splitext(
            image.filename
        )[1].lower() or ".jpg"

        filename = str(uuid.uuid4()) + extension
        image_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        image.save(image_path)
        use_limit("photos")

        prompt = request.form.get(
            "message",
            "Проаналізуй це зображення."
        ).strip()

        add_to_chat(
            chat_id,
            "user",
            "[Фото] " + prompt
        )

        answer = (
            "⚠️ Фото отримано, але поточна мала модель "
            "УкрЧату 1 є текстовою і не має зору.\n\n"
            "Підтримку vision-моделі можна додати пізніше "
            "без зміни основної архітектури."
        )

        add_to_chat(
            chat_id,
            "assistant",
            answer
        )

        add_history(
            "user",
            "[Фото] " + prompt
        )

        add_history(
            "assistant",
            answer
        )

        try:
            os.remove(image_path)
        except Exception:
            pass

        return jsonify({
            "reply": answer
        })

    # --------------------------------------------------------
    # ВІДЕО
    # --------------------------------------------------------

    if "video" in request.files:
        if not check_limit("videos"):
            return jsonify({
                "reply": limit_message("videos")
            }), 429

        video = request.files["video"]

        if not video.filename:
            return jsonify({
                "reply": "Відео не вибрано."
            })

        extension = os.path.splitext(
            video.filename
        )[1].lower() or ".mp4"

        filename = str(uuid.uuid4()) + extension
        video_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        video.save(video_path)
        use_limit("videos")

        prompt = request.form.get(
            "message",
            "Проаналізуй це відео."
        ).strip()

        add_to_chat(
            chat_id,
            "user",
            "[Відео] " + prompt
        )

        answer = (
            "⚠️ Відео отримано, але УкрЧат 1 "
            "поки що використовує малу текстову локальну модель "
            "без аналізу відео."
        )

        add_to_chat(
            chat_id,
            "assistant",
            answer
        )

        add_history(
            "user",
            "[Відео] " + prompt
        )

        add_history(
            "assistant",
            answer
        )

        try:
            os.remove(video_path)
        except Exception:
            pass

        return jsonify({
            "reply": answer
        })

    # --------------------------------------------------------
    # ТЕКСТ
    # --------------------------------------------------------

    data = request.get_json(silent=True) or {}

    text = str(data.get("message", "")).strip()

    if not text:
        return jsonify({
            "reply": "Напиши повідомлення."
        })

    if not check_limit("messages"):
        return jsonify({
            "reply": limit_message("messages")
        }), 429

    use_limit("messages")

    lower = text.lower()

    add_to_chat(
        chat_id,
        "user",
        text
    )

    add_history(
        "user",
        text
    )

    # --------------------------------------------------------
    # СТВОРЕННЯ ЗОБРАЖЕННЯ
    # --------------------------------------------------------

    if lower.startswith("створи зображення"):
        answer = (
            "⚠️ Генерація зображень не використовує Gemini "
            "у локальному УкрЧаті 1.\n\n"
            "Її можна додати окремим локальним модулем пізніше."
        )

        add_to_chat(
            chat_id,
            "assistant",
            answer
        )

        add_history(
            "assistant",
            answer
        )

        return jsonify({
            "reply": answer
        })

    # --------------------------------------------------------
    # ЧАС
    # --------------------------------------------------------

    if lower == "час":
        answer = datetime.now().strftime("%H:%M:%S")

    # --------------------------------------------------------
    # ДАТА
    # --------------------------------------------------------

    elif lower == "дата":
        answer = datetime.now().strftime("%d.%m.%Y")

    # --------------------------------------------------------
    # ІМ'Я
    # --------------------------------------------------------

    elif lower.startswith("мене звати "):
        memory["name"] = text[11:].strip()

        save_json(
            MEMORY_FILE,
            memory
        )

        answer = (
            "Приємно познайомитися, "
            + memory["name"]
            + "!"
        )

    elif lower == "як мене звати":
        answer = memory.get(
            "name",
            "Я ще не знаю твого імені."
        )

    # --------------------------------------------------------
    # НАВЧАННЯ
    # --------------------------------------------------------

    elif lower.startswith("навчи ") and "=" in text:
        key, value = text[6:].split("=", 1)

        knowledge[key.strip().lower()] = value.strip()

        save_json(
            KNOWLEDGE_FILE,
            knowledge
        )

        answer = "Запам'ятав!"

    # --------------------------------------------------------
    # БАЗА ЗНАНЬ
    # --------------------------------------------------------

    elif lower in knowledge:
        answer = knowledge[lower]

    # --------------------------------------------------------
    # КОНВЕРТЕРИ / КАЛЬКУЛЯТОР
    # --------------------------------------------------------

    else:
        answer = None

        for converter in (
            convert_volume,
            convert_speed,
            convert_time,
            convert_length,
            convert_mass
        ):
            try:
                result = converter(text)
            except Exception:
                result = None

            if result is not None:
                answer = result
                break

        if answer is None:
            try:
                result = calculate(text)
            except Exception:
                result = None

            if result is not None:
                answer = result

        # ----------------------------------------------------
        # ЛОКАЛЬНИЙ AI
        # ----------------------------------------------------

        if answer is None:
            messages = build_ai_messages(
                chat_id,
                text
            )

            answer = local_ai(messages)

    # --------------------------------------------------------
    # ЗБЕРЕЖЕННЯ ВІДПОВІДІ
    # --------------------------------------------------------

    if answer is None:
        answer = "Не вдалося отримати відповідь."

    # Не записуємо технічні помилки як знання.
    if not answer.startswith("⚠️"):
        knowledge[lower] = answer

        # Обмежуємо локальну базу знань.
        if len(knowledge) > 1000:
            first_key = next(iter(knowledge))
            del knowledge[first_key]

        save_json(
            KNOWLEDGE_FILE,
            knowledge
        )

    add_to_chat(
        chat_id,
        "assistant",
        answer
    )

    add_history(
        "assistant",
        answer
    )

    return jsonify({
        "reply": answer
    })


# ============================================================
# ЗАПУСК
# ============================================================

if __name__ == "__main__":
    print("🇺🇦 УкрЧат")
    print("Локальний Flask-сервер запущено.")
    print("AI:", LLAMA_CHAT_URL)

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
