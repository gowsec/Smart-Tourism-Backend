from serpapi import GoogleSearch

def get_robust_data_id(api_key, query):
    params = {
        "engine": "google_maps",
        "q": query,
        "hl": "vi",
        "api_key": api_key
    }
    
    search = GoogleSearch(params)
    results = search.get_dict()
    
    # 1. Thử tìm trong place_results (Dành cho địa điểm cụ thể, nổi tiếng)
    if "place_results" in results:
        return results["place_results"].get("data_id"), results["place_results"].get("title")
    
    # 2. Thử tìm trong local_results (Dành cho danh sách nhiều cửa hàng/địa điểm)
    if "local_results" in results and len(results["local_results"]) > 0:
        first_result = results["local_results"][0]
        return first_result.get("data_id"), first_result.get("title")
    
    return None, None

def run_final_test(api_key, location_name):
    print(f" Đang kiểm tra địa điểm: {location_name}")
    
    data_id, title = get_robust_data_id(api_key, location_name)
    
    if data_id:
        print(f" Đã tìm thấy Data ID: {data_id}")
        print(f" Tên chính xác: {title}")
        
        # Gọi API lấy ảnh ngay lập tức để kiểm tra
        photo_params = {
            "engine": "google_maps_photos",
            "data_id": data_id,
            "api_key": api_key
        }
        photo_search = GoogleSearch(photo_params)
        photo_results = photo_search.get_dict()
        
        photos = photo_results.get("photos", [])
        print(f" Số lượng ảnh tìm thấy: {len(photos)}")
        if photos:
            print(f" Link ảnh mẫu: {photos[0].get('image')}")
    else:
        print(" Vẫn không tìm thấy data_id. Hãy thử từ khóa khác phổ biến hơn.")

# # --- CHẠY THỬ ---
# MY_KEY = "LET INPUT API KEY" 
# run_final_test(MY_KEY, "Bitexco Financial Tower")