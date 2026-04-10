class TrieNode:
    def __init__(self):
        self.children = {}
        self.locations = []  # Danh sách địa điểm bắt đầu bằng tiền tố này


class AutocompleteEngine:
    def __init__(self):
        self.root = TrieNode()

    def insert_location(self, name, data):
        """Thêm địa điểm vào cây Trie"""
        node = self.root
        for char in name.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.locations.append(data)

    def search_suggestions(self, prefix):
        """Tìm 5 gợi ý tốt nhất dựa trên Rating """
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []  # Trả về mảng rỗng nếu không khớp
            node = node.children[char]

        # Sắp xếp theo Rating giảm dần (theo logic slide trang 20) [cite: 411]
        sorted_list = sorted(
            node.locations, key=lambda x: x['rating'], reverse=True)

        # Trả về top 5 địa điểm không trùng tên
        seen = set()
        unique_results = []
        for loc in sorted_list:
            if loc['name'] not in seen:
                unique_results.append(loc)
                seen.add(loc['name'])
            if len(unique_results) == 5:
                break

        return unique_results
if __name__ == "__main__":
    engine = AutocompleteEngine()
    
    # 1. Dữ liệu mẫu (Mục 5.7 của Triêm) - Lấy đúng từ Slide 19 của nhóm [cite: 380-401]
    sample_locations = [
        {"name": "Bảo tàng", "cost": 40000, "rating": 4.5, "cat": "Sightseeing"},
        {"name": "Landmark 81", "cost": 500000, "rating": 4.7, "cat": "Sightseeing"},
        {"name": "Cơm tấm bụi", "cost": 50000, "rating": 4.2, "cat": "Food"},
        {"name": "Nhà hàng Buffet", "cost": 800000, "rating": 4.8, "cat": "Food"},
        {"name": "Khách sạn 4 sao", "cost": 1200000, "rating": 4.6, "cat": "Hotel"},
        {"name": "Homestay xịn", "cost": 400000, "rating": 4.3, "cat": "Hotel"}
    ]
    
    for loc in sample_locations:
        engine.insert_location(loc['name'], loc)

    print("--- HỆ THỐNG DU LỊCH THÔNG MINH (MÔ PHỎNG) ---")
    
    # Kịch bản: Anh A nhập chữ 'L' [cite: 300]
    query = "L"
    suggestions = engine.search_suggestions(query)
    
    if suggestions:
        print(f"\n[1] Kết quả Autocomplete cho '{query}':")
        for i, s in enumerate(suggestions):
            print(f"    {i+1}. {s['name']} ({s['rating']}⭐) - Giá: {s['cost']} VND")
        
        # Giả lập Anh A chọn gợi ý đầu tiên (Landmark 81)
        selected = suggestions[0]
        print(f"\n[2] Bạn đã chọn: {selected['name']}")
        
        # ĐỀ XUẤT THÔNG MINH (Smart Recommendation):
        # Dựa trên ngân sách còn lại của Anh A (ví dụ còn 1 triệu) [cite: 422]
        budget = 1000000
        remaining = budget - selected['cost']
        
        print(f"\n[3] ĐỀ XUẤT LỊCH TRÌNH (Ngân sách còn lại: {remaining} VND):")
        # Logic: Tìm các địa điểm Food và Hotel phù hợp túi tiền còn lại [cite: 412-421]
        for loc in sample_locations:
            if loc['cat'] in ['Food', 'Hotel'] and loc['cost'] <= remaining:
                print(f"    - Nên đi thêm: {loc['name']} ({loc['cat']}) - {loc['cost']} VND")
    else:
        # Xử lý ngoại lệ (Exception) cho mục 5.5 [cite: 278-279]
        print(f"\n[!] Không tìm thấy kết quả nào cho '{query}'. Vui lòng thử lại!")