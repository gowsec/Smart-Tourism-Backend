from serpapi import GoogleSearch
import json

def get_smart_hotel_recommendations(api_key, location, max_budget_per_night, total_members=4):
    """
    Hàm lấy danh sách khách sạn thông minh dựa trên ngân sách và đánh giá.
    - api_key: Mã Lân đưa.
    - location: Địa điểm (vd: 'Hanoi').
    - max_budget_per_night: Ngân sách tối đa mỗi đêm (để không bị vỡ 20 triệu).
    - total_members: Số thành viên (mặc định là 4 theo Persona gia đình).
    """
    
    # 1. Thiết lập tham số gọi API (Theo đúng engine google_hotels trong ảnh bạn chụp)
    params = {
        "engine": "google_hotels",
        "q": f"Hotels in {location}",
        "check_in_date": "2026-05-01",  # Ngày đi giả định cho Simulation
        "check_out_date": "2026-05-04", # Đi 4 ngày 3 đêm theo Proposal
        "adults": total_members,        # Số người đi theo Persona
        "currency": "VND",
        "hl": "vi",                     # Trả về tiếng Việt cho thân thiện
        "api_key": api_key
    }

    try:
        # 2. Gọi SerpAPI
        search = GoogleSearch(params)
        results = search.get_dict()
        hotels = results.get("properties", [])

        print(f"Số lượng khách sạn tìm thấy: {len(hotels)}") 
        if len(hotels) > 0:
            print("Mẫu dữ liệu khách sạn đầu tiên:", hotels[0].get("rate_per_night"))
        # 3. Logic xử lý dữ liệu "Thông minh" (Smart Logic)
        smart_list = []
        for h in hotels:
            # Lấy giá tiền (đã xử lý lấy số nguyên để dễ tính toán)
            price_info = h.get("rate_per_night", {})
            price = price_info.get("extracted_before_taxes_fees", 0)
            
            # Lọc theo ngân sách: Chỉ lấy những nơi Anh A đủ tiền chi trả
            if 0 < price <= max_budget_per_night:
                smart_list.append({
                    "name": h.get("name"),
                    "rating": h.get("overall_rating", 0),
                    "reviews_count": h.get("reviews", 0),
                    "price_per_night": price,
                    "total_price": price * 3, # Tổng 3 đêm
                    "thumbnail": h.get("images", [{}])[0].get("thumbnail"), # Ảnh cho Frontend
                    "link": h.get("link")
                })

        # 4. Sắp xếp theo Rating cao nhất (Ưu tiên trải nghiệm tốt nhất)
        # Đây chính là phần Recommendation Algorithm bạn đã cam kết trong Proposal
        smart_list.sort(key=lambda x: x['rating'], reverse=True)

        return smart_list[:5] # Trả về Top 5 khách sạn "ngon" nhất

    except Exception as e:
        print(f"Lỗi khi gọi API: {e}")
        return []

# --- PHẦN CHẠY THỬ (Dành cho Quang test máy M2) ---
if __name__ == "__main__":
    MY_KEY = "224510105a5f1f5261d1829e0cb90cd6a67ca3fccd09622fbe568bd5e514c801"
    # Giả sử Anh A dành 10 triệu cho khách sạn trong 3 đêm -> ~3.3 triệu/đêm
    recommendations = get_smart_hotel_recommendations(MY_KEY, "Hà Nội", 99000000)
    
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))