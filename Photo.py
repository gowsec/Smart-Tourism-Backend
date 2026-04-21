from serpapi import GoogleSearch

def search_google_maps(keyword, location_coords, api_key, lang="vi"):
    """
    Hàm tìm kiếm địa điểm trên Google Maps qua SerpApi.
    
    Args:
        keyword (str): Từ khóa tìm kiếm (VD: 'coffee shop').
        location_coords (str): Tọa độ theo định dạng '@lat,long,zoomz' (VD: '@10.762622,106.660172,15z').
        api_key (str): API Key của bạn từ SerpApi.
        lang (str): Ngôn ngữ kết quả trả về. mặc định là 'vi'.
    """
    params = {
        "engine": "google_maps",
        "q": keyword,
        "ll": location_coords,
        "type": "search",
        "hl": lang,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        local_results = results.get("local_results", [])

        print(f"--- Tìm thấy {len(local_results)} địa điểm cho từ khóa '{keyword}' ---\n")

        for place in local_results:
            name = place.get("title")
            address = place.get("address")
            rating = place.get("rating", "N/A")
            reviews = place.get("reviews", 0)
            
            print(f" Tên: {name}")
            print(f" Địa chỉ: {address}")
            print(f" Đánh giá: {rating} ({reviews} đánh giá)")
            print("-" * 30)
            
        return local_results

    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        return None

# # --- CÁCH SỬ DỤNG ---
# MY_API_KEY = "DÁN_KEY_CỦA_BẠN_VÀO_ĐÂY"
# MY_LOCATION = "@10.762622,106.660172,15z"

# # Gọi hàm
# data = search_google_maps("tiệm bánh", MY_LOCATION, MY_API_KEY)