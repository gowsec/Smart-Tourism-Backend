from serpapi import GoogleSearch
from datetime import datetime, timedelta

def get_smart_hotel_recommendations(api_key, location, total_hotel_budget, num_days, passengers, departure_date=None):
    # Tính toán số đêm thực tế và ngân sách mỗi đêm
    num_nights = num_days - 1 if num_days > 1 else 1
    max_per_night = total_hotel_budget / num_nights
    
    check_in = datetime.strptime(departure_date, "%Y-%m-%d")
    check_out = check_in + timedelta(days=num_days - 1)

    params = {
        "engine": "google_hotels",
        "q": f"Hotels in {location}, Vietnam",
        "check_in_date": check_in.strftime("%Y-%m-%d"),
        "check_out_date": check_out.strftime("%Y-%m-%d"),
        "adults": passengers,
        "currency": "VND",
        "hl": "vi",
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        hotels = search.get_dict().get("properties", [])
        smart_list = []
        for h in hotels:
            price = h.get("rate_per_night", {}).get("extracted_before_taxes_fees", 0)
            
            # Xử lý ảnh thumbnail fallback
            img = h.get("thumbnail") or h.get("featured_image")
            if not img and h.get("images"):
                img = h.get("images")[0].get("thumbnail") if isinstance(h.get("images")[0], dict) else h.get("images")[0]

            # ✅ FIX: Lấy tọa độ GPS từ SerpAPI — dùng trực tiếp, không cần geocode lại
            coords = h.get("gps_coordinates", {})
            lat = coords.get("latitude")
            lng = coords.get("longitude")

            if 0 < price <= max_per_night:
                smart_list.append({
                    "name": h.get("name"),
                    "rating": h.get("overall_rating", 0),
                    "price_per_night": price,
                    "total_price": price * num_nights,
                    "thumbnail": img or "https://via.placeholder.com/300",
                    "link": h.get("link"),
                    "lat": lat,
                    "lng": lng,
                })
        
        smart_list.sort(key=lambda x: x['price_per_night'], reverse=True)
        return smart_list[:3]
    except Exception as e:
        print(f"Lỗi Hotel: {e}")
        return []