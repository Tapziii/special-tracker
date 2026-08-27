#!/usr/bin/env python3
"""
Global + Geofence Special Aircraft Tracker (GitHub Actions Version)
Now with Stealth-Proof Hex Tracking & Military Heavy/Tanker Category Detection!
"""

import time
import requests
import logging
import os
import json
import math

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8758934096:AAEMPHenyHmGydhG0G993GkpR4YlTAMsGg8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "2114651613")
STATE_FILE = "tracked_flights.json"

TLV_LAT = 32.0114
TLV_LON = 34.8867
TLV_RADIUS_NM = 440

# Stealth-Proof Hex Codes (Cannot be hidden by pilots)
SPECIAL_HEXES = ["738a01"] # 4X-ISR (Wing of Zion)

SPECIAL_REGS = [
    # Original Special Liveries
    "9H-EUM", "D-AEWM", "D-AEWP", "D-AIUA", "D-AIZH", "D-AIZM", "D-AIZN",
    "EI-DSY", "EI-EIB", "EI-EIE", "HB-IJN", "HB-IJO", "OE-LBO", "OE-LBY",
    "OE-LBZ", "HB-JLT", "D-ABYN", "D-AIMH", "D-AIFA", "D-AIXL", "D-ABPU",
    "D-AISZ", "D-AIBH", "D-AIBI", "D-AIBJ", "D-AILU", "EI-IMX", "OO-SSY",
    "OO-SNB", "OO-SNJ", "OO-SNM", "OO-SNO", "OO-SNP", "OO-SNQ", "D-AIND",
    "D-AING", "D-AINY", "EI-HOI", "OO-SBA", "OO-SBB", "D-AIRY", "D-AEEA",
    "D-AIEM", "D-AIEP", "D-AIEQ", "EI-IFD", "HB-IFA", "D-ABYT", "OE-LPF",
    "D-ALFI", "4X-EDF", "4X-EDM", "4X-ISR", "D-AICH", "D-ASGE", "D-AICS",
    "9H-WMR", "9H-WNM", "G-XLRA", "A6-EJB", "A6-AEN", "A6-BLV", "A6-BND",
    "A6-BMA", "A6-BMH", "PH-YHD", "PH-HSI", "PH-BXO", "PH-BVA", "PH-BKA",
    "PH-NXM", "PH-EZX", "ET-AYN", "ET-BAW", "ET-AQN", "ET-ATG", "ET-BCC",
    "ET-AXS", "SX-DVQ", "SX-DVR", "SP-LVD", "SP-LVF", "SP-LVG", "SP-LVK",
    "SP-LVL", "SP-LSC", "YL-ABN", "YL-ABX", "YL-CSJ", "YL-CSK", "YL-CSL",
    "4X-EDN", "ER-00004", "B-1540", "B-1499", "B-1343", "N91007", "N61101",
    "N24988", "N794UA", "N78017", "N77022", "N76021", "N218UA", "G-EUYP",
    "G-EUYR", "G-EUYS", "G-TTNA", "G-YMME", "G-YMMF", "G-YMMR", "G-YMMT",
    "G-YMMU", "G-STBN", "C-FSBV", "C-FIVM", "N411DX", "N521DN", "N522DZ",
    "N527DN", "N531DN", "EC-NFZ", "EC-NJY", "D-ABDQ", "9H-EUM", "D-AEWM",
    
    # 777-300ERSF Registrations
    "9H-CAZ", "9H-CAY", "N5401T", "9H-GLG", "9H-JJB", "N779CK", "N771CK",
    "N770CK", "N778CK", "A6-EBK", "N162JL",
    
    # Other Non-777 Special Registrations
    "4X-CVD", "4X-CVE", "4X-CVJ", "4X-WIA", "4X-WIR", "4X-WIS", "4X-CVG",
    "4X-CVI", "4X-CVH", "N216GA", "4X-AOO", "M-YULI", "4X-BAL", "4X-BAK",
    "4X-AFG", "4X-AFC", "4X-AFG", "4X-AFV", "4X-AFG", "4X-AFK", "4X-AFU",
    "4X-AFJ", "4X-AFY", "4X-AFA", "4X-AFS", "4X-AFL", "4X-AFH"
]

TARGET_AIRLINES = [
    "FJI", "HFA", "AFL", "CCM", "AXY", "AAF", "DJT", "QFA", "ANZ", "NBT", 
    "UBT", "IGO", "ANA", "GRL", "ARG", "AMX", "SIA", "THA", "JAL", "HVN", 
    "ALK", "KMM", "VLG", "FIN", "KZR", "EDW", "SVA", "ASL", "UAE", "OCN", 
    "TOM", "TFL", "MBU", "EXS", "HFY", "HFM", "PAL", "AIB", "VSV"
]

TARGET_TYPE_PREFIXES = ('B74', 'A38', 'A34', 'A30', 'B75', 'B76', 'B77L', 'B778', 'B779', 'C17', 'C5', 'A124', 'T204', 'A310', 'K35R', 'C135', 'A400', 'E29', 'IL76', 'IL96', 'A3ST', 'A337', 'C130', 'C30J')
GLOBAL_FETCH_TYPES = "B741,B742,B743,B744,B748,B74S,B74R,A388,A342,A343,A345,A346,A306,A30B,B752,B753,B762,B763,B764,B77L,B77W,B772,B778,B779,B788,B789,B78X,C17,C5,A124,T204,T214,A310,A319,A321,A332,A333,A339,A359,A35K,K35R,C135,A400,E290,E295,IL76,IL96,MD11,A3ST,A337,C130,C30J"

IRREGULAR_COMBOS = [
    ("DLH", "A319"), ("DLH", "A333"), ("DLH", "A343"), ("DLH", "A346"), ("DLH", "A359"),
    ("DLH", "B744"), ("DLH", "B748"), ("DLH", "B789"), ("AUA", "B763"), ("AUA", "B772"),
    ("AUA", "B789"), ("SWR", "A221"), ("SWR", "A343"), ("SWR", "B77W"), ("BEL", "A333"),
    ("AFR", "A321"), ("AFR", "A332"), ("AFR", "A359"), ("AFR", "B772"), ("AFR", "B77W"),
    ("AFR", "B789"), ("BAW", "B788"), ("BAW", "B789"), ("BAW", "B78X"), ("BAW", "A35K"),
    ("BAW", "B77W"), ("KLM", "A332"), ("KLM", "A333"), ("KLM", "B772"), ("KLM", "B77W"),
    ("KLM", "B789"), ("KLM", "B78X"), ("IBE", "A332"), ("IBE", "A333"), ("IBE", "A359"),
    ("ITY", "A221"), ("ITY", "A339"), ("ITY", "A359"), ("LOT", "B788"), ("LOT", "B789"),
    ("SAS", "A333"), ("SAS", "A359"), ("EWG", "A332"), ("EWG", "A333"), ("CFG", "A339"),
    ("CFG", "B753"), ("CFG", "B763"), ("UAE", "A388"), ("ETD", "B78X"), ("ETD", "A359"),
    ("UAL", "B763"), ("UAL", "B764"), ("AAL", "B788"), ("DAL", "A332"), ("DAL", "A339"),
    ("DAL", "B763"), ("DAL", "B764"), ("ACA", "A333"), ("ETH", "B763"), ("ETH", "B77W"),
    ("AIC", "B77W"), ("AIC", "A359"), ("CHH", "A333"), ("MMZ", "B763"), ("MMZ", "B772"),
    ("MMZ", "A332"), ("MMZ", "A333"), ("MMZ", "A343"), ("OAE", "B763"), ("OAE", "B772"),
    ("FDX", "MD11"), ("UPS", "MD11"), ("UPS", "B748"), ("CLX", "B748")
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f: return json.load(f)
        except Exception: pass
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def send_telegram_alert(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown", "disable_web_page_preview": True}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def is_target_aircraft(hex_code: str, reg: str, ac_type: str, callsign: str, is_military: bool, category: str) -> bool:
    if hex_code in SPECIAL_HEXES: return True
    if reg and reg in SPECIAL_REGS: return True
    if ac_type and ac_type.startswith(TARGET_TYPE_PREFIXES): return True
    if callsign and callsign[:3] in TARGET_AIRLINES: return True
    if callsign and ac_type:
        for prefix, actype in IRREGULAR_COMBOS:
            if callsign.startswith(prefix) and ac_type.startswith(actype): return True
    if is_military and category in ["A3", "A4", "A5"]: return True
    return False

def get_flight_route(registration: str) -> str:
    if not registration or registration == "N/A": return "Unknown Route"
    try:
        url = f"https://api.flightradar24.com/common/v1/flight/list.json?query={registration}&fetchBy=reg"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "application/json"}
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            flights = res.json().get("result", {}).get("response", {}).get("data", [])
            for f in flights:
                dep_time = f.get("time", {}).get("real", {}).get("departure")
                arr_time = f.get("time", {}).get("real", {}).get("arrival")
                if dep_time is not None and arr_time is None:
                    orig = f.get("airport", {}).get("origin", {}).get("code", {}).get("iata", "N/A") if f.get("airport", {}).get("origin") else "N/A"
                    dest = f.get("airport", {}).get("destination", {}).get("code", {}).get("iata", "N/A") if f.get("airport", {}).get("destination") else "N/A"
                    flight_no = f.get("identification", {}).get("number", {}).get("default", "N/A")
                    if flight_no != "N/A": return f"{orig} ➡️ {dest} ({flight_no})"
                    return f"{orig} ➡️ {dest}"
    except: pass
    return "Unknown Route"

def calculate_distance_eta(lat, lon, gs):
    if not lat or not lon or not isinstance(gs, (int, float)) or gs <= 0:
        return "Unknown", "Unknown"
    
    R = 3440.065 # Earth radius in NM
    dlat = math.radians(TLV_LAT - lat)
    dlon = math.radians(TLV_LON - lon)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(TLV_LAT)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    dist_nm = R * c
    eta_mins = (dist_nm / gs) * 60
    return f"{int(dist_nm)} NM", f"~{int(eta_mins)} mins"

def fetch_adsb_data(url: str):
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if res.status_code == 200: return res.json().get("ac", [])
    except: pass
    return []

def poll_sky():
    global tracked_flights
    geofence_ac = fetch_adsb_data(f"https://api.adsb.lol/v2/lat/{TLV_LAT}/lon/{TLV_LON}/dist/{TLV_RADIUS_NM}")
    geofence_hexes = {ac.get("hex", "").lower() for ac in geofence_ac if ac.get("hex")}
    type_ac = fetch_adsb_data(f"https://api.adsb.lol/v2/type/{GLOBAL_FETCH_TYPES}")
    
    reg_ac = []
    batch_size = 50
    for i in range(0, len(SPECIAL_REGS), batch_size):
        batch = SPECIAL_REGS[i:i+batch_size]
        batch_ac = fetch_adsb_data(f"https://api.adsb.lol/v2/reg/{','.join(batch)}")
        if batch_ac: reg_ac.extend(batch_ac)
    
    all_aircraft = {}
    for ac in geofence_ac + type_ac + reg_ac:
        hex_code = ac.get("hex", "").lower()
        if hex_code: all_aircraft[hex_code] = ac

    currently_airborne_targets = set()

    for hex_code, ac in all_aircraft.items():
        reg = ac.get("r", "").upper()
        ac_type = ac.get("t", "").upper()
        callsign = ac.get("flight", "").strip().upper()
        squawk = str(ac.get("squawk", ""))
        category = ac.get("category", "")
        is_military = bool(ac.get("dbFlags", 0) & 1)
        
        in_geofence = hex_code in geofence_hexes
        is_emergency = squawk in ["7700", "7600", "7500"]
        is_target = is_target_aircraft(hex_code, reg, ac_type, callsign, is_military, category)
        
        if not is_target and not (in_geofence and is_emergency): continue
            
        alt = ac.get("alt_baro", "Unknown")
        gs = ac.get("gs", "Unknown")
        lat = ac.get("lat")
        lon = ac.get("lon")

        is_airborne = False
        try:
            if isinstance(alt, (int, float)) and alt > 0: is_airborne = True
            elif isinstance(alt, str) and alt.isdigit() and int(alt) > 0: is_airborne = True
        except: pass

        if not is_airborne: continue
        
        currently_airborne_targets.add(hex_code)
        
        if hex_code not in tracked_flights:
            tracked_flights[hex_code] = {
                "callsign": callsign, 
                "route_checked": False, 
                "alerted": False, 
                "route": "Unknown Route", 
                "emergency_alerted": False
            }
        
        state = tracked_flights[hex_code]
        dist_str, eta_str = calculate_distance_eta(lat, lon, gs)
        
        if is_target:
            if not state.get("route_checked"):
                state["route"] = get_flight_route(reg)
                state["route_checked"] = True
                
            route = state["route"]
            route_to_tlv = "TLV" in route or "LLBG" in route
            is_hidden_route = (route == "Unknown Route")
            
            is_heavy_military = is_military and category in ["A3", "A4", "A5"]
            military_prefixes = ('C17', 'C5', 'A124', 'K35R', 'C135', 'A400', 'IL76', 'IL96', 'A3ST', 'A337', 'C130', 'C30J')
            is_military_or_special = (reg in SPECIAL_REGS) or (hex_code in SPECIAL_HEXES) or ac_type.startswith(military_prefixes) or is_heavy_military
            
            should_alert = route_to_tlv or (in_geofence and is_hidden_route and is_military_or_special)

            if should_alert and not state.get("alerted"):
                trigger_reason = "🌐 *Target Route matches TLV!*" if route_to_tlv else "📍 *Unknown Target in TLV Airspace!*"
                msg_reg = reg if reg else "Unknown"
                msg_type = ac_type if ac_type else "Unknown"
                
                alert_msg = (
                    f"🚨 *Target Aircraft Detected!*\n"
                    f"{trigger_reason}\n\n"
                    f"*Registration:* {msg_reg} ({msg_type})\n"
                    f"*Callsign:* {callsign}\n"
                    f"*Route:* {route}\n"
                    f"*Distance to TLV:* {dist_str}\n"
                    f"*ETA:* {eta_str}\n"
                    f"*Altitude:* {alt} ft\n"
                    f"*Speed:* {gs} kts\n\n"
                    f"[Track on ADSB Exchange](https://globe.adsbexchange.com/?icao={hex_code})"
                )
                send_telegram_alert(alert_msg)
                state["alerted"] = True

        if in_geofence and is_emergency and not state.get("emergency_alerted", False):
            msg_reg = reg if reg else "Unknown"
            msg_type = ac_type if ac_type else "Unknown"
            squawk_type = "GENERAL EMERGENCY" if squawk == "7700" else "RADIO FAILURE" if squawk == "7600" else "HIJACKING"
            
            alert_msg = (
                f"⚠️ *EMERGENCY SQUAWK NEAR TLV!* ⚠️\n"
                f"Aircraft broadcasting {squawk} ({squawk_type})\n\n"
                f"*Registration:* {msg_reg} ({msg_type})\n"
                f"*Callsign:* {callsign}\n"
                f"*Distance to TLV:* {dist_str}\n"
                f"*ETA:* {eta_str}\n"
                f"*Altitude:* {alt} ft\n"
                f"*Speed:* {gs} kts\n\n"
                f"[Track on ADSB Exchange](https://globe.adsbexchange.com/?icao={hex_code})"
            )
            send_telegram_alert(alert_msg)
            state["emergency_alerted"] = True

    for hex_code in list(tracked_flights.keys()):
        if hex_code not in currently_airborne_targets:
            del tracked_flights[hex_code]

def main():
    global tracked_flights
    logging.info("Starting GitHub Actions Tracker Run...")
    tracked_flights = load_state()
    poll_sky()
    save_state(tracked_flights)
    logging.info("Run complete. State saved.")

if __name__ == "__main__":
    main()
