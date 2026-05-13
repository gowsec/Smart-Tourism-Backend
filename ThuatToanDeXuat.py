import math
import re

W_DISTANCE = 0.5
W_PRICE = 0.15
W_RATING = 0.35
MIN_REVIEWS = 50
SYSTEM_AVG_RATING = 4.2
MAX_DISTANCE_KM = 30 

def haversine(lat1, lon1, lat2, lon2):
    """Tính khoảng cách đường chim bay giữa 2 tọa độ"""
    if not all([lat1, lon1, lat2, lon2]): return 5.0
    R = 6371
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    dphi = math.radians(float(lat2) - float(lat1))
    dlambda = math.radians(float(lon2) - float(lon1))
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bayesian_rating(r, v):
    """Tính điểm rating dựa trên số lượng review để đảm bảo độ tin cậy"""
    try:
        r, v = float(r), int(v)
    except:
        r, v = 4.0, 50
    return (v / (v + MIN_REVIEWS)) * r + (MIN_REVIEWS / (v + MIN_REVIEWS)) * SYSTEM_AVG_RATING

def extract_price(price_str, default_price):
    if not price_str or price_str == "Giá tùy chọn": return default_price
    nums = re.findall(r'\d+', str(price_str).replace('.', '').replace(',', ''))
    return int(nums[0]) if nums else default_price

def apply_recommendation_algorithm(hotels, tours, foods, budget):
    """Hàm điều phối chính để chấm điểm và sắp xếp lại danh sách địa điểm"""
    if not hotels or not tours: 
        return hotels, tours, foods
    
    # Lấy tọa độ khách sạn đầu tiên làm tâm điểm hành trình
    center_lat = hotels[0].get("lat")
    center_lng = hotels[0].get("lng")
    ideal_price = (budget * 0.2) / 3 

    def calculate_score(item, category_default_price):
        # 1. Điểm Rating (Bayesian)
        r_score = (bayesian_rating(item.get("rating", 4.0), item.get("reviews", 50)) / 5.0) * 10
        # 2. Điểm Khoảng cách
        dist = haversine(center_lat, center_lng, item.get("lat"), item.get("lng"))
        d_score = max(0, 10 - (dist / MAX_DISTANCE_KM) * 10)
        # 3. Điểm Giá
        price = extract_price(item.get("price"), category_default_price)
        p_score = 10 if price <= ideal_price else max(0, 10 - ((price - ideal_price) / 100000 * 2.5))
        
        final_score = (d_score * W_DISTANCE) + (p_score * W_PRICE) + (r_score * W_RATING)
        item['ai_score'] = final_score
        return final_score

    for t in tours: calculate_score(t, 100000)
    tours.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
    for f in foods: calculate_score(f, 150000)
    foods.sort(key=lambda x: x.get('ai_score', 0), reverse=True)

    return hotels, tours, foods