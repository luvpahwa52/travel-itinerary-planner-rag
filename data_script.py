
import pandas as pd
import os

# Load existing data
attractions_df = pd.read_csv("data/attractions.csv")
hotels_df = pd.read_csv("data/hotels.csv")
food_df = pd.read_csv("data/food.csv")
transport_df = pd.read_csv("data/transport.csv")

print(f"Current: {len(attractions_df)} attractions | {len(hotels_df)} hotels | {len(food_df)} food | {len(transport_df)} transport")
print(f"Cities: {', '.join(attractions_df['city'].unique())}")

os.makedirs("data", exist_ok=True)


# =============================
# HOTELS — Add 4 new cities
# =============================
hotels_data = [
    # GOA (4)
    {"city": "Goa", "name": "Zostel Goa (Calangute)", "type": "Hostel", "price_per_night_inr": 600, "rating": 4.2, "area": "Calangute", "description": "Budget backpacker hostel with dorms and private rooms near Calangute Beach."},
    {"city": "Goa", "name": "OYO Baga Comfort Inn", "type": "Budget Hotel", "price_per_night_inr": 1200, "rating": 3.8, "area": "Baga", "description": "Affordable budget hotel 5 minutes from Baga Beach with AC rooms."},
    {"city": "Goa", "name": "Treebo Trend Morjim", "type": "Mid-Range", "price_per_night_inr": 2500, "rating": 4.1, "area": "Morjim", "description": "Mid-range hotel near Morjim Beach with pool and restaurant."},
    {"city": "Goa", "name": "Taj Fort Aguada Resort", "type": "Luxury", "price_per_night_inr": 12000, "rating": 4.8, "area": "Sinquerim", "description": "5-star luxury resort within a 16th-century Portuguese fort with private beach and infinity pool."},

    # DELHI (4)
    {"city": "Delhi", "name": "Moustache Hostel Delhi", "type": "Hostel", "price_per_night_inr": 500, "rating": 4.3, "area": "Paharganj", "description": "Popular backpacker hostel near New Delhi Railway Station with rooftop cafe."},
    {"city": "Delhi", "name": "Hotel Amax Inn", "type": "Budget Hotel", "price_per_night_inr": 1500, "rating": 3.7, "area": "Karol Bagh", "description": "Budget hotel in Karol Bagh shopping hub with AC, WiFi, and room service."},
    {"city": "Delhi", "name": "The Park New Delhi", "type": "Mid-Range", "price_per_night_inr": 5000, "rating": 4.3, "area": "Connaught Place", "description": "Stylish mid-range hotel in CP with rooftop bar, spa, and fine dining."},
    {"city": "Delhi", "name": "The Imperial New Delhi", "type": "Luxury", "price_per_night_inr": 18000, "rating": 4.9, "area": "Janpath", "description": "Heritage luxury hotel from 1931 with museum-worthy art collection and award-winning restaurants."},

    # JAIPUR (4)
    {"city": "Jaipur", "name": "Zostel Jaipur", "type": "Hostel", "price_per_night_inr": 500, "rating": 4.1, "area": "Gangapole", "description": "Colorful hostel in the old city near Hawa Mahal with rooftop fort views."},
    {"city": "Jaipur", "name": "Hotel Pearl Palace", "type": "Budget Hotel", "price_per_night_inr": 1800, "rating": 4.4, "area": "Hathroi Fort", "description": "Award-winning heritage budget hotel with themed rooms and rooftop restaurant."},
    {"city": "Jaipur", "name": "Samode Haveli", "type": "Mid-Range", "price_per_night_inr": 6000, "rating": 4.6, "area": "Gangapole", "description": "A 175-year-old restored haveli with traditional Rajasthani architecture and pool."},
    {"city": "Jaipur", "name": "Rambagh Palace", "type": "Luxury", "price_per_night_inr": 25000, "rating": 4.9, "area": "Bhawani Singh Road", "description": "Former Maharaja residence, now a Taj Hotel with 47-acre Mughal gardens and polo grounds."},

    # KERALA (4)
    {"city": "Kerala", "name": "Zostel Alleppey", "type": "Hostel", "price_per_night_inr": 550, "rating": 4.0, "area": "Alleppey", "description": "Backpacker hostel near Alleppey beach and backwater jetty."},
    {"city": "Kerala", "name": "Tea Valley Resort Munnar", "type": "Budget Hotel", "price_per_night_inr": 2000, "rating": 4.2, "area": "Munnar", "description": "Budget resort surrounded by tea plantations with valley views."},
    {"city": "Kerala", "name": "Alleppey Houseboat (Premium)", "type": "Mid-Range", "price_per_night_inr": 6000, "rating": 4.7, "area": "Alleppey Backwaters", "description": "Premium houseboat with AC bedroom, upper deck, and private chef."},
    {"city": "Kerala", "name": "Kumarakom Lake Resort", "type": "Luxury", "price_per_night_inr": 15000, "rating": 4.8, "area": "Kumarakom", "description": "Award-winning luxury resort on Vembanad Lake with Ayurvedic spa and pool villas."},

    # MANALI (4)
    {"city": "Manali", "name": "Zostel Manali", "type": "Hostel", "price_per_night_inr": 500, "rating": 4.3, "area": "Old Manali", "description": "Popular backpacker hostel in Old Manali with mountain views and bonfire nights."},
    {"city": "Manali", "name": "Hotel Manali Inn", "type": "Budget Hotel", "price_per_night_inr": 1500, "rating": 3.9, "area": "Mall Road", "description": "Budget hotel on Mall Road with valley-facing rooms and in-house restaurant."},
    {"city": "Manali", "name": "The Orchard Greens", "type": "Mid-Range", "price_per_night_inr": 4000, "rating": 4.4, "area": "Hadimba Road", "description": "Mid-range resort near Hadimba Temple surrounded by apple orchards."},
    {"city": "Manali", "name": "The Himalayan", "type": "Luxury", "price_per_night_inr": 10000, "rating": 4.7, "area": "Log Huts Area", "description": "Luxury mountain resort with panoramic Himalayan views and heated pool."},

    # VARANASI (4)
    {"city": "Varanasi", "name": "Zostel Varanasi", "type": "Hostel", "price_per_night_inr": 450, "rating": 4.2, "area": "Assi Ghat", "description": "Backpacker hostel near Assi Ghat with rooftop Ganga views."},
    {"city": "Varanasi", "name": "Hotel Alka", "type": "Budget Hotel", "price_per_night_inr": 1200, "rating": 4.0, "area": "Dashashwamedh Ghat", "description": "Heritage budget hotel right on Dashashwamedh Ghat with Ganga views."},
    {"city": "Varanasi", "name": "BrijRama Palace", "type": "Mid-Range", "price_per_night_inr": 7000, "rating": 4.6, "area": "Darbhanga Ghat", "description": "Restored 18th-century palace on the ghats with river-facing rooms."},
    {"city": "Varanasi", "name": "Taj Nadesar Palace", "type": "Luxury", "price_per_night_inr": 20000, "rating": 4.8, "area": "Nadesar", "description": "Intimate luxury palace in 40 acres of mango orchards and jasmine gardens."},

    # MUMBAI (4) — NEW
    {"city": "Mumbai", "name": "Zostel Mumbai", "type": "Hostel", "price_per_night_inr": 700, "rating": 4.1, "area": "Colaba", "description": "Backpacker hostel in Colaba near Gateway of India with common lounge and city tours."},
    {"city": "Mumbai", "name": "Hotel Residency Fort", "type": "Budget Hotel", "price_per_night_inr": 2000, "rating": 3.8, "area": "Fort", "description": "Budget hotel in Fort area near CST station with clean rooms and AC."},
    {"city": "Mumbai", "name": "Trident Nariman Point", "type": "Mid-Range", "price_per_night_inr": 7000, "rating": 4.5, "area": "Nariman Point", "description": "Premium hotel overlooking Marine Drive with sea-view rooms and rooftop pool."},
    {"city": "Mumbai", "name": "Taj Mahal Palace", "type": "Luxury", "price_per_night_inr": 22000, "rating": 4.9, "area": "Colaba", "description": "Iconic 1903 luxury hotel next to Gateway of India with harbour views and 7 restaurants."},

    # UDAIPUR (4) — NEW
    {"city": "Udaipur", "name": "Zostel Udaipur", "type": "Hostel", "price_per_night_inr": 500, "rating": 4.2, "area": "Lal Ghat", "description": "Backpacker hostel near Lal Ghat with lake views and rooftop cafe."},
    {"city": "Udaipur", "name": "Hotel Lakend", "type": "Budget Hotel", "price_per_night_inr": 2500, "rating": 4.0, "area": "Fateh Sagar", "description": "Budget hotel on Fateh Sagar Lake with lake-view rooms and restaurant."},
    {"city": "Udaipur", "name": "Amet Haveli", "type": "Mid-Range", "price_per_night_inr": 5000, "rating": 4.5, "area": "Hanuman Ghat", "description": "Heritage lakeside haveli with rooftop restaurant overlooking Lake Pichola and City Palace."},
    {"city": "Udaipur", "name": "Taj Lake Palace", "type": "Luxury", "price_per_night_inr": 30000, "rating": 4.9, "area": "Lake Pichola", "description": "Floating white marble palace in the middle of Lake Pichola. One of the world's most romantic hotels."},

    # RISHIKESH (4) — NEW
    {"city": "Rishikesh", "name": "Zostel Rishikesh", "type": "Hostel", "price_per_night_inr": 500, "rating": 4.3, "area": "Tapovan", "description": "Backpacker hostel in Tapovan near Laxman Jhula with Ganges views and yoga sessions."},
    {"city": "Rishikesh", "name": "Hotel Ishan", "type": "Budget Hotel", "price_per_night_inr": 1500, "rating": 3.9, "area": "Laxman Jhula", "description": "Budget hotel near Laxman Jhula with clean rooms, river views, and yoga arrangements."},
    {"city": "Rishikesh", "name": "Aloha on the Ganges", "type": "Mid-Range", "price_per_night_inr": 4500, "rating": 4.4, "area": "Tapovan", "description": "Riverside resort with private beach, spa, adventure desk, and multi-cuisine restaurant."},
    {"city": "Rishikesh", "name": "Ananda in the Himalayas", "type": "Luxury", "price_per_night_inr": 35000, "rating": 4.9, "area": "Narendra Nagar", "description": "World-renowned luxury wellness resort in a Maharaja's palace estate with Ayurveda, yoga, and Ganges views."},

    # AGRA (4) — NEW
    {"city": "Agra", "name": "Zostel Agra", "type": "Hostel", "price_per_night_inr": 500, "rating": 4.1, "area": "Taj Ganj", "description": "Backpacker hostel in Taj Ganj with rooftop Taj Mahal views and common kitchen."},
    {"city": "Agra", "name": "Hotel Sidhartha", "type": "Budget Hotel", "price_per_night_inr": 1200, "rating": 3.8, "area": "Taj Ganj", "description": "Budget hotel near Taj Mahal east gate with AC rooms and rooftop restaurant with Taj views."},
    {"city": "Agra", "name": "Crystal Sarovar Premiere", "type": "Mid-Range", "price_per_night_inr": 4000, "rating": 4.3, "area": "Fatehabad Road", "description": "Modern mid-range hotel on Fatehabad Road with pool, spa, and 2km from Taj Mahal."},
    {"city": "Agra", "name": "The Oberoi Amarvilas", "type": "Luxury", "price_per_night_inr": 28000, "rating": 4.9, "area": "Taj East Gate", "description": "Ultra-luxury hotel 600m from Taj Mahal. Every room has unobstructed Taj views. Mughal-inspired architecture."},
]

hotels_df = pd.DataFrame(hotels_data)
hotels_df.to_csv("data/hotels.csv", index=False)
print(f"✅ hotels.csv — {len(hotels_df)} records across {hotels_df['city'].nunique()} cities")

