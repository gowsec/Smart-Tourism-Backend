# THIẾT KẾ BACKEND - NHÓM 4

## 5.6 Thuật toán Autocomplete
- **Thuật toán**: Trie (Cây tiền tố).
- [cite_start]**Lý do**: Tối ưu tốc độ tìm kiếm $O(K)$, đáp ứng KPI phản hồi < 10s[cite: 321].
- [cite_start]**Logic**: Sắp xếp kết quả dựa trên Rating và Category (Food, Hotel, Sightseeing)[cite: 333, 409].

## 5.5 Workflow xử lý
1. [cite_start]**Nhận Input**: Chuỗi ký tự từ người dùng[cite: 324].
2. **Xử lý**: 
   - Duyệt cây Trie tìm địa điểm khớp.
   - [cite_start]Lọc theo ngân sách (Budget Filtering)[cite: 332].
3. **Ngoại lệ (Exception Handling)**: 
   - [cite_start]Trả về mã lỗi nếu gặp Network Error hoặc JSON Parse Error[cite: 278, 280].
4. [cite_start]**Output**: Trả về Top 5 gợi ý (JSON format)[cite: 334].