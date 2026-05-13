from serpapi import GoogleSearch
from datetime import datetime, timedelta

def get_hotel_image_fallback(hotel_name, location, api_key):
    """
    Tìm ảnh thật từ Google Images nếu dữ liệu Google Hotels bị thiếu.
    """
    params = {
        "engine": "google_images",
        "q": f"{hotel_name} {location} exterior photo",
        "api_key": api_key
    }
    try:
        res = GoogleSearch(params).get_dict()
        images = res.get("images_results", [])
        # Lấy ảnh gốc đầu tiên tìm được
        return images[0].get("original") or images[0].get("thumbnail")
    except:
        return None

def get_smart_hotel_recommendations(api_key, location, total_hotel_budget, num_days, passengers, departure_date=None):
    num_nights = num_days - 1 if num_days > 1 else 1
    max_per_night = total_hotel_budget / num_nights
    
    # Cấu hình Bayesian để lọc khách sạn "cùi" (theo ThuatToanDeXuat.py)
    MIN_REVIEWS = 50
    AVG_RATING = 4.2

    try:
        check_in = datetime.strptime(departure_date, "%Y-%m-%d")
    except:
        check_in = datetime.today() + timedelta(days=14)
    check_out = check_in + timedelta(days=num_nights)

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
            # 1. Lấy giá (Hỗ trợ nhiều format của SerpAPI)
            rate = h.get("rate_per_night", {})
            price = rate.get("extracted_lowest") or rate.get("extracted_before_taxes_fees") or 0
            
            # 2. Xử lý ảnh đa tầng (Logic cũ của bạn)
            img = h.get("thumbnail") or h.get("featured_image")
            if not img and h.get("images"):
                first_img = h.get("images")[0]
                img = first_img.get("thumbnail") if isinstance(first_img, dict) else first_img

            # 🔥 CỨU CÁNH: Nếu vẫn không có ảnh, search Google Images ngay
            if not img:
                img = get_hotel_image_fallback(h.get("name"), location, api_key)

            rating = h.get("overall_rating", 0)
            reviews = h.get("reviews", 0)

            if price > 0:
                # --- TÍNH ĐIỂM (SCORE) ĐỂ TRÁNH ĐỒ CÙI ---
                # Quality Score: Bayesian Rating
                b_rating = (reviews / (reviews + MIN_REVIEWS)) * rating + (MIN_REVIEWS / (reviews + MIN_REVIEWS)) * AVG_RATING
                quality_score = (b_rating / 5.0) * 10

                # Price Score: Ưu tiên sát ngân sách để lấy đồ xịn
                if price <= max_per_night:
                    price_score = (price / max_per_night) * 10
                else:
                    price_score = 0

                # Trọng số: 70% Chất lượng, 30% Độ xịn
                final_score = (quality_score * 0.7) + (price_score * 0.3)

                coords = h.get("gps_coordinates", {})
                smart_list.append({
                    "name": h.get("name"),
                    "rating": rating,
                    "price_per_night": price,
                    "total_price": price * num_nights,
                    # Fallback cuối cùng sang placehold.co (không dùng via.placeholder vì bị chặn)
                    "thumbnail": img or "https://placehold.co/400x300?text=S-Trip+Hotel",
                    "link": h.get("link"),
                    "lat": coords.get("latitude"),
                    "lng": coords.get("longitude"),
                    "score": final_score
                })
        
        # Lọc những KS trong ngân sách
        valid_hotels = [h for h in smart_list if 0 < h["price_per_night"] <= max_per_night]
        
        if valid_hotels:
            # Sắp xếp theo ĐIỂM SCORE (Ưu tiên hàng xịn, giá sát ngân sách)
            valid_hotels.sort(key=lambda x: x['score'], reverse=True)
            return valid_hotels[:5]
        else:
            # Nếu lủng ngân sách, lấy 5 cái rẻ nhất
            smart_list.sort(key=lambda x: x['price_per_night'] if x['price_per_night'] > 0 else float('inf'))
            return smart_list[:5]
            
    except Exception as e:
        print(f"Lỗi Hotel Service: {e}")
        return []