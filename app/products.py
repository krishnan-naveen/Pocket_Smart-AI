"""Simulated product catalog.

The project brief asks for "mock API calls or simulated scraping from Amazon, IKEA, Zomato, etc."
Real scraping of those sites is against their terms of service, so this module returns a small,
hand-written catalog. Prices are illustrative (INR). Links are real *search* URLs on each platform.
"""
from urllib.parse import quote_plus

# platform -> search URL template
_SEARCH = {
    "IKEA": "https://www.ikea.com/in/en/search/?q={q}",
    "Amazon": "https://www.amazon.in/s?k={q}",
    "Flipkart": "https://www.flipkart.com/search?q={q}",
    "Pepperfry": "https://www.pepperfry.com/site_product/search?q={q}",
    "Zomato": "https://www.zomato.com/search?q={q}",
    "Swiggy": "https://www.swiggy.com/search?query={q}",
    "OYO": "https://www.oyorooms.com/search?query={q}",
    "Tanishq": "https://www.tanishq.co.in/search?q={q}",
    "CaratLane": "https://www.caratlane.com/search?q={q}",
    "Myntra": "https://www.myntra.com/{q}",
    "Nykaa": "https://www.nykaa.com/search/result/?q={q}",
}


def _item(id_, name, category, platform, price, tags, unit="item", **extra):
    return {
        "id": id_,
        "name": name,
        "category": category,
        "platform": platform,
        "price": price,
        "unit": unit,  # "item" | "per_person" | "per_event"
        "tags": tags,
        "url": _SEARCH[platform].format(q=quote_plus(name)),
        **extra,
    }


# ---------------------------------------------------------------- HOME
HOME_ITEMS = [
    # living room
    _item("h1", "3-seater fabric sofa", "furniture", "IKEA", 24999, ["living room", "modern", "cozy"]),
    _item("h2", "Compact coffee table", "furniture", "Amazon", 3999, ["living room", "modern", "minimal"]),
    _item("h3", "TV unit with storage", "furniture", "Pepperfry", 8999, ["living room", "modern", "traditional"]),
    _item("h4", "Handloom cotton cushion covers (set of 5)", "decor", "Amazon", 799, ["living room", "traditional", "cozy"]),
    _item("h5", "Abstract canvas wall art", "decor", "Flipkart", 1499, ["living room", "modern", "minimal"]),
    _item("h6", "Arc floor lamp", "lighting", "IKEA", 4290, ["living room", "modern", "minimal"]),
    _item("h7", "Jute area rug 5x7 ft", "decor", "Amazon", 2499, ["living room", "bedroom", "cozy", "traditional"]),
    # bedroom
    _item("h8", "Queen size storage bed", "furniture", "Pepperfry", 21999, ["bedroom", "modern", "traditional"]),
    _item("h9", "Memory foam mattress (queen)", "furniture", "Amazon", 11999, ["bedroom", "cozy", "modern"]),
    _item("h10", "Bedside table with drawer", "furniture", "IKEA", 3490, ["bedroom", "minimal", "modern"]),
    _item("h11", "Blackout curtains (pair)", "decor", "Flipkart", 1299, ["bedroom", "living room", "minimal"]),
    _item("h12", "Warm LED bedside lamp", "lighting", "Amazon", 899, ["bedroom", "cozy", "minimal"]),
    _item("h13", "Cotton bedsheet set with pillow covers", "decor", "Flipkart", 1199, ["bedroom", "cozy", "traditional"]),
    # kitchen
    _item("h14", "4-seater dining set", "furniture", "Pepperfry", 15999, ["kitchen", "traditional", "modern"]),
    _item("h15", "Stainless steel kitchen rack", "furniture", "Amazon", 2799, ["kitchen", "minimal", "modern"]),
    _item("h16", "Under-cabinet LED strip lights", "lighting", "Amazon", 699, ["kitchen", "modern", "minimal"]),
    _item("h17", "Ceramic canister set", "decor", "IKEA", 1290, ["kitchen", "minimal", "cozy"]),
    _item("h18", "Herb planter shelf", "decor", "Flipkart", 999, ["kitchen", "cozy", "traditional"]),
    # study / home office
    _item("h19", "Ergonomic office chair", "furniture", "Amazon", 7499, ["study", "modern", "minimal"]),
    _item("h20", "Study desk with shelves", "furniture", "IKEA", 8990, ["study", "minimal", "modern"]),
    _item("h21", "Adjustable LED desk lamp", "lighting", "Amazon", 1199, ["study", "minimal", "modern"]),
    _item("h22", "Wall-mounted bookshelf", "furniture", "Pepperfry", 3299, ["study", "traditional", "minimal"]),
    _item("h23", "Desk organizer set", "decor", "Flipkart", 499, ["study", "minimal", "cozy"]),
    _item("h24", "Indoor money plant with pot", "decor", "Amazon", 449, ["study", "living room", "bedroom", "kitchen", "cozy"]),
]

# ---------------------------------------------------------------- PARTY
PARTY_ITEMS = [
    # venues (per event)
    _item("p1", "Community hall booking (4 hours)", "venue", "OYO", 12000, ["birthday", "housewarming", "anniversary", "baby shower"], "per_event", capacity=80),
    _item("p2", "Rooftop terrace party space", "venue", "OYO", 18000, ["birthday", "anniversary", "corporate"], "per_event", capacity=50),
    _item("p3", "Banquet hall (evening)", "venue", "OYO", 45000, ["wedding", "anniversary", "corporate", "baby shower"], "per_event", capacity=200),
    _item("p4", "Home party setup (no venue fee)", "venue", "Amazon", 0, ["birthday", "housewarming", "baby shower"], "per_event", capacity=25),
    # food (per person)
    _item("p5", "Veg buffet (starter + main + dessert)", "food", "Zomato", 450, ["birthday", "housewarming", "wedding", "anniversary", "baby shower", "corporate"], "per_person"),
    _item("p6", "Non-veg buffet combo", "food", "Swiggy", 650, ["birthday", "anniversary", "corporate", "wedding"], "per_person"),
    _item("p7", "Snacks and mocktails platter", "food", "Zomato", 250, ["birthday", "corporate", "baby shower", "housewarming"], "per_person"),
    _item("p8", "South Indian meals (banana leaf)", "food", "Swiggy", 350, ["housewarming", "wedding", "anniversary"], "per_person"),
    # decor (per event)
    _item("p9", "Balloon arch and backdrop kit", "decor", "Amazon", 1499, ["birthday", "baby shower", "anniversary"], "per_event"),
    _item("p10", "LED fairy lights (10 m x 4)", "decor", "Flipkart", 799, ["birthday", "wedding", "housewarming", "anniversary"], "per_event"),
    _item("p11", "Flower garland and table centerpieces", "decor", "Amazon", 2499, ["wedding", "housewarming", "anniversary", "baby shower"], "per_event"),
    _item("p12", "Photo booth props and banner", "decor", "Flipkart", 699, ["birthday", "corporate", "baby shower"], "per_event"),
    _item("p13", "Return-gift hampers", "decor", "Amazon", 120, ["birthday", "baby shower", "housewarming"], "per_person"),
    _item("p14", "Theme table decor and stage lighting", "decor", "Amazon", 5999, ["wedding", "corporate", "anniversary"], "per_event"),
]

# ---------------------------------------------------------------- JEWELRY
JEWELRY_ITEMS = [
    _item("j1", "22K gold plated jhumka earrings", "earrings", "Myntra", 1499, ["wedding", "festival", "traditional"]),
    _item("j2", "Kundan choker necklace set", "necklace", "Amazon", 2999, ["wedding", "festival", "traditional"]),
    _item("j3", "Temple jewellery long haram", "necklace", "Flipkart", 3499, ["festival", "wedding", "traditional"]),
    _item("j4", "Diamond solitaire stud earrings (14K)", "earrings", "CaratLane", 14999, ["party", "office", "wedding", "modern"]),
    _item("j5", "Sterling silver pendant with chain", "necklace", "Amazon", 1299, ["office", "casual", "modern"]),
    _item("j6", "Rose gold minimalist bracelet", "bracelet", "Myntra", 1199, ["office", "casual", "party", "modern"]),
    _item("j7", "American diamond cocktail ring", "ring", "Flipkart", 999, ["party", "wedding", "modern"]),
    _item("j8", "Oxidised silver statement earrings", "earrings", "Myntra", 599, ["casual", "festival", "boho"]),
    _item("j9", "Gold chain with pearl drop (18K)", "necklace", "Tanishq", 18999, ["wedding", "festival", "traditional", "office"]),
    _item("j10", "Pearl stud earrings", "earrings", "Amazon", 799, ["office", "casual", "wedding", "modern"]),
    _item("j11", "Bangles set (glass, 12 pcs)", "bangles", "Flipkart", 449, ["festival", "casual", "traditional"]),
    _item("j12", "Gold-tone kada bangle", "bangles", "Myntra", 1799, ["festival", "wedding", "party", "traditional"]),
    _item("j13", "Statement layered necklace", "necklace", "Amazon", 899, ["party", "casual", "boho", "modern"]),
    _item("j14", "Polki bridal set (necklace + earrings + maang tikka)", "set", "Tanishq", 39999, ["wedding", "traditional"]),
]

CATALOGS = {"home": HOME_ITEMS, "party": PARTY_ITEMS, "jewelry": JEWELRY_ITEMS}

HOME_ROOMS = ["living room", "bedroom", "kitchen", "study"]
HOME_STYLES = ["modern", "minimal", "traditional", "cozy"]
PARTY_EVENTS = ["birthday", "wedding", "anniversary", "housewarming", "baby shower", "corporate"]
JEWELRY_OCCASIONS = ["wedding", "festival", "party", "office", "casual"]
JEWELRY_STYLES = ["traditional", "modern", "boho"]
