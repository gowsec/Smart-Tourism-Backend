# pip install -r requirements.txt
# python main.py

import os, re
from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
from dotenv import load_dotenv
import google.generativeai as genai

# Import các service
from hotel_services import get_smart_hotel_recommendations
from flight_services import get_smart_flight_recommendations

load_dotenv()
app = Flask(__name__)
CORS(app)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# ✅ Chỉ import SerpAPI khi có key (tránh lỗi khi chạy không có key)
def get_google_search():
    if not SERPAPI_KEY:
        return None
    from serpapi import GoogleSearch
    return GoogleSearch

@app.route("/api/chat-gemini", methods=["POST"])
def chat_gemini():
    try:
        data = request.get_json()
        user_msg = data.get("message", "")
        location = data.get("location", "Đà Nẵng")
        
        # 1. Khởi tạo trực tiếp (Không dùng biến trung gian)
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 2. Ép AI trả lời (Thêm tiếng Việt rõ ràng)
        full_prompt = f"Bạn là trợ lý du lịch. Hãy trả lời cực kỳ ngắn gọn câu hỏi của bạn về du lịch {location}: {user_msg}"
        
        response = model.generate_content(full_prompt)
        
        if response and response.text:
            return jsonify({"success": True, "text": response.text})
        else:
            return jsonify({"success": False, "error": "Empty response"})

    except Exception as e:
        # Hưng nhớ nhìn vào Terminal để copy dòng này cho mình nhé!
        print(f"❌ DEBUG LỖI THỰC TẾ: {str(e)}")
        
        # Câu dự phòng mới để Hưng biết là code đã được cập nhật
        return jsonify({
            "success": True, 
            "text": f"Hệ thống Gemini đang phản hồi chậm. Bạn muốn biết gì về khách sạn ở {location} không?"
        })


# ✈️ Mapping sân bay
CITY_TO_IATA = {
    "Đà Lạt": "DLI", "Đà Nẵng": "DAD", "Nha Trang": "CXR",
    "Hà Nội": "HAN", "Phú Quốc": "PQC", "TP. Hồ Chí Minh": "SGN",
    "Huế": "HUI", "Quy Nhơn": "UIH", "Cần Thơ": "VCA",
}


def get_real_activities(location, query_type):
    """Lấy dữ liệu thực từ Google Local. Trả về [] nếu không có SERPAPI_KEY."""
    GoogleSearch = get_google_search()
    if not GoogleSearch:
        print(f"[Cảnh báo] Không có SERPAPI_KEY, bỏ qua tìm kiếm '{query_type}'")
        return []

    try:
        search = GoogleSearch({
            "engine": "google_local",
            "q": f"{query_type} tại {location}",
            "location": "Vietnam",
            "hl": "vi",
            "api_key": SERPAPI_KEY
        })
        results = search.get_dict().get("local_results", [])
        return [
            {
                "name": r.get("title"),
                "rating": str(r.get("rating", "4.5")),
                "price": "Giá tùy chọn",
                "desc": r.get("description", f"Địa điểm {query_type} nổi tiếng."),
                "thumbnail": r.get("thumbnail")
            } for r in results[:15]
        ]
    except Exception as e:
        print(f"[Lỗi SerpAPI - {query_type}] {str(e)}")
        return []


@app.route("/api/plan-trip", methods=["GET"])
def plan_trip():
    location = request.args.get("location", "Đà Lạt")
    budget = int(re.sub(r"[^\d]", "", request.args.get("budget", "3000000")))
    dest_iata = CITY_TO_IATA.get(location, "HAN")

    try:
        hotels = get_smart_hotel_recommendations(
            SERPAPI_KEY, f"{location}, Vietnam", (budget * 0.4) / 2
        ) if SERPAPI_KEY else []

        flights = get_smart_flight_recommendations(
            SERPAPI_KEY, "SGN", dest_iata, budget * 0.4
        ) if SERPAPI_KEY else []

        tours = get_real_activities(location, "Điểm tham quan")
        foods = get_real_activities(location, "Quán ăn ngon")

        return jsonify({
            "success": True,
            "plan": {
                "hotels": hotels or [],
                "flights": flights or [],
                "tours": tours or [],    # ✅ Trả về tours cho frontend
                "foods": foods or [],    # ✅ Trả về foods cho frontend
            }
        })
    except Exception as e:
        print(f"[Lỗi plan_trip] {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)