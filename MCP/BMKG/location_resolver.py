from difflib import get_close_matches
import pandas as pd 
import re

path = '/Users/nicholasterrencesalim/source tree/lang-project/data/kode-wilayah.csv'

df = pd.read_csv(path)

# ADM4 = kode yang punya 3 titik (contoh: 11.01.01.2001)
df["dot_count"] = df["kode"].astype(str).str.count(r"\.")
ADM4_DF = df[df["dot_count"] == 3].copy()


# bikin kolom lowercase untuk matching
ADM4_DF["nama_lower"] = ADM4_DF["nama"].str.lower()

# index dictionary biar cepat
ADM4_NAME_INDEX = {
    row["nama_lower"]: row["kode"]
    for _, row in ADM4_DF.iterrows()
}

# ADM4_LOOKUP = {
#     "yogyakarta": "34.71.01.1001",
#     "jogja": "34.71.01.1001",
#     "yogya": "34.71.01.1001",
#     "bandung": "32.73.01.1001",
#     "kemayoran": "31.71.03.1001",
# }

def extract_location(text: str) -> str:
    text = text.lower()
    
    text = re.sub(r"[^a-z\s]", "", text)
    
    words = text.split()

    stopwords = [
        "bagaimana", "cuaca", "di", "ke", "kota",
        "hari", "ini", "gimana", "sekarang"
    ]
    
    filtered = [w for w in words if w not in stopwords]

    # for w in stopwords:
    #     text = text.replace(w, "")

    return " ".join(filtered).strip()

def normalize(text: str) -> str :
    text = text.lower()
    text = re.sub(r"[^a-z\s]", "", text)
    text = text.replace("kota", "")
    return text.strip()

def getLocation(query: str):
    # print('query: ', query)
    if isinstance(query, list):
        query = query[0] if query else ""
        
    if not isinstance(query, str):
        return {"status": "NOT_FOUND"}
    
    q = query.lower().strip()
    
    locations = extract_location(query)
    
    print('loc: ', locations)
    
    if locations in ADM4_NAME_INDEX:
        return {
            "status": "FOUND",
            "adm4": ADM4_NAME_INDEX[locations]
        }
    
    #for partial match
    candidates = [
        name for name in ADM4_NAME_INDEX
        if locations in name
    ]
    
    # if len(candidates) == 1:
    #     return {
    #         'status': "FOUND",
    #         'adm4': ADM4_NAME_INDEX[candidates[0]]
    #     }
    
    matches = get_close_matches(locations, ADM4_NAME_INDEX.keys(), n=1, cutoff=0.6)
    
    print('matches: ', matches)

    if matches:
        return {
            "status": "FOUND",
            "adm4": ADM4_NAME_INDEX[matches[0]]
        }
    
    if len(candidates) > 1:
        return {
            "status": "AMBIGUOUS",
            "candidates": candidates
        }
    return {"status": "NOT_FOUND"} 

# def get_adm4_candidates(user_text: str):
    
#     location = extract_location(user_text)
    
#     print('extract', location)
    
#     if not location:
#         return {"status": "NOT_FOUND"}

#     norm =  normalize(location)
    
#     # 1. exact
#     if norm in ADM4_LOOKUP:
#         return {
#             "status": "FOUND",
#             "adm4": ADM4_LOOKUP[norm],
#             "name": norm
#         }
        
#     candidates = get_close_matches(
#         norm,
#         ADM4_LOOKUP.keys(),
#         n = 3,
#         cutoff= 0.6
#     )
    
#     if candidates:
#         return {
#             "status": "AMBIGUOUS",
#             "candidates": candidates
#         }
        
#     return {
#         "status": "NOT_FOUND"
#     }