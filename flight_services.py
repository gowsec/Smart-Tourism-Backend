from serpapi import GoogleSearch
from datetime import datetime, timedelta

def get_smart_flight_recommendations(api_key, departure_id, arrival_id, max_total_budget, num_days, passengers, departure_date=None):
    outbound_dt = datetime.strptime(departure_date, "%Y-%m-%d")
    # Ngày về = Ngày đi + (Số ngày du lịch - 1)
    return_dt = outbound_dt + timedelta(days=num_days - 1)

    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_dt.strftime("%Y-%m-%d"),
        "return_date": return_dt.strftime("%Y-%m-%d"),
        "currency": "VND",
        "adults": passengers,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        flights = search.get_dict().get("best_flights", [])
        smart_flights = []
        for f in flights:
            price = f.get("price", 0)
            if 0 < price <= max_total_budget:
                leg = f.get("flights", [{}])[0]
                smart_flights.append({
                    "airline": leg.get("airline"),
                    "price": price,
                    "thumbnail": leg.get("airline_logo")
                })
        smart_flights.sort(key=lambda x: x['price'])
        return smart_flights[:3]
    except Exception as e:
        print(f"Lỗi Flight: {e}")
        return []