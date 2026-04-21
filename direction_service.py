from serpapi import GoogleSearch

def get_google_maps_directions(api_key, origin, destination, mode="0"):
    """
    Hàm lấy dữ liệu chỉ đường từ Google Maps qua SerpApi.
    
    Tham số:
    api_key (str): Mã Private API Key của bạn.
    origin (str): Điểm xuất phát (Địa chỉ hoặc Tọa độ).
    destination (str): Điểm đến (Địa chỉ hoặc Tọa độ).
    mode (str): Chế độ di chuyển (0: Ô tô, 1: Xe đạp, 2: Đi bộ, 3: Công cộng).
    
    Trả về:
    dict: Dữ liệu JSON chứa thông tin đường đi.
    """
    
    params = {
        "engine": "google_maps_directions",
        "start_addr": origin,
        "end_addr": destination,
        "travel_mode": mode,
        "hl": "vi",  # Trả về tiếng Việt
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        data = search.get_dict()
        return data
    except Exception as e:
        print(f"Lỗi khi gọi API: {e}")
        return None

def print_route_summary(data):
    """Hàm bổ trợ để in kết quả ra màn hình đẹp mắt"""
    if not data or "directions" not in data:
        print("Không tìm thấy dữ liệu đường đi.")
        return

    routes = data.get("directions", [])
    for i, route in enumerate(routes):
        print(f"=== Tuyến đường {i+1}: {route.get('title')} ===")
        print(f"📍 Từ: {data.get('search_parameters', {}).get('start_addr')}")
        print(f"🏁 Đến: {data.get('search_parameters', {}).get('end_addr')}")
        print(f"📏 Khoảng cách: {route.get('distance')}")
        print(f"⏱️ Thời gian: {route.get('duration')}")
        print("-" * 40)

# 