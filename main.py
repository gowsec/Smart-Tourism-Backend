# pip install -r requirements.txt
# python main.py

import os, re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai

# Import các service
from hotel_services import get_smart_hotel_recommendations
from flight_services import get_smart_flight_recommendations
from direction_service import get_all_modes_directions

load_dotenv()
app = Flask(__name__)
CORS(app)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "") # ae5111d31011d5745569d2607729352381b0093772e1620e67a59b46cac49187
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

        search_data = search.get_dict()

        if "error" in search_data:
            print("🚨 LỖI SERPAPI:", search_data["error"])

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
                "lat": coords.get("latitude"),
                "lng": coords.get("longitude"),
                "place_id": r.get("place_id") or r.get("data_id", ""),  # ← dùng cho reviews chính xác
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



@app.route("/api/reviews", methods=["GET"])
def get_place_reviews():
    place    = request.args.get("place", "")
    place_id = request.args.get("place_id", "")

    if place_id and not (place_id.startswith("ChIJ") or "0x" in place_id):
        place_id = ""

    if not place and not place_id:
        return jsonify({"success": False, "reviews": []})
    
    GoogleSearch = get_google_search()
    if not GoogleSearch:
        return jsonify({"success": True, "reviews": []})
        
    try:
        reviews = []
        total_reviews = 0
        
        # 1. FALLBACK: NẾU KHÔNG CÓ PLACE_ID, TÌM BẰNG TÊN TRƯỚC
        if not place_id and place:
            search_data = GoogleSearch({"engine": "google_maps", "q": place, "hl": "vi", "api_key": SERPAPI_KEY}).get_dict()
            place_results = search_data.get("place_results", {})
            
            # Ưu tiên 1: Cố lấy ID từ place_results
            place_id = place_results.get("place_id") or place_results.get("data_id", "")
            
            # Ưu tiên 2: Cố lấy ID từ local_results (hay gặp ở Điểm tham quan/Ăn uống)
            if not place_id:
                local_results = search_data.get("local_results", [])
                if local_results and len(local_results) > 0:
                    place_id = local_results[0].get("place_id") or local_results[0].get("data_id", "")
            
            # Ưu tiên 3 (Dành cho Khách sạn): Không có ID nhưng Maps trả sẵn review thì hốt luôn
            if not place_id and "reviews" in place_results:
                reviews = place_results.get("reviews", [])
                total_reviews = place_results.get("reviews_unparsed", len(reviews))

        # 2. KHI ĐÃ CÓ ID (Do Frontend truyền hoặc do Fallback tìm ra)
        if place_id:
            params = {"engine": "google_maps_reviews", "place_id": place_id, "hl": "vi", "api_key": SERPAPI_KEY}
            data = GoogleSearch(params).get_dict()
            
            # Nếu request không bị lỗi
            if "error" not in data:
                reviews = data.get("reviews", [])
                total_reviews = data.get("place_info", {}).get("reviews") or len(reviews)

        # 3. CHUẨN HÓA DỮ LIỆU TRẢ VỀ FRONTEND
        result  = [{
            "user":    r.get("user", {}).get("name", "Ẩn danh"),
            "avatar":  r.get("user", {}).get("thumbnail"),
            "rating":  r.get("rating"),
            "content": r.get("snippet", "") or r.get("text", ""),
            "date":    r.get("date", ""),
            "photos":  r.get("images", [])
        } for r in reviews]
        
        return jsonify({"success": True, "reviews": result, "total": total_reviews})
        
    except Exception as e:
        print(f"[Lỗi reviews] {e}")
        return jsonify({"success": False, "reviews": [], "error": str(e)})


@app.route("/api/images", methods=["GET"])
def get_place_images():
    place = request.args.get("place", "")
    # Frontend truyền lên là place_id, nhưng ta sẽ xử lý nó như data_id
    passed_id = request.args.get("place_id", "")
    
    # Engine google_maps_photos BẮT BUỘC dùng định dạng ID là 0x...:0x...
    # Nếu ID gửi lên là dãy số hoặc ChIJ..., ta xóa đi để bắt Fallback tìm lại đúng chuẩn 0x...
    data_id = passed_id if passed_id and "0x" in passed_id else ""

    if not place and not data_id:
        return jsonify({"success": False, "images": []})
        
    GoogleSearch = get_google_search()
    if not GoogleSearch:
        return jsonify({"success": True, "images": []})
        
    try:
        photos = []
        
        # 1. FALLBACK: TÌM LẠI ĐÚNG DATA_ID CHUẨN (0x...:0x...)
        if not data_id and place:
            search_data = GoogleSearch({"engine": "google_maps", "q": place, "hl": "vi", "api_key": SERPAPI_KEY}).get_dict()
            place_results = search_data.get("place_results", {})
            
            # Lấy data_id thay vì place_id
            data_id = place_results.get("data_id")
            
            if not data_id:
                local_results = search_data.get("local_results", [])
                if local_results and len(local_results) > 0:
                    data_id = local_results[0].get("data_id")

        # 2. GỌI ENGINE LẤY ẢNH VỚI THAM SỐ `data_id`
        if data_id:
            params = {
                "engine": "google_maps_photos", 
                "data_id": data_id, # <--- SỬA CHÍNH MẠNG Ở ĐÂY: API này đòi tên tham số là data_id
                "hl": "vi", 
                "api_key": SERPAPI_KEY
            }
            data = GoogleSearch(params).get_dict()
            photos = data.get("photos", [])
            
        images = [p.get("image") or p.get("thumbnail") for p in photos if p.get("image") or p.get("thumbnail")]
        return jsonify({"success": True, "images": images[:15]}) 
        
    except Exception as e:
        print(f"[Lỗi images] {e}")
        return jsonify({"success": False, "images": []})

if __name__ == "__main__":
    app.run(port=5000, debug=True)