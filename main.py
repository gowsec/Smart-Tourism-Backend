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
from direction_service import get_all_modes_directions

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
        print(f"❌ DEBUG LỖI THỰC TẾ: {str(e)}")
  
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
        processed_results = []
        for r in results:
            # 1. Tìm ảnh ở nhiều nguồn khác nhau trong dữ liệu API
            # Thử lấy 'thumbnail', nếu không có thì lấy 'featured_image'
            img_url = r.get("thumbnail") or r.get("featured_image")
            
            # 2. Nếu hoàn toàn không có ảnh, dùng ảnh mặc định (Placeholder)
            if not img_url:
                img_url = "https://via.placeholder.com/300x200?text=S-Trip+No+Image"

            coords = r.get("gps_coordinates", {})
            processed_results.append({
                "name": r.get("title"),
                "rating": str(r.get("rating", "4.5")),
                "price": "Giá tùy chọn",
                "desc": r.get("description", f"Địa điểm {query_type} nổi tiếng."),
                "thumbnail": img_url,
                "lat": coords.get("latitude"),   # Google Maps coordinates
                "lng": coords.get("longitude"),  # → MapBubble dùng trực tiếp
            })
            
        return processed_results[:15]

    except Exception as e:
        print(f"[Lỗi SerpAPI - {query_type}] {str(e)}")
        return []


@app.route("/api/directions", methods=["GET"])
def directions():
    """
    Lấy khoảng cách + thời gian giữa 2 điểm cho tất cả phương tiện.
    Query params:
      origin      — tên hoặc "lat,lng"
      destination — tên hoặc "lat,lng"
    """
    origin      = request.args.get("origin", "")
    destination = request.args.get("destination", "")
    if not origin or not destination:
        return jsonify({"success": False, "error": "Thiếu origin hoặc destination"}), 400
    try:
        modes = get_all_modes_directions(SERPAPI_KEY, origin, destination)
        return jsonify({"success": True, "modes": modes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/plan-trip", methods=["GET"])
def plan_trip():
    location = request.args.get("location", "Đà Lạt")
    budget_raw = request.args.get("budget", "5000000")
    budget = int(re.sub(r"[^\d]", "", budget_raw))
    departure_date = request.args.get("departure_date", "2026-05-30")

    # Xử lý chuỗi "4 ngày 3 đêm" để lấy số ngày chuẩn
    days_raw = request.args.get("days", "3")
    match = re.search(r'\d+', days_raw)
    num_days = int(match.group()) if match else 3
    
    passengers = int(request.args.get("passengers", 1))
    
    # Phân bổ ngân sách (40% cho mỗi dịch vụ)
    hotel_budget = budget * 0.4 
    flight_budget = budget * 0.4

    try:
        # 1. Tìm Khách sạn
        hotels = get_smart_hotel_recommendations(SERPAPI_KEY, location, hotel_budget, num_days, passengers, departure_date)
        
        # 2. Tìm Vé máy bay
        flights = get_smart_flight_recommendations(SERPAPI_KEY, "SGN", CITY_TO_IATA.get(location, "HAN"), flight_budget, num_days, passengers, departure_date)

        # 3. Lấy lại Tours và Foods đã mất
        tours = get_real_activities(location, "Điểm tham quan")
        foods = get_real_activities(location, "Quán ăn ngon")

        return jsonify({
            "success": True,
            "plan": {
                "hotels": hotels or [],
                "flights": flights or [],
                "tours": tours or [],
                "foods": foods or []
            }
        })
    except Exception as e:
        print(f"Lỗi plan_trip: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)