
from serpapi.google_search import GoogleSearch
import math
import itertools

# =========================
# CONFIG
# =========================

SERP_API_KEY = "hey girl this your song let's see that ***** "

MAX_DISTANCE_KM = 50
SYSTEM_AVG_RATING = 4.2
MIN_REVIEWS = 50

W_DISTANCE = 0.4
W_PRICE = 0.35
W_RATING = 0.25


# =========================
# PRICE ESTIMATION
# =========================

CATEGORY_PRICE = {
    "hotel": (800000, 3000000),
    "food": (50000, 250000),
    "coffee": (40000, 120000),
    "attraction": (50000, 300000)
}


def estimate_price(category):
    low, high = CATEGORY_PRICE.get(category, (100000, 300000))
    return (low + high) / 2


# =========================
# BAYESIAN RATING
# =========================

def bayesian_rating(r, v):
    return (v / (v + MIN_REVIEWS)) * r + (MIN_REVIEWS / (v + MIN_REVIEWS)) * SYSTEM_AVG_RATING


# =========================
# HAVERSINE DISTANCE
# =========================

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# =========================
# GET PLACE (SERPAPI)
# =========================

def get_place_info(name, category):
    params = {
        "engine": "google_maps",
        "q": name,
        "api_key": SERP_API_KEY
    }

    try:
        data = GoogleSearch(params).get_dict()

        place = None

        if "place_results" in data:
            place = data["place_results"]
        elif "local_results" in data and data["local_results"]:
            place = data["local_results"][0]
        else:
            return None

        gps = place.get("gps_coordinates", {})

        return {
            "name": name,
            "category": category,
            "rating": place.get("rating", 4.0),
            "reviews": place.get("reviews", 0),
            "lat": gps.get("latitude", 0),
            "lng": gps.get("longitude", 0)
        }

    except:
        return None


# =========================
# SEARCH PLACES
# =========================

def search_places(destination, category, limit=8):
    query = f"best {category}s in {destination}"

    params = {
        "engine": "google_maps",
        "q": query,
        "api_key": SERP_API_KEY
    }

    data = GoogleSearch(params).get_dict()

    results = data.get("local_results", [])[:limit]

    places = []

    for r in results:
        name = r.get("title")
        if name:
            info = get_place_info(name, category)
            if info:
                places.append(info)

    return places


# =========================
# SCORE FUNCTIONS
# =========================

def distance_score(d):
    if d <= 0:
        return 0
    return max(0, 10 - (d / MAX_DISTANCE_KM) * 10)


def price_score(price, budget):
    if price <= budget:
        return 10
    penalty = (price - budget) / 100000 * 2.5
    return max(0, 10 - penalty)


def rating_score(route):
    vals = []
    for p in route:
        vals.append(bayesian_rating(p["rating"], p["reviews"]))
    return (sum(vals) / len(vals)) / 5 * 10


# =========================
# DISTANCE + PRICE
# =========================

def route_distance(route):
    total = 0
    for i in range(len(route) - 1):
        a = route[i]
        b = route[i + 1]
        total += haversine(a["lat"], a["lng"], b["lat"], b["lng"])
    return total


def route_price(route):
    return sum(estimate_price(p["category"]) for p in route)


# =========================
# GENERATE ROUTES
# =========================

def generate_routes(hotels, foods, coffees, attractions):
    routes = []

    for h in hotels:
        for c in coffees:
            for f in itertools.combinations(foods, 2):
                for a in itertools.combinations(attractions, 2):
                    route = [h] + list(f) + [c] + list(a)
                    routes.append(route)

    return routes


# =========================
# MAIN SYSTEM
# =========================

def recommend_routes(destination, budget):
    hotels = search_places(destination, "hotel", 5)
    foods = search_places(destination, "food", 8)
    coffees = search_places(destination, "coffee", 5)
    attractions = search_places(destination, "attraction", 8)

    routes = generate_routes(hotels, foods, coffees, attractions)

    scored = []

    for r in routes:

        d = route_distance(r)
        p = route_price(r)

        ds = distance_score(d)
        ps = price_score(p, budget)
        rs = rating_score(r)

        final = ds * W_DISTANCE + ps * W_PRICE + rs * W_RATING

        scored.append((final, r, d, p, ds, ps, rs))

    scored.sort(reverse=True, key=lambda x: x[0])

    top = scored[:20]

    print("\n========== TOP ROUTES ==========\n")

    for i, (final, route, d, p, ds, ps, rs) in enumerate(top):

        print(f"ROUTE #{i+1}")
        for x in route:
            print("-", x["name"], f"({x['category']})")

        print(f"\nDistance: {round(d,2)} km")
        print(f"Price: {int(p):,} VND")
        print(f"Distance Score: {round(ds,2)}")
        print(f"Price Score: {round(ps,2)}")
        print(f"Rating Score: {round(rs,2)}")
        print(f"FINAL SCORE: {round(final,2)}")
        print("\n" + "="*50 + "\n")


# =========================
# RUN
# =========================

recommend_routes(
    destination="Dong Nai Vietnam",
    budget=5_000_000
)


print("DONE")

# # Note
# # =========================================================
# # HÀM THỰC THI CHÍNH
# # =========================================================

# # Tên hàm:
# # analyze_route()

# # ---------------------------------------------------------
# # CHỨC NĂNG
# # ---------------------------------------------------------
# # Hàm này dùng để:
# #
# # 1. Phân tích toàn bộ lộ trình
# # 2. Lấy dữ liệu từ SerpApi:
# #    - rating
# #    - reviews
# #    - price level
# #    - gps coordinates
# #
# # 3. Tính:
# #    - tổng khoảng cách
# #    - tổng chi phí
# #    - điểm distance
# #    - điểm price
# #    - điểm rating
# #
# # 4. Xuất kết quả cuối cùng theo thang điểm 10


# # =========================================================
# # ĐẦU VÀO HÀM
# # =========================================================

# from serpapi.google_search import GoogleSearch
# import math

# # =========================================================
# # CONFIG
# # =========================================================

# SERP_API_KEY = "hey girl this your song let's see that *****"

# OVER_PENALTY = 2.8

# SYSTEM_AVG_RATING = 4.2
# MIN_REVIEWS = 50

# MAX_DISTANCE_KM = 50

# # trọng số
# W_DISTANCE = 0.40
# W_PRICE = 0.35
# W_RATING = 0.25


# # =========================================================
# # CATEGORY PRICE ESTIMATION
# # =========================================================

# CATEGORY_PRICE = {

#     "com tam": (50000, 100000),

#     "pho": (40000, 90000),

#     "coffee": (30000, 80000),

#     "milk tea": (35000, 70000),

#     "restaurant": (150000, 400000),

#     "hotel": (1000000, 5000000),

#     "mall": (100000, 300000)
# }


# # =========================================================
# # PRICE LEVEL MAP
# # =========================================================

# PRICE_LEVEL_MAP = {

#     "$": 70000,

#     "$$": 200000,

#     "$$$": 500000,

#     "$$$$": 1500000
# }


# # =========================================================
# # ROUTE INPUT
# # =========================================================

# route = [

#     {
#         "name": "Ben Thanh Market, Ho Chi Minh City",
#         "category": "mall"
#     },

#     {
#         "name": "Landmark 81, Ho Chi Minh City",
#         "category": "mall"
#     },

#     {
#         "name": "Cơm Tấm Ba Ghiền, Ho Chi Minh City",
#         "category": "com tam"
#     },

#     {
#         "name": "Highlands Coffee, Ho Chi Minh City",
#         "category": "coffee"
#     }
# ]


# # =========================================================
# # USER BUDGET
# # =========================================================

# user_budget = 2_000_000


# # =========================================================
# # GET PLACE INFO
# # =========================================================

# def get_place_info(place_name):

#     params = {

#         "engine": "google_maps",

#         "q": place_name,

#         "api_key": SERP_API_KEY
#     }

#     try:

#         search = GoogleSearch(params)

#         data = search.get_dict()

#         print("\n========== DEBUG API ==========")
#         print(data)

#         # ---------------------------------------------
#         # CASE 1
#         # ---------------------------------------------

#         if "place_results" in data:

#             place = data["place_results"]

#         # ---------------------------------------------
#         # CASE 2
#         # ---------------------------------------------

#         elif (
#             "local_results" in data
#             and
#             len(data["local_results"]) > 0
#         ):

#             place = data["local_results"][0]

#         else:

#             print("KHÔNG TÌM THẤY PLACE")

#             return None

#         # ---------------------------------------------
#         # GPS
#         # ---------------------------------------------

#         gps = place.get(
#             "gps_coordinates",
#             {}
#         )

#         lat = gps.get(
#             "latitude",
#             0
#         )

#         lng = gps.get(
#             "longitude",
#             0
#         )

#         result = {

#             "rating": place.get(
#                 "rating",
#                 4.0
#             ),

#             "reviews": place.get(
#                 "reviews",
#                 0
#             ),

#             "price_level": place.get(
#                 "price",
#                 None
#             ),

#             "lat": lat,

#             "lng": lng
#         }

#         print("\nPLACE INFO:")
#         print(result)

#         return result

#     except Exception as e:

#         print("API ERROR:", e)

#         return None


# # =========================================================
# # HAVERSINE
# # =========================================================

# def haversine(lat1, lon1, lat2, lon2):

#     R = 6371

#     phi1 = math.radians(lat1)
#     phi2 = math.radians(lat2)

#     dphi = math.radians(lat2 - lat1)
#     dlambda = math.radians(lon2 - lon1)

#     a = (

#         math.sin(dphi / 2) ** 2

#         +

#         math.cos(phi1)
#         *
#         math.cos(phi2)
#         *
#         math.sin(dlambda / 2) ** 2
#     )

#     c = 2 * math.atan2(
#         math.sqrt(a),
#         math.sqrt(1 - a)
#     )

#     return R * c


# # =========================================================
# # ESTIMATE PRICE
# # =========================================================

# def estimate_price(category):

#     if category not in CATEGORY_PRICE:

#         return 100000

#     low, high = CATEGORY_PRICE[category]

#     return (low + high) / 2


# # =========================================================
# # GET FINAL PRICE
# # =========================================================

# def get_final_price(price_level, category):

#     if price_level in PRICE_LEVEL_MAP:

#         return PRICE_LEVEL_MAP[price_level]

#     return estimate_price(category)


# # =========================================================
# # BAYESIAN RATING
# # =========================================================

# def bayesian_rating(R, v):

#     return (

#         (v / (v + MIN_REVIEWS)) * R

#         +

#         (MIN_REVIEWS / (v + MIN_REVIEWS))
#         * SYSTEM_AVG_RATING
#     )


# # =========================================================
# # DISTANCE SCORE
# # =========================================================

# def distance_score(total_distance):

#     score = 10 - (
#         (total_distance / MAX_DISTANCE_KM) * 10
#     )

#     return max(0, min(score, 10))


# # =========================================================
# # PRICE SCORE
# # =========================================================

# def price_score(total_price, budget):

#     # vượt ngân sách
#     if total_price > budget:

#         diff = total_price - budget

#         unit = diff / 100_000

#         penalty = unit * OVER_PENALTY

#         score = 10 - penalty

#     else:

#         score = 10

#     return max(0, min(score, 10))


# # =========================================================
# # RATING SCORE
# # =========================================================
# def rating_score(ratings, reviews):

#     # không có dữ liệu
#     if len(ratings) == 0:

#         return 0

#     weighted = []

#     for i in range(len(ratings)):

#         wr = bayesian_rating(
#             ratings[i],
#             reviews[i]
#         )

#         weighted.append(wr)

#     avg = sum(weighted) / len(weighted)

#     return (avg / 5.0) * 10


# # =========================================================
# # MAIN
# # =========================================================

# def analyze_route(route, budget):

#     print("\n========== ROUTE ANALYSIS ==========\n")

#     total_distance = 0
#     total_price = 0

#     ratings = []
#     reviews = []

#     infos = []

#     # -----------------------------------------------------
#     # GET ALL INFO
#     # -----------------------------------------------------

#     for place in route:

#         info = get_place_info(
#             place["name"]
#         )

#         infos.append(info)

#     # -----------------------------------------------------
#     # PRINT EACH PLACE
#     # -----------------------------------------------------

#     for i in range(len(route)):

#         place = route[i]

#         info = infos[i]

#         if info is None:

#             continue

#         # price
#         price = get_final_price(

#             info["price_level"],

#             place["category"]
#         )

#         total_price += price

#         ratings.append(
#             info["rating"]
#         )

#         reviews.append(
#             info["reviews"]
#         )

#         print(f"ĐỊA ĐIỂM {i + 1}")

#         print(f"Tên: {place['name']}")

#         print(f"Loại: {place['category']}")

#         print(f"Rating: {info['rating']}")

#         print(f"Reviews: {info['reviews']}")

#         print(f"Price Level: {info['price_level']}")

#         print(
#             f"Giá ước lượng: "
#             f"{price:,.0f} VND"
#         )

#         # -------------------------------------------------
#         # DISTANCE
#         # -------------------------------------------------

#         if i < len(route) - 1:

#             next_place = route[i + 1]

#             next_info = infos[i + 1]

#             distance = haversine(

#                 info["lat"],
#                 info["lng"],

#                 next_info["lat"],
#                 next_info["lng"]
#             )

#             total_distance += distance

#             print(
#                 f"\n→ Đi tới:"
#             )

#             print(
#                 f"{next_place['name']}"
#             )

#             print(
#                 f"Khoảng cách: "
#                 f"{distance:.2f} km"
#             )

#         print("\n" + "-" * 50 + "\n")

#     # -----------------------------------------------------
#     # SCORES
#     # -----------------------------------------------------

#     d_score = distance_score(
#         total_distance
#     )

#     p_score = price_score(
#         total_price,
#         budget
#     )

#     r_score = rating_score(
#         ratings,
#         reviews
#     )

#     final_score = (

#         d_score * W_DISTANCE

#         +

#         p_score * W_PRICE

#         +

#         r_score * W_RATING
#     )

#     # -----------------------------------------------------
#     # FINAL
#     # -----------------------------------------------------

#     print("\n========== FINAL RESULT ==========\n")

#     print(
#         f"Tổng khoảng cách: "
#         f"{total_distance:.2f} km"
#     )

#     print(
#         f"Tổng chi phí: "
#         f"{total_price:,.0f} VND"
#     )

#     print(
#         f"Ngân sách user: "
#         f"{budget:,.0f} VND"
#     )

#     print(
#         f"\nDistance Score: "
#         f"{d_score:.2f}/10"
#     )

#     print(
#         f"Price Score: "
#         f"{p_score:.2f}/10"
#     )

#     print(
#         f"Rating Score: "
#         f"{r_score:.2f}/10"
#     )

#     print(
#         f"\nFINAL SCORE: "
#         f"{final_score:.2f}/10"
#     )


# # =========================================================
# # RUN
# # =========================================================

# analyze_route(
#     route,
#     user_budget
# )
