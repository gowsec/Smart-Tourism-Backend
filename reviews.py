from flask import Flask, request, jsonify

from flask_cors import CORS

from serpapi import GoogleSearch


app = Flask(__name__)

CORS(app)  # Để Nhi/Hưng (Frontend) gọi được từ React/HTML


API_KEY = "2c4654d942ef2072e678c4b77db52a0639194f7e528644fce4ea92157e4c9b9f"


# --- HELPER FUNCTION ---

def get_google_maps_data(place_name):

    params = {

        "engine": "google_maps",

        "q": place_name,

        "api_key": API_KEY

    }

    search = GoogleSearch(params)

    results = search.get_dict()

    # Lấy kết quả đầu tiên tìm thấy

    if "local_results" in results and len(results["local_results"]) > 0:

        return results["local_results"][0]

    return None


# --- ENDPOINT 1: LẤY HÌNH ẢNH ---

@app.route('/api/images', methods=['GET'])
def get_images():

    place = request.args.get('place')

    if not place:

        return jsonify({"error": "Thiếu tham số place"}), 400

    data = get_google_maps_data(place)

    if data and "thumbnail" in data:

        # Lưu ý: SerpApi thường trả về ảnh đại diện (thumbnail)

        # và một danh sách ảnh khác nếu có trong 'photos'

        return jsonify({

            "place": place,

            "main_image": data.get("thumbnail"),

            "more_images": data.get("photos", [])  # Danh sách các ảnh khác

        })

    return jsonify({"message": "Không tìm thấy ảnh"}), 404


# --- ENDPOINT 2: LẤY REVIEWS ---

@app.route('/api/reviews', methods=['GET'])
def get_reviews():

    place = request.args.get('place')

    if not place:

        return jsonify({"error": "Thiếu tham số place"}), 400

    params = {

        "engine": "google_maps_reviews",

        "q": place,  # Hoặc dùng data_id lấy từ kết quả search địa điểm để chính xác hơn

        "api_key": API_KEY

    }

    try:

        search = GoogleSearch(params)

        results = search.get_dict()

        reviews = results.get("reviews", [])

        # Chỉ lấy các thông tin cần thiết cho Frontend

        formatted_reviews = []

        for r in reviews[:5]:  # Lấy 5 review mới nhất

            formatted_reviews.append({

                "user": r.get("user", {}).get("name"),

                "rating": r.get("rating"),

                "content": r.get("snippet"),

                "date": r.get("date")

            })

        return jsonify({

            "place": place,

            "total_reviews": results.get("search_information", {}).get("total_results"),

            "reviews": formatted_reviews

        })

    except Exception as e:

        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':

    app.run(debug=True, port=5000)
