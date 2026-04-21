from serpapi import GoogleSearch
import json

def get_smart_flight_recommendations(api_key, departure_id, arrival_id, max_total_budget):
    """
    Hàm lấy danh sách vé máy bay khứ hồi thông minh.
    - departure_id: Mã sân bay đi (vd: 'SGN' - Tân Sơn Nhất).
    - arrival_id: Mã sân bay đến (vd: 'HAN' - Nội Bài).
    - max_total_budget: Ngân sách tối đa cho TỔNG vé máy bay của cả gia đình.
    """
    
    # 1. Thiết lập tham số (Dùng engine google_flights theo Proposal)
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": "2026-05-01", # Ngày đi khớp với khách sạn
        "return_date": "2026-05-04",   # Ngày về (4 ngày 3 đêm)
        "currency": "VND",
        "hl": "vi",
        "api_key": api_key
    }

    try:
        # 2. Gọi SerpAPI
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Google Flights trả về kết quả tốt nhất trong 'best_flights'
        flights = results.get("best_flights", [])
        
        print(f"Số lượng chuyến bay tìm thấy: {len(flights)}")

        # 3. Logic xử lý dữ liệu "Thông minh" (Smart Logic)
        smart_flights = []
        for f in flights:
            price = f.get("price", 0)
            
            # Lọc theo ngân sách của Anh A
            if 0 < price <= max_total_budget:
                # Lấy thông tin hãng bay và thời gian từ chặng đầu tiên
                first_leg = f.get("flights", [{}])[0]
                
                smart_flights.append({
                    "airline": first_leg.get("airline"),
                    "flight_number": first_leg.get("flight_number"),
                    "departure": first_leg.get("departure_airport", {}).get("name"),
                    "arrival": first_leg.get("arrival_airport", {}).get("name"),
                    "total_duration": f.get("total_duration"), # Tổng thời gian bay
                    "price": price,
                    "type": f.get("type"), # Khứ hồi hay một chiều
                    "thumbnail": first_leg.get("airline_logo") # Logo hãng bay cho UI
                })

        # 4. Sắp xếp theo giá rẻ nhất (Tối ưu ngân sách cho Anh A)
        smart_flights.sort(key=lambda x: x['price'])

        return smart_flights[:3] # Trả về 3 lựa chọn tốt nhất

    except Exception as e:
        print(f"Lỗi khi gọi API Flight: {e}")
        return []

# # --- PHẦN CHẠY THỬ (Dành cho Quang test máy M2) ---
# if __name__ == "__main__":
#     MY_KEY = "224510105a5f1f5261d1829e0cb90cd6a67ca3fccd09622fbe568bd5e514c801"
    
#     # Giả sử Anh A dành tối đa 8 triệu cho vé máy bay khứ hồi cả nhà
#     # SGN: Sân bay Tân Sơn Nhất, HAN: Sân bay Nội Bài
#     flight_results = get_smart_flight_recommendations(MY_KEY, "SGN", "HAN", 8000000)
    
#     print(json.dumps(flight_results, indent=2, ensure_ascii=False))