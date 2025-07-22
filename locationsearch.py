import pandas as pd

# Offline data for Telangana places
data = {
    "Place": [
        "Cyberabad", "Hyderabad", "Karimnagar", "Khammam", "Nizamabad", "Rachakonda", "Ramagundam",
        "Siddipet", "Warangal", "Adilabad", "Bhadradri Kothagudem", "Jagtial", "Jayashankar Bhupalpalli",
        "Jogulamba Gadwal", "Kamareddy", "Kumuram Bheem Asifabad", "Mahabubabad", "Mahabubnagar",
        "Medak", "Nagarkurnool", "Nalgonda", "Nirmal", "Rajanna Sircilla", "Sanga Reddy",
        "Suryapet", "Vikarabad", "Wanaparthy", "RP Secunderabad"
    ],
    "Latitude": [
        17.4933, 17.3850, 18.4386, 17.2473, 18.6725, 17.4239, 18.7557,
        18.0973, 17.9784, 19.6667, 17.4607, 18.7904, 18.4385,
        16.2350, 18.2643, 19.3762, 17.5980, 16.7480,
        18.0456, 16.4802, 17.0541, 19.0968, 18.3852, 17.6280,
        17.1310, 17.3410, 16.3612, 17.4385
    ],
    "Longitude": [
        78.3986, 78.4867, 79.1288, 80.1437, 78.0941, 78.6575, 79.4710,
        78.8487, 79.5910, 78.5333, 80.6480, 78.9237, 79.1288,
        77.8000, 78.3419, 79.3444, 80.0022, 77.9975,
        78.2607, 78.4258, 79.2671, 78.3441, 78.8095, 78.0822,
        79.6237, 77.9040, 78.0667, 78.4983
    ],
    "Total_Crime_2022": [
        2241, 2165, 283, 282, 576, 1803, 251,
        185, 385, 128, 146, 88, 81,
        271, 151, 53, 102, 220,
        98, 252, 172, 63, 51, 210,
        155, 64, 192, 675
    ]
}


df = pd.DataFrame(data)

def assign_zone(crime):
    if crime >= 1000:
        return 'Red'   
    elif crime >= 200:
        return 'Orange'
    else:
        return 'Green'  

def get_crime_by_coords(lat, lon):
    match = df[(df['Latitude'] == lat) & (df['Longitude'] == lon)]
    if not match.empty:
        return int(match.iloc[0]["Total_Crime_2022"])
    else:
        return -1  

def get_zone_by_coords(lat, lon):
    crime = get_crime_by_coords(lat, lon)
    if crime == -1:
        return "Coordinates not found in database."
    return assign_zone(crime)

