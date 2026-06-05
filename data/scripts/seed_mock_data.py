"""
seed_mock_data.py - Generate mock data CSV for banking transaction agent demo.
Run: python seed_mock_data.py
Output: ../csv/ folder with 16 CSV files + README.md
"""

import csv
import json
import uuid
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONSTANTS
# ============================================================

SEED = 42
random.seed(SEED)

FIXED_NOW = datetime(2026, 6, 1, 12, 0, 0)
OUTPUT_DIR = Path(os.path.dirname(__file__)).parent / "csv"

BANK_MAP = {
    "VCB": "Vietcombank",
    "TCB": "Techcombank",
    "BIDV": "BIDV",
    "CTG": "VietinBank",
    "VPB": "VPBank",
    "MB": "MB Bank",
    "ACB": "ACB",
    "STB": "Sacombank",
    "TPB": "TPBank",
    "VIB": "VIB",
}

CARRIER_MAP = {
    "09": "VIETTEL",
    "03": "VIETTEL",
    "07": "MOBIFONE",
    "08": "VINAPHONE",
}

MCC_MAP = {
    "FOOD": "5812",
    "TRANSPORT": "4121",
    "SHOPPING": "5691",
    "ENTERTAINMENT": "7832",
    "GROCERY": "5411",
    "ECOMMERCE": "5399",
    "DIGITAL_WALLET": "6012",
    "ELECTRONICS": "5732",
}

BANK_CODES = list(BANK_MAP.keys())

# Vietnamese name components
HO = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Vo", "Dang", "Bui", "Do", "Ngo"]
DEM = ["Van", "Thi", "Duc", "Minh", "Quoc", "Thanh", "Ngoc", "Hoang", "Anh", "Huu"]
TEN = ["An", "Binh", "Cuong", "Dung", "Em", "Giang", "Hoa", "Khoa", "Linh", "Minh",
       "Nam", "Oanh", "Phuc", "Quang", "Son", "Tuan", "Uyen", "Vy", "Xuan", "Yen",
       "Hieu", "Thao", "Duc", "Lan", "Hai", "Trang", "Long", "Mai", "Hung", "Nhi"]

MERCHANT_NAMES = {
    "FOOD": ["Highlands Coffee", "The Coffee House", "Pho 24", "Baemin", "GrabFood",
             "Jollibee", "KFC", "Lotteria", "Pizza 4Ps", "Phuc Long",
             "Starbucks", "GoGi House", "Kichi Kichi", "McDonalds", "Burger King",
             "Com Tam Ba Ghien", "Banh Mi Huynh Hoa", "Tra Sua Bobapop", "Hai Di Lao", "Sumo BBQ"],
    "TRANSPORT": ["Grab", "Be", "Gojek", "Xanh SM", "Mai Linh",
                  "Vinasun", "AhaMove", "Lalamove", "Vietjet Air", "Vietnam Airlines",
                  "VNR Booking", "Bamboo Airways"],
    "SHOPPING": ["Shopee", "Lazada", "Tiki", "Sendo", "Uniqlo",
                 "Zara", "H&M", "Muji", "Vincom Center", "Aeon Mall",
                 "Lotte Mart", "Big C"],
    "ENTERTAINMENT": ["CGV Cinemas", "Lotte Cinema", "Galaxy Cinema", "Spotify Vietnam",
                      "Netflix", "FPT Play", "VieON", "Casino Online"],
    "GROCERY": ["WinMart", "Bach Hoa Xanh", "Co.op Mart", "Mega Market",
                "Family Mart", "Circle K", "GS25", "7-Eleven"],
    "ECOMMERCE": ["Shopee", "Lazada", "Tiki", "Sendo", "Thegioididong",
                  "Cellphones", "FPT Shop", "Unknown Merchant"],
    "DIGITAL_WALLET": ["MoMo", "ZaloPay", "VNPay", "ShopeePay",
                       "Viettel Money", "VNPT Pay", "Payoo", "Overseas Shop"],
    "ELECTRONICS": ["Thegioididong", "Dien May Xanh", "Cellphones", "FPT Shop"],
}

CITIES = ["Ha Noi", "Ho Chi Minh", "Da Nang", "Hai Phong", "Can Tho"]
CITY_WEIGHTS = [40, 40, 10, 5, 5]

# ============================================================
# HELPERS
# ============================================================


def make_id(table_name, index):
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{table_name}-{index}"))


def random_timestamp(start, end):
    delta = end - start
    seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=seconds)


def gen_phone():
    prefix = random.choice(["09", "03", "07", "08"])
    rest = "".join([str(random.randint(0, 9)) for _ in range(8)])
    return prefix + rest


def gen_account_no():
    length = random.randint(10, 13)
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


def gen_vn_name():
    return f"{random.choice(HO)} {random.choice(DEM)} {random.choice(TEN)}"


def write_csv(filename, rows, fieldnames):
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return filepath


# ============================================================
# DATA GENERATION
# ============================================================

# Storage
customers = []
accounts = []
cards = []
beneficiaries = []
merchants = []
billers = []
customer_biller_accounts = []
transaction_categories = []
transactions = []
action_requests = []
api_call_logs = []
audit_logs = []
fraud_reports = []
reported_accounts_list = []
reported_customers_list = []
fraud_decisions_list = []

# Lookup dicts
cust_by_cif = {}
accts_by_cif = {}
cards_by_cif = {}
benes_by_cif = {}
cba_by_cif = {}


def generate_customers():
    global customers, cust_by_cif
    for i in range(1, 101):
        cid = make_id("customers", i)
        cif = f"CIF{i:06d}"
        name = gen_vn_name()
        phone = gen_phone()
        slug = name.lower().replace(" ", ".")
        email = f"{slug}@example.com"

        r = random.random()
        if r < 0.10:
            kyc = "BASIC"
        elif r < 0.80:
            kyc = "VERIFIED"
        else:
            kyc = "ENHANCED"

        r2 = random.random()
        if r2 < 0.90:
            status = "ACTIVE"
        elif r2 < 0.97:
            status = "SUSPENDED"
        else:
            status = "CLOSED"

        created_at = random_timestamp(datetime(2023, 1, 1), datetime(2025, 11, 30))

        cust = {
            "customer_id": cid,
            "cif_no": cif,
            "full_name": name,
            "phone_number": phone,
            "email": email,
            "kyc_level": kyc,
            "status": status,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        customers.append(cust)
        cust_by_cif[cif] = cust


def generate_accounts():
    global accounts, accts_by_cif
    idx = 1
    for cust in customers:
        cif = cust["cif_no"]
        is_active = cust["status"] == "ACTIVE"
        num_accounts = random.randint(1, 3)
        accts_by_cif[cif] = []

        for j in range(num_accounts):
            aid = make_id("accounts", idx)
            acc_no = gen_account_no()

            if j == 0:
                acc_type = "PAYMENT"
            else:
                acc_type = random.choice(["PAYMENT", "SAVINGS"])

            balance = random.randint(500000, 500000000)
            avail = int(balance * random.uniform(0.85, 1.0))

            if j == 0 and is_active:
                status = "ACTIVE"
            else:
                r = random.random()
                if r < 0.90:
                    status = "ACTIVE"
                elif r < 0.97:
                    status = "FROZEN"
                else:
                    status = "CLOSED"

            opened_at = random_timestamp(
                datetime(2023, 1, 1),
                datetime(2025, 11, 30)
            )

            acc = {
                "account_id": aid,
                "account_no": acc_no,
                "cif_no": cif,
                "account_type": acc_type,
                "currency": "VND",
                "balance": balance,
                "available_balance": avail,
                "status": status,
                "opened_at": opened_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            accounts.append(acc)
            accts_by_cif[cif].append(acc)
            idx += 1


def generate_cards():
    global cards, cards_by_cif
    idx = 1
    # ~60% customers get cards
    cust_with_cards = random.sample(customers, 60)
    for cust in cust_with_cards:
        cif = cust["cif_no"]
        cards_by_cif.setdefault(cif, [])
        num_cards = random.randint(1, 2)

        # Get accounts for this customer
        cust_accts = [a for a in accts_by_cif.get(cif, []) if a["status"] == "ACTIVE"]
        if not cust_accts:
            cust_accts = accts_by_cif.get(cif, [])
        if not cust_accts:
            continue

        for _ in range(num_cards):
            cid = make_id("cards", idx)
            acc = random.choice(cust_accts)
            last4 = f"{random.randint(0, 9999):04d}"
            masked = f"**** **** **** {last4}"

            r = random.random()
            card_type = "DEBIT" if r < 0.60 else "CREDIT"

            r2 = random.random()
            if r2 < 0.40:
                network = "VISA"
            elif r2 < 0.70:
                network = "MASTERCARD"
            else:
                network = "NAPAS"

            if card_type == "CREDIT":
                credit_limit = random.randint(20000000, 200000000)
                available_limit = int(credit_limit * random.uniform(0.4, 1.0))
            else:
                credit_limit = None
                available_limit = None

            r3 = random.random()
            if r3 < 0.80:
                status = "ACTIVE"
            elif r3 < 0.95:
                status = "LOCKED"
            else:
                status = "EXPIRED"

            issued_at = random_timestamp(datetime(2023, 6, 1), datetime(2025, 11, 30))

            card = {
                "card_id": cid,
                "cif_no": cif,
                "account_no": acc["account_no"],
                "masked_card_no": masked,
                "card_type": card_type,
                "card_network": network,
                "credit_limit": credit_limit,
                "available_limit": available_limit,
                "status": status,
                "issued_at": issued_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            cards.append(card)
            cards_by_cif[cif].append(card)
            idx += 1


def generate_beneficiaries():
    global beneficiaries, benes_by_cif
    idx = 1
    nicknames_pool = ["Minh", "Me", "Anh Nam", "Tien nha", "Thue nha", "Bo",
                      "Em gai", "Anh trai", "Ban Hoa", "Tien hoc", "Chi Lan",
                      "Dong nghiep", "Tiet kiem", "Bao hiem"]

    # Ensure at least 20 customers have beneficiary named "Minh"
    active_custs = [c for c in customers if c["status"] == "ACTIVE"]

    # First 25 customers get a "Minh" beneficiary
    minh_customers = active_custs[:25]
    # First 5 of those get 2 "Minh" beneficiaries for ambiguity
    ambiguity_customers = minh_customers[:5]

    # 10 customers get "Tien nha" or "Thue nha"
    rent_customers = active_custs[25:35]

    for cust in customers:
        cif = cust["cif_no"]
        benes_by_cif.setdefault(cif, [])
        num_benes = random.randint(1, 5)

        for j in range(num_benes):
            bid = make_id("beneficiaries", idx)
            bene_name = gen_vn_name()
            bene_acc = gen_account_no()
            bank_code = random.choice(BANK_CODES)
            bank_name = BANK_MAP[bank_code]

            nickname = random.choice(nicknames_pool) if random.random() < 0.6 else None
            is_saved = random.random() < 0.70
            last_used = random_timestamp(datetime(2025, 12, 1), FIXED_NOW) if random.random() < 0.7 else None

            created_at = random_timestamp(datetime(2023, 6, 1), datetime(2025, 12, 31))

            bene = {
                "beneficiary_id": bid,
                "cif_no": cif,
                "beneficiary_name": bene_name,
                "beneficiary_account_no": bene_acc,
                "beneficiary_bank_code": bank_code,
                "beneficiary_bank_name": bank_name,
                "nickname": nickname,
                "is_saved": is_saved,
                "last_used_at": last_used.strftime("%Y-%m-%d %H:%M:%S") if last_used else "",
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            beneficiaries.append(bene)
            benes_by_cif[cif].append(bene)
            idx += 1

    # Ensure Minh beneficiaries
    for cust in minh_customers:
        cif = cust["cif_no"]
        bid = make_id("beneficiaries", idx)
        bank_code = random.choice(BANK_CODES)
        bene = {
            "beneficiary_id": bid,
            "cif_no": cif,
            "beneficiary_name": f"{random.choice(HO)} Van Minh",
            "beneficiary_account_no": gen_account_no(),
            "beneficiary_bank_code": bank_code,
            "beneficiary_bank_name": BANK_MAP[bank_code],
            "nickname": "Minh",
            "is_saved": True,
            "last_used_at": random_timestamp(datetime(2026, 4, 1), datetime(2026, 4, 30)).strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": random_timestamp(datetime(2024, 1, 1), datetime(2025, 6, 30)).strftime("%Y-%m-%d %H:%M:%S"),
        }
        beneficiaries.append(bene)
        benes_by_cif[cif].append(bene)
        idx += 1

    # Ambiguity: second "Minh" for first 5
    for cust in ambiguity_customers:
        cif = cust["cif_no"]
        bid = make_id("beneficiaries", idx)
        bank_code = random.choice(BANK_CODES)
        bene = {
            "beneficiary_id": bid,
            "cif_no": cif,
            "beneficiary_name": f"{random.choice(HO)} Thi Minh",
            "beneficiary_account_no": gen_account_no(),
            "beneficiary_bank_code": bank_code,
            "beneficiary_bank_name": BANK_MAP[bank_code],
            "nickname": "Minh",
            "is_saved": True,
            "last_used_at": random_timestamp(datetime(2026, 3, 1), datetime(2026, 4, 30)).strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": random_timestamp(datetime(2024, 1, 1), datetime(2025, 6, 30)).strftime("%Y-%m-%d %H:%M:%S"),
        }
        beneficiaries.append(bene)
        benes_by_cif[cif].append(bene)
        idx += 1

    # Rent beneficiaries
    for cust in rent_customers:
        cif = cust["cif_no"]
        bid = make_id("beneficiaries", idx)
        bank_code = random.choice(BANK_CODES)
        nick = random.choice(["Tien nha", "Thue nha"])
        bene = {
            "beneficiary_id": bid,
            "cif_no": cif,
            "beneficiary_name": gen_vn_name(),
            "beneficiary_account_no": gen_account_no(),
            "beneficiary_bank_code": bank_code,
            "beneficiary_bank_name": BANK_MAP[bank_code],
            "nickname": nick,
            "is_saved": True,
            "last_used_at": random_timestamp(datetime(2026, 4, 1), datetime(2026, 5, 31)).strftime("%Y-%m-%d %H:%M:%S"),
            "created_at": random_timestamp(datetime(2024, 1, 1), datetime(2025, 6, 30)).strftime("%Y-%m-%d %H:%M:%S"),
        }
        beneficiaries.append(bene)
        benes_by_cif[cif].append(bene)
        idx += 1


def generate_merchants():
    global merchants
    idx = 1
    categories = list(MERCHANT_NAMES.keys())
    cat_weights = [25, 15, 15, 10, 10, 10, 10, 5]

    used_names = set()
    while len(merchants) < 80:
        cat = random.choices(categories, weights=cat_weights, k=1)[0]
        name = random.choice(MERCHANT_NAMES[cat])
        if name in used_names and len(merchants) > 60:
            # Allow some duplicates with different cities after 60
            pass
        elif name in used_names:
            continue

        used_names.add(name)
        mid = make_id("merchants", idx)
        city = random.choices(CITIES, weights=CITY_WEIGHTS, k=1)[0]

        r = random.random()
        status = "ACTIVE" if r < 0.95 else "INACTIVE"

        merch = {
            "merchant_id": mid,
            "merchant_name": name,
            "merchant_category": cat,
            "mcc_code": MCC_MAP[cat],
            "city": city,
            "country": "VN",
            "status": status,
        }
        merchants.append(merch)
        idx += 1

        if len(merchants) >= 80:
            break

    # Ensure anomaly merchants
    anomaly_names = ["Casino Online", "Unknown Merchant", "Overseas Shop"]
    for aname in anomaly_names:
        found = any(m["merchant_name"] == aname for m in merchants)
        if not found and len(merchants) < 83:
            mid = make_id("merchants", idx)
            cat = random.choice(["ENTERTAINMENT", "ECOMMERCE", "DIGITAL_WALLET"])
            merch = {
                "merchant_id": mid,
                "merchant_name": aname,
                "merchant_category": cat,
                "mcc_code": MCC_MAP[cat],
                "city": random.choice(CITIES),
                "country": "VN",
                "status": "ACTIVE",
            }
            merchants.append(merch)
            idx += 1


def generate_billers():
    global billers
    biller_data = [
        ("EVN_HANOI", "EVN Ha Noi", "ELECTRICITY", "EVN"),
        ("EVN_HCMC", "EVN Ho Chi Minh", "ELECTRICITY", "EVN"),
        ("EVN_DANANG", "EVN Da Nang", "ELECTRICITY", "EVN"),
        ("EVN_SOUTH", "EVN Mien Nam", "ELECTRICITY", "EVN"),
        ("EVN_CENTRAL", "EVN Mien Trung", "ELECTRICITY", "EVN"),
        ("SAWACO", "SAWACO", "WATER", "SAWACO"),
        ("HAWACO", "HAWACO Ha Noi", "WATER", "HAWACO"),
        ("DAWACO", "DAWACO Da Nang", "WATER", "DAWACO"),
        ("BINH_DUONG_WATER", "Nuoc Binh Duong", "WATER", "BIWASE"),
        ("DONG_NAI_WATER", "Nuoc Dong Nai", "WATER", "DONAWACO"),
        ("VNPT_NET_HN", "VNPT Internet Ha Noi", "INTERNET", "VNPT"),
        ("VNPT_NET_HCM", "VNPT Internet HCM", "INTERNET", "VNPT"),
        ("FPT_NET_HN", "FPT Internet Ha Noi", "INTERNET", "FPT"),
        ("FPT_NET_HCM", "FPT Internet HCM", "INTERNET", "FPT"),
        ("VIETTEL_NET", "Viettel Internet", "INTERNET", "VIETTEL"),
        ("CMC_NET", "CMC Internet", "INTERNET", "CMC"),
        ("SCTV_NET", "SCTV Internet", "INTERNET", "SCTV"),
        ("VNPT_PHONE", "VNPT Dien thoai tra sau", "PHONE_POSTPAID", "VNPT"),
        ("VIETTEL_PHONE", "Viettel tra sau", "PHONE_POSTPAID", "VIETTEL"),
        ("MOBI_PHONE", "Mobifone tra sau", "PHONE_POSTPAID", "MOBIFONE"),
    ]
    for i, (code, name, btype, provider) in enumerate(biller_data, 1):
        bid = make_id("billers", i)
        billers.append({
            "biller_id": bid,
            "biller_code": code,
            "biller_name": name,
            "biller_type": btype,
            "provider": provider,
            "status": "ACTIVE",
        })


def generate_customer_biller_accounts():
    global customer_biller_accounts, cba_by_cif
    idx = 1
    prefix_map = {
        "ELECTRICITY": "PD",
        "WATER": "PW",
        "INTERNET": "PI",
        "PHONE_POSTPAID": "PP",
    }
    alias_map = {
        "ELECTRICITY": ["Nha Ha Noi", "Nha bo me", "Can ho", "Dien nha"],
        "WATER": ["Nuoc nha", "Nha Ha Noi", "Can ho"],
        "INTERNET": ["Internet nha", "FPT nha", "Wifi nha"],
        "PHONE_POSTPAID": ["Dien thoai", "So chinh", "So phu"],
    }

    evn_billers = [b for b in billers if b["biller_type"] == "ELECTRICITY"]

    for cust in customers:
        cif = cust["cif_no"]
        cba_by_cif.setdefault(cif, [])
        if cust["status"] != "ACTIVE":
            continue

        # Most customers get at least 1 EVN
        if random.random() < 0.85:
            evn = random.choice(evn_billers)
            prefix = prefix_map[evn["biller_type"]]
            bill_code = f"{prefix}{random.randint(100000000, 999999999)}"
            alias = random.choice(alias_map[evn["biller_type"]])
            status = "ACTIVE" if random.random() < 0.90 else "INACTIVE"
            last_paid = random_timestamp(datetime(2026, 3, 1), FIXED_NOW) if random.random() < 0.8 else None

            cba = {
                "customer_biller_account_id": make_id("customer_biller_accounts", idx),
                "cif_no": cif,
                "biller_id": evn["biller_id"],
                "customer_bill_code": bill_code,
                "alias": alias,
                "status": status,
                "last_paid_at": last_paid.strftime("%Y-%m-%d %H:%M:%S") if last_paid else "",
            }
            customer_biller_accounts.append(cba)
            cba_by_cif[cif].append(cba)
            idx += 1

        # Some get water/internet too
        extra_count = random.randint(0, 3)
        other_billers = [b for b in billers if b["biller_type"] != "ELECTRICITY"]
        for _ in range(extra_count):
            bl = random.choice(other_billers)
            prefix = prefix_map[bl["biller_type"]]
            bill_code = f"{prefix}{random.randint(100000000, 999999999)}"
            alias = random.choice(alias_map[bl["biller_type"]])
            status = "ACTIVE" if random.random() < 0.90 else "INACTIVE"
            last_paid = random_timestamp(datetime(2026, 1, 1), FIXED_NOW) if random.random() < 0.7 else None

            cba = {
                "customer_biller_account_id": make_id("customer_biller_accounts", idx),
                "cif_no": cif,
                "biller_id": bl["biller_id"],
                "customer_bill_code": bill_code,
                "alias": alias,
                "status": status,
                "last_paid_at": last_paid.strftime("%Y-%m-%d %H:%M:%S") if last_paid else "",
            }
            customer_biller_accounts.append(cba)
            cba_by_cif[cif].append(cba)
            idx += 1


def generate_transaction_categories():
    global transaction_categories
    cat_data = [
        ("FOOD", "An uong", "SPENDING"),
        ("SHOPPING", "Mua sam", "SPENDING"),
        ("TRANSPORT", "Di chuyen", "SPENDING"),
        ("ENTERTAINMENT", "Giai tri", "SPENDING"),
        ("GROCERIES", "Sieu thi / Tap hoa", "SPENDING"),
        ("CARD_PAYMENT", "Thanh toan the", "SPENDING"),
        ("TRANSFER", "Chuyen khoan", "TRANSFER"),
        ("FAMILY_TRANSFER", "Chuyen khoan gia dinh", "TRANSFER"),
        ("RENT", "Tien thue nha", "TRANSFER"),
        ("SALARY", "Luong", "INCOME"),
        ("INTEREST", "Lai suat", "INCOME"),
        ("REFUND", "Hoan tien", "INCOME"),
        ("CASH_DEPOSIT", "Nap tien mat", "INCOME"),
        ("BILL_ELECTRICITY", "Hoa don dien", "BILL"),
        ("BILL_WATER", "Hoa don nuoc", "BILL"),
        ("BILL_INTERNET", "Hoa don internet", "BILL"),
        ("PHONE_TOPUP", "Nap dien thoai", "BILL"),
        ("BANK_FEE", "Phi ngan hang", "FEE"),
        ("CASH_WITHDRAWAL", "Rut tien mat", "CASH"),
        ("OTHER", "Khac", "OTHER"),
    ]
    for i, (code, name, group) in enumerate(cat_data, 1):
        cid = make_id("transaction_categories", i)
        transaction_categories.append({
            "category_id": cid,
            "category_code": code,
            "category_name": name,
            "category_group": group,
        })


# Category lookup
def get_cat_id(code):
    for c in transaction_categories:
        if c["category_code"] == code:
            return c["category_id"]
    return None


def generate_transactions():
    global transactions
    idx = 1
    seq = 1

    # Distribution
    type_counts = {
        "BANK_TRANSFER": 1500,
        "CARD_PAYMENT": 1250,
        "BILL_PAYMENT": 600,
        "PHONE_TOPUP": 500,
        "CASH_WITHDRAWAL": 400,
        "CASH_DEPOSIT": 150,
        "SALARY": 250,
        "FEE": 200,
        "INTEREST": 100,
        "REFUND": 50,
    }

    # Month distribution: total 5000
    month_dist = {
        5: 2000,
        4: 1250,
        3: 750,
        2: 500,
        1: 300,
        12: 200,
    }

    active_custs = [c for c in customers if c["status"] == "ACTIVE"]
    active_cifs = [c["cif_no"] for c in active_custs]

    # Helper to get random timestamp in a month
    def rand_time_in_month(month, year=2026, day_range=None, hour_range=None):
        if year == 2025:
            days_in_month = 31
        else:
            if month in [1, 3, 5]:
                days_in_month = 31
            elif month == 2:
                days_in_month = 28
            else:
                days_in_month = 30

        if day_range:
            day = random.randint(day_range[0], min(day_range[1], days_in_month))
        else:
            day = random.randint(1, days_in_month)

        if hour_range:
            hour = random.randint(hour_range[0], hour_range[1])
        else:
            hour = random.randint(0, 23)

        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        return datetime(year, month, day, hour, minute, second)

    def pick_month():
        r = random.random()
        cum = 0
        for m, count in month_dist.items():
            cum += count / 5000
            if r < cum:
                return m
        return 5

    # Category mapping for card payments
    card_cat_map = {
        "FOOD": "FOOD",
        "TRANSPORT": "TRANSPORT",
        "SHOPPING": "SHOPPING",
        "ENTERTAINMENT": "ENTERTAINMENT",
        "GROCERY": "GROCERIES",
        "ECOMMERCE": "SHOPPING",
        "DIGITAL_WALLET": "CARD_PAYMENT",
        "ELECTRONICS": "SHOPPING",
    }

    # Biller type to category
    biller_cat_map = {
        "ELECTRICITY": "BILL_ELECTRICITY",
        "WATER": "BILL_WATER",
        "INTERNET": "BILL_INTERNET",
        "PHONE_POSTPAID": "BILL_INTERNET",
    }

    channels = ["MOBILE", "WEB", "ATM", "POS", "QR", "CARD"]

    # Pre-assign phone numbers for PHONE_TOPUP repeats
    phone_topup_numbers = {}
    for cif in active_cifs[:50]:
        phone_topup_numbers[cif] = gen_phone()

    # Generate all transactions by type
    all_txns = []

    # BANK_TRANSFER
    for _ in range(type_counts["BANK_TRANSFER"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        amount = random.randint(100000, 50000000)
        # 80% OUT, 20% IN
        direction = "OUT" if random.random() < 0.8 else "IN"

        cust_benes = benes_by_cif.get(cif, [])
        bene = random.choice(cust_benes) if cust_benes and random.random() < 0.7 else None

        if direction == "OUT":
            if bene:
                cp_acc = bene["beneficiary_account_no"]
                cp_bank = bene["beneficiary_bank_code"]
                cp_name = bene["beneficiary_name"]
                bene_id = bene["beneficiary_id"]
            else:
                cp_acc = gen_account_no()
                cp_bank = random.choice(BANK_CODES)
                cp_name = gen_vn_name()
                bene_id = ""
            desc = f"Chuyen tien cho {cp_name.split()[-1]}"
        else:
            cp_acc = gen_account_no()
            cp_bank = random.choice(BANK_CODES)
            cp_name = gen_vn_name()
            bene_id = ""
            desc = f"Nhan tien tu {cp_name.split()[-1]}"

        # Category
        if bene and bene.get("nickname") in ["Tien nha", "Thue nha"]:
            cat_code = "RENT"
        elif bene and bene.get("nickname") in ["Me", "Bo", "Em gai", "Anh trai"]:
            cat_code = "FAMILY_TRANSFER"
        else:
            cat_code = "TRANSFER"

        status = "SUCCESS" if random.random() < 0.95 else random.choice(["FAILED", "REVERSED", "PENDING"])

        all_txns.append({
            "type": "BANK_TRANSFER",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": direction,
            "category_code": cat_code,
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": bene_id,
            "counterparty_account_no": cp_acc,
            "counterparty_bank_code": cp_bank,
            "counterparty_name": cp_name,
            "channel": random.choice(["MOBILE", "WEB"]),
            "description": desc,
            "status": status,
        })

    # CARD_PAYMENT
    active_merchants = [m for m in merchants if m["status"] == "ACTIVE"]
    food_merchants = [m for m in active_merchants if m["merchant_category"] == "FOOD"]

    for i in range(type_counts["CARD_PAYMENT"]):
        cif = random.choice(active_cifs)
        cust_cards = cards_by_cif.get(cif, [])
        active_cards = [c for c in cust_cards if c["status"] == "ACTIVE"]
        if not active_cards:
            # Pick another customer with cards
            for alt_cif in active_cifs:
                alt_cards = [c for c in cards_by_cif.get(alt_cif, []) if c["status"] == "ACTIVE"]
                if alt_cards:
                    cif = alt_cif
                    active_cards = alt_cards
                    break
        if not active_cards:
            continue

        card = random.choice(active_cards)
        acc_no = card["account_no"]

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year, hour_range=(11, 22))

        merch = random.choice(active_merchants)
        amount = random.randint(20000, 5000000)

        cat_code = card_cat_map.get(merch["merchant_category"], "CARD_PAYMENT")
        status = "SUCCESS" if random.random() < 0.95 else random.choice(["FAILED", "REVERSED", "PENDING"])

        all_txns.append({
            "type": "CARD_PAYMENT",
            "cif_no": cif,
            "account_no": acc_no,
            "card_id": card["card_id"],
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "OUT",
            "category_code": cat_code,
            "merchant_id": merch["merchant_id"],
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": random.choice(["CARD", "POS", "QR"]),
            "description": f"Thanh toan tai {merch['merchant_name']}",
            "status": status,
        })

    # BILL_PAYMENT
    for _ in range(type_counts["BILL_PAYMENT"]):
        cif = random.choice(active_cifs)
        cust_cbas = cba_by_cif.get(cif, [])
        if not cust_cbas:
            # pick random biller
            bl = random.choice(billers)
            bill_code = f"PD{random.randint(100000000, 999999999)}"
        else:
            cba = random.choice(cust_cbas)
            bl = next((b for b in billers if b["biller_id"] == cba["biller_id"]), random.choice(billers))
            bill_code = cba["customer_bill_code"]

        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year, day_range=(1, 10))

        amount = random.randint(50000, 3000000)
        cat_code = biller_cat_map.get(bl["biller_type"], "BILL_ELECTRICITY")
        status = "SUCCESS" if random.random() < 0.95 else "FAILED"

        all_txns.append({
            "type": "BILL_PAYMENT",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "OUT",
            "category_code": cat_code,
            "merchant_id": "",
            "biller_id": bl["biller_id"],
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": random.choice(["MOBILE", "WEB"]),
            "description": f"Thanh toan hoa don {bl['biller_type'].lower()} {bl['biller_code']} {bill_code}",
            "status": status,
        })

    # PHONE_TOPUP
    topup_amounts = [10000, 20000, 50000, 100000, 200000, 500000]
    for _ in range(type_counts["PHONE_TOPUP"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        # Reuse phone for repeat pattern
        if cif in phone_topup_numbers and random.random() < 0.6:
            phone = phone_topup_numbers[cif]
        else:
            phone = gen_phone()
            if cif not in phone_topup_numbers:
                phone_topup_numbers[cif] = phone

        carrier = CARRIER_MAP.get(phone[:2], "VIETTEL")
        amount = random.choice(topup_amounts)
        status = "SUCCESS" if random.random() < 0.95 else "FAILED"

        all_txns.append({
            "type": "PHONE_TOPUP",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "OUT",
            "category_code": "PHONE_TOPUP",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": phone,
            "counterparty_bank_code": "",
            "counterparty_name": phone,
            "channel": random.choice(["MOBILE", "WEB"]),
            "description": f"Nap dien thoai {carrier} {phone}",
            "status": status,
        })

    # CASH_WITHDRAWAL
    for _ in range(type_counts["CASH_WITHDRAWAL"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        amount = random.randint(10, 200) * 50000
        status = "SUCCESS" if random.random() < 0.95 else "FAILED"

        all_txns.append({
            "type": "CASH_WITHDRAWAL",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "OUT",
            "category_code": "CASH_WITHDRAWAL",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": "ATM",
            "description": "Rut tien mat ATM",
            "status": status,
        })

    # CASH_DEPOSIT
    for _ in range(type_counts["CASH_DEPOSIT"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        amount = random.randint(1000000, 50000000)
        status = "SUCCESS"

        all_txns.append({
            "type": "CASH_DEPOSIT",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "IN",
            "category_code": "CASH_DEPOSIT",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": "ATM",
            "description": "Nap tien mat",
            "status": status,
        })

    # SALARY
    companies = ["FPT Software", "Viettel IDC", "VNG Corp", "VinGroup", "Masan Group",
                 "Techcombank", "VNPT", "CMC Corp", "KMS Technology", "NashTech"]
    for _ in range(type_counts["SALARY"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        # Salary day 1-5 or 25-30
        if random.random() < 0.5:
            day_range = (1, 5)
        else:
            day_range = (25, 28)
        txn_time = rand_time_in_month(month, year, day_range=day_range)

        amount = random.randint(8000000, 80000000)
        company = random.choice(companies)

        all_txns.append({
            "type": "SALARY",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "IN",
            "category_code": "SALARY",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": company,
            "channel": "MOBILE",
            "description": f"Luong thang {month:02d}/{year} - {company}",
            "status": "SUCCESS",
        })

    # FEE
    fee_descs = [
        ("Phi duy tri tai khoan", 11000),
        ("Phi SMS Banking", 11000),
        ("Phi thuong nien the", 150000),
        ("Phi chuyen tien ngoai he thong", None),
    ]
    for _ in range(type_counts["FEE"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        fee_desc, fee_amt = random.choice(fee_descs)
        if fee_amt is None:
            fee_amt = random.choice([5500, 11000, 16500, 22000, 33000])
        amount = fee_amt

        all_txns.append({
            "type": "FEE",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "OUT",
            "category_code": "BANK_FEE",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": "MOBILE",
            "description": fee_desc,
            "status": "SUCCESS",
        })

    # INTEREST
    for _ in range(type_counts["INTEREST"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["account_type"] == "SAVINGS"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        amount = random.randint(10000, 2000000)

        all_txns.append({
            "type": "INTEREST",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "IN",
            "category_code": "INTEREST",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": "MOBILE",
            "description": "Lai suat tiet kiem",
            "status": "SUCCESS",
        })

    # REFUND
    for _ in range(type_counts["REFUND"]):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        month = pick_month()
        year = 2025 if month == 12 else 2026
        txn_time = rand_time_in_month(month, year)

        amount = random.randint(20000, 5000000)

        all_txns.append({
            "type": "REFUND",
            "cif_no": cif,
            "account_no": acc["account_no"],
            "card_id": "",
            "transaction_time": txn_time,
            "amount": amount,
            "direction": "IN",
            "category_code": "REFUND",
            "merchant_id": "",
            "biller_id": "",
            "beneficiary_id": "",
            "counterparty_account_no": "",
            "counterparty_bank_code": "",
            "counterparty_name": "",
            "channel": "MOBILE",
            "description": "Hoan tien giao dich",
            "status": "SUCCESS",
        })

    # Add anomaly transactions (30+)
    anomaly_merchants = [m for m in merchants if m["merchant_name"] in ["Casino Online", "Unknown Merchant", "Overseas Shop"]]
    if not anomaly_merchants:
        anomaly_merchants = active_merchants[:3]

    for _ in range(35):
        cif = random.choice(active_cifs)
        cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        if not cust_accts:
            cust_accts = accts_by_cif[cif]
        acc = random.choice(cust_accts)

        # Anomaly: 2-5am, large amount, new recipient
        month = random.choice([4, 5])
        txn_time = rand_time_in_month(month, 2026, hour_range=(2, 5))
        amount = random.randint(20000000, 100000000)

        atype = random.choice(["BANK_TRANSFER", "CARD_PAYMENT"])
        if atype == "BANK_TRANSFER":
            all_txns.append({
                "type": "BANK_TRANSFER",
                "cif_no": cif,
                "account_no": acc["account_no"],
                "card_id": "",
                "transaction_time": txn_time,
                "amount": amount,
                "direction": "OUT",
                "category_code": "TRANSFER",
                "merchant_id": "",
                "biller_id": "",
                "beneficiary_id": "",  # new recipient
                "counterparty_account_no": gen_account_no(),
                "counterparty_bank_code": random.choice(BANK_CODES),
                "counterparty_name": gen_vn_name(),
                "channel": "MOBILE",
                "description": "Chuyen tien gap",
                "status": "SUCCESS",
            })
        else:
            cust_cards = [c for c in cards_by_cif.get(cif, []) if c["status"] == "ACTIVE"]
            if not cust_cards:
                continue
            card = random.choice(cust_cards)
            merch = random.choice(anomaly_merchants) if anomaly_merchants else random.choice(active_merchants)
            cat_code = card_cat_map.get(merch["merchant_category"], "CARD_PAYMENT")
            all_txns.append({
                "type": "CARD_PAYMENT",
                "cif_no": cif,
                "account_no": card["account_no"],
                "card_id": card["card_id"],
                "transaction_time": txn_time,
                "amount": amount,
                "direction": "OUT",
                "category_code": cat_code,
                "merchant_id": merch["merchant_id"],
                "biller_id": "",
                "beneficiary_id": "",
                "counterparty_account_no": "",
                "counterparty_bank_code": "",
                "counterparty_name": "",
                "channel": "CARD",
                "description": f"Thanh toan tai {merch['merchant_name']}",
                "status": "SUCCESS",
            })

    # Sort by time and assign IDs
    all_txns.sort(key=lambda x: x["transaction_time"])

    for txn_data in all_txns:
        tid = make_id("transactions", idx)
        month = txn_data["transaction_time"].month
        year = txn_data["transaction_time"].year
        ref = f"TXN{year}{month:02d}{seq:06d}"

        cat_id = get_cat_id(txn_data["category_code"])
        txn_time = txn_data["transaction_time"]
        created_at = txn_time + timedelta(seconds=random.randint(1, 10))

        # balance_after for recent transactions (month 5)
        balance_after = ""
        if month == 5 and random.random() < 0.5:
            balance_after = random.randint(1000000, 200000000)
        elif month == 4 and random.random() < 0.3:
            balance_after = random.randint(1000000, 200000000)

        ext_ref = ""
        if txn_data["status"] == "SUCCESS" and random.random() < 0.8:
            type_abbr = txn_data["type"][:3].upper()
            ext_ref = f"EXT{type_abbr}{seq:06d}"

        txn = {
            "transaction_id": tid,
            "transaction_ref": ref,
            "cif_no": txn_data["cif_no"],
            "account_no": txn_data["account_no"],
            "card_id": txn_data["card_id"],
            "transaction_time": txn_time.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": txn_data["amount"],
            "currency": "VND",
            "direction": txn_data["direction"],
            "transaction_type": txn_data["type"],
            "category_id": cat_id,
            "merchant_id": txn_data["merchant_id"],
            "biller_id": txn_data["biller_id"],
            "beneficiary_id": txn_data["beneficiary_id"],
            "counterparty_account_no": txn_data["counterparty_account_no"],
            "counterparty_bank_code": txn_data["counterparty_bank_code"],
            "counterparty_name": txn_data["counterparty_name"],
            "channel": txn_data["channel"],
            "description": txn_data["description"],
            "status": txn_data["status"],
            "balance_after": balance_after,
            "external_reference": ext_ref,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
        transactions.append(txn)
        idx += 1
        seq += 1


def generate_action_requests():
    global action_requests
    idx = 1
    active_cifs = [c["cif_no"] for c in customers if c["status"] == "ACTIVE"]

    user_texts = {
        "TRANSFER": [
            "Chuyen cho Minh 2 trieu nhu thang truoc",
            "Chuyen 50 trieu cho nguoi nhan moi",
            "Chuyen tien thue nha thang nay",
            "Gui tien cho me 5 trieu",
            "Chuyen cho anh Nam 10 trieu",
        ],
        "PHONE_TOPUP": [
            "Nap dien thoai 100k cho so lan truoc",
            "Nap 200k cho me",
            "Nap dien thoai 50k",
        ],
        "BILL_PAYMENT": [
            "Thanh toan hoa don dien hom nay",
            "Tra tien nuoc thang nay",
            "Thanh toan internet FPT",
        ],
        "CARD_LOCK": [
            "Khoa the tin dung cua toi",
            "Khoa the Visa ngay",
        ],
        "CARD_UNLOCK": [
            "Mo khoa the Visa",
            "Mo khoa the tin dung",
        ],
        "CARD_LIMIT_CHANGE": [
            "Tang han muc the len 100 trieu",
            "Giam han muc the xuong 50 trieu",
        ],
    }

    api_names = {
        "TRANSFER": "external_transfer_api",
        "PHONE_TOPUP": "external_phone_topup_api",
        "BILL_PAYMENT": "external_bill_payment_api",
        "CARD_LOCK": "external_card_service_api",
        "CARD_UNLOCK": "external_card_service_api",
        "CARD_LIMIT_CHANGE": "external_card_service_api",
    }

    # Distribution: 120 total
    type_dist = {
        "TRANSFER": 48,
        "PHONE_TOPUP": 18,
        "BILL_PAYMENT": 24,
        "CARD_LOCK": 12,
        "CARD_UNLOCK": 10,
        "CARD_LIMIT_CHANGE": 8,
    }

    # Status distribution
    status_pool = (
        ["DRAFT"] * 6 +
        ["MISSING_INFO"] * 12 +
        ["PENDING_CONFIRMATION"] * 12 +
        ["PENDING_OTP"] * 6 +
        ["READY_TO_EXECUTE"] * 6 +
        ["EXECUTED"] * 60 +
        ["FAILED"] * 10 +
        ["BLOCKED"] * 8
    )

    # Risk distribution
    risk_pool = (
        ["GREEN"] * 72 +
        ["YELLOW"] * 30 +
        ["ORANGE"] * 12 +
        ["RED"] * 6
    )

    action_idx = 0
    for action_type, count in type_dist.items():
        for _ in range(count):
            cif = random.choice(active_cifs)
            aid = make_id("action_requests", idx)

            risk_tier = random.choice(risk_pool)
            if risk_tier == "GREEN":
                risk_score = round(random.uniform(0.0, 0.29), 2)
            elif risk_tier == "YELLOW":
                risk_score = round(random.uniform(0.3, 0.59), 2)
            elif risk_tier == "ORANGE":
                risk_score = round(random.uniform(0.6, 0.79), 2)
            else:
                risk_score = round(random.uniform(0.8, 1.0), 2)

            # Status assignment with business rules
            if risk_tier == "RED":
                status = "BLOCKED"
            else:
                status = random.choice(status_pool)
                # Don't let non-RED be BLOCKED too often
                while status == "BLOCKED" and risk_tier != "RED":
                    status = random.choice(status_pool)

            user_text = random.choice(user_texts[action_type])

            # Generate payload
            cust_accts = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
            if not cust_accts:
                cust_accts = accts_by_cif[cif]
            acc = random.choice(cust_accts)

            if action_type == "TRANSFER":
                cust_benes = benes_by_cif.get(cif, [])
                bene = random.choice(cust_benes) if cust_benes else None
                amount = random.randint(100000, 50000000)
                payload = {
                    "from_account_no": acc["account_no"],
                    "to_account_no": bene["beneficiary_account_no"] if bene else gen_account_no(),
                    "to_bank_code": bene["beneficiary_bank_code"] if bene else random.choice(BANK_CODES),
                    "to_name": bene["beneficiary_name"] if bene else gen_vn_name(),
                    "amount": amount,
                    "currency": "VND",
                    "description": f"Chuyen tien cho {bene['beneficiary_name'].split()[-1] if bene else 'nguoi nhan'}",
                }
                resolved = {"beneficiary_name": payload["to_name"], "amount": amount, "bank_code": payload["to_bank_code"]}
            elif action_type == "PHONE_TOPUP":
                phone = gen_phone()
                carrier = CARRIER_MAP.get(phone[:2], "VIETTEL")
                amount = random.choice([50000, 100000, 200000, 500000])
                payload = {
                    "from_account_no": acc["account_no"],
                    "phone_number": phone,
                    "telco": carrier,
                    "amount": amount,
                    "currency": "VND",
                }
                resolved = {"phone_number": phone, "telco": carrier, "amount": amount}
            elif action_type == "BILL_PAYMENT":
                cust_cbas = cba_by_cif.get(cif, [])
                if cust_cbas:
                    cba = random.choice(cust_cbas)
                    bl = next((b for b in billers if b["biller_id"] == cba["biller_id"]), billers[0])
                    bill_code = cba["customer_bill_code"]
                else:
                    bl = random.choice(billers)
                    bill_code = f"PD{random.randint(100000000, 999999999)}"
                amount = random.randint(50000, 3000000)
                payload = {
                    "from_account_no": acc["account_no"],
                    "biller_code": bl["biller_code"],
                    "customer_bill_code": bill_code,
                    "amount": amount,
                    "currency": "VND",
                }
                resolved = {"biller_code": bl["biller_code"], "bill_code": bill_code, "amount": amount}
            elif action_type == "CARD_LOCK":
                cust_cards = cards_by_cif.get(cif, [])
                if cust_cards:
                    card = random.choice(cust_cards)
                else:
                    card = {"card_id": make_id("cards", 999), "masked_card_no": "**** **** **** 0000"}
                payload = {
                    "card_id": card["card_id"],
                    "masked_card_no": card["masked_card_no"],
                    "action": "LOCK",
                    "reason": "USER_REQUEST",
                }
                resolved = {"card_id": card["card_id"], "action": "LOCK"}
                amount = 0
            elif action_type == "CARD_UNLOCK":
                cust_cards = cards_by_cif.get(cif, [])
                if cust_cards:
                    card = random.choice(cust_cards)
                else:
                    card = {"card_id": make_id("cards", 999), "masked_card_no": "**** **** **** 0000"}
                payload = {
                    "card_id": card["card_id"],
                    "masked_card_no": card["masked_card_no"],
                    "action": "UNLOCK",
                    "reason": "USER_REQUEST",
                }
                resolved = {"card_id": card["card_id"], "action": "UNLOCK"}
                amount = 0
            else:  # CARD_LIMIT_CHANGE
                cust_cards = [c for c in cards_by_cif.get(cif, []) if c["card_type"] == "CREDIT"]
                if cust_cards:
                    card = random.choice(cust_cards)
                else:
                    card = {"card_id": make_id("cards", 999), "masked_card_no": "**** **** **** 0000"}
                new_limit = random.choice([50000000, 100000000, 150000000, 200000000])
                payload = {
                    "card_id": card["card_id"],
                    "masked_card_no": card["masked_card_no"],
                    "new_limit": new_limit,
                    "currency": "VND",
                }
                resolved = {"card_id": card["card_id"], "new_limit": new_limit}
                amount = 0

            # Missing fields for MISSING_INFO
            missing_fields = []
            if status == "MISSING_INFO":
                if action_type == "TRANSFER":
                    missing_fields = random.choice([["to_account_no"], ["to_bank_code", "to_name"], ["amount"]])
                elif action_type == "PHONE_TOPUP":
                    missing_fields = random.choice([["phone_number"], ["amount"]])
                elif action_type == "BILL_PAYMENT":
                    missing_fields = random.choice([["biller_code"], ["customer_bill_code"]])
                else:
                    missing_fields = ["card_id"]

            # Confirmation/OTP rules
            requires_confirmation = risk_tier != "GREEN" or (action_type in ["TRANSFER", "BILL_PAYMENT"] and amount > 5000000)
            requires_otp = risk_tier in ["YELLOW", "ORANGE"] or (action_type == "TRANSFER" and amount > 10000000)

            created_at = random_timestamp(datetime(2026, 4, 1), datetime(2026, 5, 31))
            updated_at = created_at + timedelta(seconds=random.randint(5, 300))

            # Clear payload for statuses that shouldn't have complete payload
            api_payload = payload if status not in ["DRAFT", "MISSING_INFO"] else {}
            if status in ["EXECUTED", "FAILED", "READY_TO_EXECUTE", "PENDING_OTP", "PENDING_CONFIRMATION"]:
                api_payload = payload

            action = {
                "action_id": aid,
                "cif_no": cif,
                "action_type": action_type,
                "status": status,
                "user_text": user_text,
                "api_name": api_names[action_type],
                "api_payload": json.dumps(api_payload, ensure_ascii=False),
                "resolved_entities": json.dumps(resolved, ensure_ascii=False),
                "missing_fields": json.dumps(missing_fields, ensure_ascii=False),
                "risk_score": risk_score,
                "risk_tier": risk_tier,
                "requires_confirmation": requires_confirmation,
                "requires_otp": requires_otp,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            action_requests.append(action)
            idx += 1
            action_idx += 1


def generate_api_call_logs():
    global api_call_logs
    idx = 1

    for action in action_requests:
        if action["status"] not in ["EXECUTED", "FAILED"]:
            continue

        aid = action["action_id"]
        api_name = action["api_name"]
        request_payload = action["api_payload"]
        action_created = datetime.strptime(action["created_at"], "%Y-%m-%d %H:%M:%S")
        log_time = action_created + timedelta(seconds=random.randint(1, 5))

        if action["status"] == "EXECUTED":
            http_status = 200
            log_status = "SUCCESS"
            type_abbr = action["action_type"][:3].upper()
            response = {
                "external_reference": f"EXT{type_abbr}{idx:06d}",
                "status": "SUCCESS",
                "message": "Operation completed successfully",
            }
        else:
            http_status = random.choice([400, 500])
            log_status = "FAILED"
            response = {
                "error_code": random.choice(["INSUFFICIENT_FUNDS", "INVALID_ACCOUNT", "TIMEOUT", "SERVICE_UNAVAILABLE"]),
                "message": "Operation failed",
            }

        log = {
            "api_call_id": make_id("api_call_logs", idx),
            "action_id": aid,
            "api_name": api_name,
            "request_payload": request_payload,
            "response_payload": json.dumps(response, ensure_ascii=False),
            "http_status": http_status,
            "status": log_status,
            "created_at": log_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        api_call_logs.append(log)
        idx += 1


def generate_audit_logs():
    global audit_logs
    idx = 1

    actors_map = {
        "USER_REQUEST_RECEIVED": "USER",
        "INTENT_CLASSIFIED": "ORCHESTRATOR",
        "ENTITY_EXTRACTED": "TRANSACTION_AGENT",
        "RECIPIENT_RESOLVED": "TRANSACTION_AGENT",
        "BILLER_RESOLVED": "TRANSACTION_AGENT",
        "CARD_RESOLVED": "TRANSACTION_AGENT",
        "TEXT2SQL_GENERATED": "TEXT2SQL_AGENT",
        "SQL_VALIDATED": "TEXT2SQL_AGENT",
        "RISK_CHECKED": "GUARDIAN",
        "USER_CONFIRMED": "USER",
        "OTP_VERIFIED": "USER",
        "API_CALLED": "EXECUTOR",
        "ACTION_EXECUTED": "EXECUTOR",
        "ACTION_FAILED": "EXECUTOR",
        "ACTION_BLOCKED": "GUARDIAN",
    }

    for action in action_requests:
        aid = action["action_id"]
        cif = action["cif_no"]
        action_type = action["action_type"]
        status = action["status"]
        base_time = datetime.strptime(action["created_at"], "%Y-%m-%d %H:%M:%S")

        # Build event sequence
        events = ["USER_REQUEST_RECEIVED", "INTENT_CLASSIFIED", "ENTITY_EXTRACTED"]

        if action_type == "TRANSFER":
            events.append("RECIPIENT_RESOLVED")
        elif action_type in ["BILL_PAYMENT"]:
            events.append("BILLER_RESOLVED")
        elif action_type in ["CARD_LOCK", "CARD_UNLOCK", "CARD_LIMIT_CHANGE"]:
            events.append("CARD_RESOLVED")
        elif action_type == "PHONE_TOPUP":
            pass  # no special resolution

        events.append("RISK_CHECKED")

        if action["requires_confirmation"] and status not in ["DRAFT", "MISSING_INFO"]:
            events.append("USER_CONFIRMED")

        if action["requires_otp"] and status in ["EXECUTED", "FAILED", "READY_TO_EXECUTE"]:
            events.append("OTP_VERIFIED")

        if status == "EXECUTED":
            events.append("API_CALLED")
            events.append("ACTION_EXECUTED")
        elif status == "FAILED":
            events.append("API_CALLED")
            events.append("ACTION_FAILED")
        elif status == "BLOCKED":
            events.append("ACTION_BLOCKED")

        # Generate audit entries
        current_time = base_time
        for event_type in events:
            current_time = current_time + timedelta(seconds=random.randint(1, 3))
            actor = actors_map.get(event_type, "ORCHESTRATOR")

            payload = {"event": event_type, "action_type": action_type}
            if event_type == "RISK_CHECKED":
                payload["risk_score"] = action["risk_score"]
                payload["risk_tier"] = action["risk_tier"]
            elif event_type == "USER_REQUEST_RECEIVED":
                payload["user_text"] = action["user_text"]

            audit = {
                "audit_id": make_id("audit_logs", idx),
                "action_id": aid,
                "cif_no": cif,
                "event_type": event_type,
                "actor": actor,
                "event_payload": json.dumps(payload, ensure_ascii=False),
                "created_at": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            audit_logs.append(audit)
            idx += 1


# ============================================================
# FRAUD DATA GENERATION
# ============================================================

def generate_fraud_data():
    """Generate fraud_reports, reported_accounts, reported_customers, fraud_decisions."""
    global fraud_reports, reported_accounts_list, reported_customers_list, fraud_decisions_list

    FRAUD_TYPES = ["SHOPPING_SCAM", "INVESTMENT_SCAM", "LOAN_SCAM", "IMPERSONATION", "ROMANCE_SCAM", "OTHER"]
    CONTACT_CHANNELS = ["FACEBOOK", "ZALO", "TELEGRAM", "WEBSITE", "PHONE", "OTHER"]
    AFTERMATHS = ["BLOCKED_CONTACT", "NO_GOODS", "ASKED_MORE_MONEY", "LINK_GONE", "OTHER"]

    active_custs = [c for c in customers if c["status"] == "ACTIVE"]
    active_cifs = [c["cif_no"] for c in active_custs]

    # Pick some outgoing BANK_TRANSFER transactions to use as basis for fraud reports
    out_transfers = [t for t in transactions
                     if t["transaction_type"] == "BANK_TRANSFER"
                     and t["direction"] == "OUT"
                     and t["status"] == "SUCCESS"
                     and t["counterparty_account_no"]
                     and t["counterparty_bank_code"]]

    # Group transfers by counterparty to simulate multiple reporters
    from collections import defaultdict
    cp_to_txns = defaultdict(list)
    for t in out_transfers:
        key = (t["counterparty_account_no"], t["counterparty_bank_code"])
        cp_to_txns[key].append(t)

    # Select 8 counterparty accounts to be "scam accounts"
    # Pick ones with multiple reporters for realistic data
    scam_candidates = [(k, v) for k, v in cp_to_txns.items() if len(v) >= 2]
    if len(scam_candidates) < 8:
        scam_candidates = list(cp_to_txns.items())[:8]
    else:
        scam_candidates = random.sample(scam_candidates, min(8, len(scam_candidates)))

    report_idx = 1
    ra_idx = 1
    rc_idx = 1

    # Track reported accounts for aggregation
    ra_map = {}  # (account_no, bank_code) -> reported_account record
    rc_map = {}  # cif_no -> reported_customer record

    for (cp_acc, cp_bank), txn_list in scam_candidates:
        # Create 1-5 fraud reports for this scam account from different users
        num_reports = min(len(txn_list), random.randint(1, 5))
        reporters_used = set()
        total_amount = 0
        confidence_scores = []

        for i in range(num_reports):
            txn = txn_list[i % len(txn_list)]
            reporter_cif = txn["cif_no"]

            # Skip if same reporter already reported this account
            if reporter_cif in reporters_used:
                continue
            reporters_used.add(reporter_cif)

            fraud_type = random.choice(FRAUD_TYPES)
            contact_channel = random.choice(CONTACT_CHANNELS)
            aftermath = random.choice(AFTERMATHS)
            has_evidence = random.random() < 0.6

            # Calculate confidence score
            score = 40  # has verified transaction
            txn_time = datetime.strptime(txn["transaction_time"], "%Y-%m-%d %H:%M:%S")
            days_ago = (FIXED_NOW - txn_time).days
            if days_ago <= 30:
                score += 20
            if fraud_type != "OTHER":
                score += 15
            if aftermath != "OTHER":
                score += 15
            if has_evidence:
                score += 10
            score = min(score, 100)
            confidence_scores.append(score)
            total_amount += txn["amount"]

            report = {
                "report_id": make_id("fraud_reports", report_idx),
                "reporter_cif_no": reporter_cif,
                "transaction_ref": txn["transaction_ref"],
                "reported_account_no": cp_acc,
                "reported_bank_code": cp_bank,
                "reported_customer_cif": "",
                "fraud_type": fraud_type,
                "contact_channel": contact_channel,
                "aftermath": aftermath,
                "reason_text": f"Bi lua dao qua {contact_channel.lower()}, {aftermath.lower().replace('_', ' ')}",
                "has_evidence": has_evidence,
                "confidence_score": score,
                "status": random.choice(["VALIDATED", "CONFIRMED"]) if score >= 60 else "SUBMITTED",
                "created_at": random_timestamp(datetime(2026, 5, 1), FIXED_NOW).strftime("%Y-%m-%d %H:%M:%S"),
            }
            fraud_reports.append(report)
            report_idx += 1

        # Create/update reported_account entry
        valid_count = len(reporters_used)
        avg_conf = int(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0

        # Risk level rules
        if valid_count >= 5 or avg_conf >= 80:
            risk_level = "CRITICAL"
            risk_score = 0.95
        elif valid_count >= 3:
            risk_level = "HIGH"
            risk_score = 0.75
        elif valid_count >= 2:
            risk_level = "MEDIUM"
            risk_score = 0.50
        else:
            risk_level = "LOW"
            risk_score = 0.25

        first_report_time = min(r["created_at"] for r in fraud_reports if r["reported_account_no"] == cp_acc)
        last_report_time = max(r["created_at"] for r in fraud_reports if r["reported_account_no"] == cp_acc)

        ra_record = {
            "reported_account_id": make_id("reported_accounts", ra_idx),
            "account_no": cp_acc,
            "bank_code": cp_bank,
            "linked_customer_cif": "",
            "valid_report_count": valid_count,
            "unique_reporter_count": len(reporters_used),
            "total_reported_amount": total_amount,
            "avg_confidence_score": avg_conf,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "status": "ACTIVE",
            "first_reported_at": first_report_time,
            "last_reported_at": last_report_time,
        }
        reported_accounts_list.append(ra_record)
        ra_map[(cp_acc, cp_bank)] = ra_record
        ra_idx += 1

    # Generate reported_customers for accounts that belong to our bank (simulated)
    # Pick 3 random customers to be "reported customers"
    reported_cust_cifs = random.sample(active_cifs[50:70], min(3, len(active_cifs[50:70])))
    for cif in reported_cust_cifs:
        num_accts = random.randint(1, 2)
        num_reports = random.randint(2, 5)
        total_amt = random.randint(10000000, 100000000)

        if num_accts >= 2:
            rl = "FROZEN"
            rs = 0.70
        else:
            rl = "WATCH"
            rs = 0.40

        rc_record = {
            "reported_customer_id": make_id("reported_customers", rc_idx),
            "cif_no": cif,
            "reported_account_count": num_accts,
            "valid_report_count": num_reports,
            "total_reported_amount": total_amt,
            "risk_score": rs,
            "risk_level": rl,
            "status": "ACTIVE",
            "created_at": random_timestamp(datetime(2026, 5, 1), FIXED_NOW).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": random_timestamp(datetime(2026, 5, 15), FIXED_NOW).strftime("%Y-%m-%d %H:%M:%S"),
        }
        reported_customers_list.append(rc_record)
        rc_map[cif] = rc_record
        rc_idx += 1

    # Generate fraud_decisions (simulating transfer screening logs)
    fd_idx = 1
    decisions_options = ["ALLOW", "WARN", "STEP_UP_AUTH", "HOLD", "BLOCK"]
    # Create 15-20 fraud_decisions for various action_requests
    transfer_actions = [a for a in action_requests if a["action_type"] == "TRANSFER"]
    for action in random.sample(transfer_actions, min(18, len(transfer_actions))):
        payload = json.loads(action["api_payload"]) if action["api_payload"] else {}
        receiver_acc = payload.get("to_account_no", gen_account_no())
        receiver_bank = payload.get("to_bank_code", random.choice(BANK_CODES))

        # Check if receiver is in reported_accounts
        ra_key = (receiver_acc, receiver_bank)
        if ra_key in ra_map:
            ra = ra_map[ra_key]
            matched = ra["valid_report_count"]
            risk_lvl = ra["risk_level"]
            if risk_lvl == "CRITICAL":
                decision = "BLOCK"
            elif risk_lvl == "HIGH":
                decision = "HOLD"
            elif risk_lvl == "MEDIUM":
                decision = "STEP_UP_AUTH"
            else:
                decision = "WARN"
            rs = ra["risk_score"]
        else:
            matched = 0
            risk_lvl = ""
            decision = "ALLOW"
            rs = 0.0

        reason_codes = []
        if matched > 0:
            reason_codes.append(f"REPORTED_ACCOUNT_{risk_lvl}")
        if action["risk_tier"] in ["ORANGE", "RED"]:
            reason_codes.append("HIGH_RISK_ACTION")

        fd = {
            "decision_id": make_id("fraud_decisions", fd_idx),
            "action_id": action["action_id"],
            "receiver_account_no": receiver_acc,
            "receiver_bank_code": receiver_bank,
            "matched_report_count": matched,
            "risk_score": rs,
            "risk_level": risk_lvl if risk_lvl else "NONE",
            "decision": decision,
            "reason_codes": json.dumps(reason_codes, ensure_ascii=False),
            "created_at": action["created_at"],
        }
        fraud_decisions_list.append(fd)
        fd_idx += 1


# ============================================================
# VALIDATION
# ============================================================

def validate_data():
    print("Running validation...")

    cif_set = {c["cif_no"] for c in customers}
    acc_no_set = {a["account_no"] for a in accounts}
    card_id_set = {c["card_id"] for c in cards}
    merchant_id_set = {m["merchant_id"] for m in merchants}
    biller_id_set = {b["biller_id"] for b in billers}
    bene_id_set = {b["beneficiary_id"] for b in beneficiaries}
    cat_id_set = {c["category_id"] for c in transaction_categories}
    action_id_set = {a["action_id"] for a in action_requests}

    # FK: accounts.cif_no
    for a in accounts:
        assert a["cif_no"] in cif_set, f"accounts FK fail: {a['cif_no']}"

    # FK: cards
    for c in cards:
        assert c["cif_no"] in cif_set, f"cards cif FK fail: {c['cif_no']}"
        cust_acc_nos = {a["account_no"] for a in accts_by_cif[c["cif_no"]]}
        assert c["account_no"] in cust_acc_nos, f"cards account FK fail: card {c['card_id']} acc {c['account_no']} not in cif {c['cif_no']}"

    # FK: beneficiaries
    for b in beneficiaries:
        assert b["cif_no"] in cif_set, f"beneficiaries FK fail: {b['cif_no']}"

    # FK: customer_biller_accounts
    for cba in customer_biller_accounts:
        assert cba["cif_no"] in cif_set, f"cba cif FK fail: {cba['cif_no']}"
        assert cba["biller_id"] in biller_id_set, f"cba biller FK fail: {cba['biller_id']}"

    # FK: transactions
    for t in transactions:
        assert t["cif_no"] in cif_set, f"txn cif FK fail: {t['cif_no']}"
        cust_acc_nos = {a["account_no"] for a in accts_by_cif[t["cif_no"]]}
        assert t["account_no"] in cust_acc_nos, f"txn account FK fail: {t['transaction_ref']}"
        if t["card_id"]:
            cust_card_ids = {c["card_id"] for c in cards_by_cif.get(t["cif_no"], [])}
            assert t["card_id"] in cust_card_ids, f"txn card FK fail: {t['transaction_ref']}"
        if t["merchant_id"]:
            assert t["merchant_id"] in merchant_id_set, f"txn merchant FK fail: {t['transaction_ref']}"
        if t["biller_id"]:
            assert t["biller_id"] in biller_id_set, f"txn biller FK fail: {t['transaction_ref']}"
        if t["beneficiary_id"]:
            cust_bene_ids = {b["beneficiary_id"] for b in benes_by_cif.get(t["cif_no"], [])}
            assert t["beneficiary_id"] in cust_bene_ids, f"txn beneficiary FK fail: {t['transaction_ref']}"
        assert t["category_id"] in cat_id_set, f"txn category FK fail: {t['transaction_ref']}"

    # FK: action_requests
    for a in action_requests:
        assert a["cif_no"] in cif_set, f"action cif FK fail: {a['action_id']}"

    # FK: api_call_logs
    for log in api_call_logs:
        assert log["action_id"] in action_id_set, f"api_call action FK fail: {log['api_call_id']}"

    # FK: audit_logs
    for al in audit_logs:
        if al["action_id"]:
            assert al["action_id"] in action_id_set, f"audit action FK fail: {al['audit_id']}"
        assert al["cif_no"] in cif_set, f"audit cif FK fail: {al['audit_id']}"

    # Business rules
    active_custs = [c for c in customers if c["status"] == "ACTIVE"]
    for c in active_custs:
        cif = c["cif_no"]
        active_payment = [a for a in accts_by_cif[cif] if a["status"] == "ACTIVE" and a["account_type"] == "PAYMENT"]
        assert len(active_payment) >= 1, f"ACTIVE customer {cif} has no ACTIVE PAYMENT account"

    # CARD_PAYMENT must have card_id and merchant_id
    for t in transactions:
        if t["transaction_type"] == "CARD_PAYMENT":
            assert t["card_id"], f"CARD_PAYMENT missing card_id: {t['transaction_ref']}"
            assert t["merchant_id"], f"CARD_PAYMENT missing merchant_id: {t['transaction_ref']}"
        if t["transaction_type"] == "BILL_PAYMENT":
            assert t["biller_id"], f"BILL_PAYMENT missing biller_id: {t['transaction_ref']}"
        if t["transaction_type"] == "BANK_TRANSFER" and t["direction"] == "OUT":
            assert t["counterparty_account_no"], f"BANK_TRANSFER OUT missing counterparty: {t['transaction_ref']}"
            assert t["counterparty_bank_code"], f"BANK_TRANSFER OUT missing bank_code: {t['transaction_ref']}"
            assert t["counterparty_name"], f"BANK_TRANSFER OUT missing name: {t['transaction_ref']}"
        if t["transaction_type"] == "PHONE_TOPUP":
            assert t["counterparty_name"], f"PHONE_TOPUP missing phone: {t['transaction_ref']}"
            assert t["counterparty_account_no"] == t["counterparty_name"], f"PHONE_TOPUP phone mismatch: {t['transaction_ref']}"
            prefix = t["counterparty_name"][:2]
            assert prefix in CARRIER_MAP, f"PHONE_TOPUP invalid prefix: {t['transaction_ref']}"

    # Action request business rules
    for a in action_requests:
        if a["status"] == "MISSING_INFO":
            mf = json.loads(a["missing_fields"])
            assert len(mf) > 0, f"MISSING_INFO but empty missing_fields: {a['action_id']}"
        if a["risk_tier"] == "RED":
            assert a["status"] == "BLOCKED", f"RED but not BLOCKED: {a['action_id']}"
        if a["status"] == "EXECUTED":
            has_success = any(log["action_id"] == a["action_id"] and log["status"] == "SUCCESS" for log in api_call_logs)
            assert has_success, f"EXECUTED but no SUCCESS api_call: {a['action_id']}"
        if a["status"] == "BLOCKED":
            has_success = any(log["action_id"] == a["action_id"] and log["status"] == "SUCCESS" for log in api_call_logs)
            assert not has_success, f"BLOCKED but has SUCCESS api_call: {a['action_id']}"

    # api_call_logs timing
    for log in api_call_logs:
        action = next(a for a in action_requests if a["action_id"] == log["action_id"])
        assert log["created_at"] > action["created_at"], f"api_call before action: {log['api_call_id']}"

    # audit_logs ordering per action
    from collections import defaultdict
    audit_by_action = defaultdict(list)
    for al in audit_logs:
        if al["action_id"]:
            audit_by_action[al["action_id"]].append(al)
    for aid, logs in audit_by_action.items():
        times = [l["created_at"] for l in logs]
        assert times == sorted(times), f"audit_logs not ordered for action: {aid}"

    # Uniqueness
    txn_refs = [t["transaction_ref"] for t in transactions]
    assert len(txn_refs) == len(set(txn_refs)), "Duplicate transaction_ref"

    acc_nos = [a["account_no"] for a in accounts]
    assert len(acc_nos) == len(set(acc_nos)), "Duplicate account_no"

    biller_codes = [b["biller_code"] for b in billers]
    assert len(biller_codes) == len(set(biller_codes)), "Duplicate biller_code"

    cat_codes = [c["category_code"] for c in transaction_categories]
    assert len(cat_codes) == len(set(cat_codes)), "Duplicate category_code"

    # JSON validity
    for a in action_requests:
        json.loads(a["api_payload"])
        json.loads(a["resolved_entities"])
        json.loads(a["missing_fields"])
    for log in api_call_logs:
        json.loads(log["request_payload"])
        json.loads(log["response_payload"])
    for al in audit_logs:
        json.loads(al["event_payload"])

    print("ALL CHECKS PASSED")


# ============================================================
# README GENERATION
# ============================================================

def generate_readme():
    readme = """# Mock Banking Data

## Purpose

Mock data for AI banking assistant demo. Used for Text2SQL queries, transaction history,
beneficiary resolution, bill payment, phone top-up, and risk-checked action workflows.
Data is deterministic (seed=42) and reproducible.

## Tables

| # | Table | Rows |
|---|-------|------|
| 1 | customers | {customers} |
| 2 | accounts | {accounts} |
| 3 | cards | {cards} |
| 4 | beneficiaries | {beneficiaries} |
| 5 | merchants | {merchants} |
| 6 | billers | {billers} |
| 7 | customer_biller_accounts | {cba} |
| 8 | transaction_categories | {categories} |
| 9 | transactions | {transactions} |
| 10 | action_requests | {actions} |
| 11 | api_call_logs | {api_logs} |
| 12 | audit_logs | {audit_logs} |

## Relationships (Text ER)

```
customers (cif_no) ─┬─< accounts (cif_no, account_no)
                    ├─< cards (cif_no, account_no → accounts)
                    ├─< beneficiaries (cif_no)
                    ├─< customer_biller_accounts (cif_no, biller_id → billers)
                    ├─< transactions (cif_no, account_no, card_id?, merchant_id?, biller_id?, beneficiary_id?, category_id)
                    ├─< action_requests (cif_no)
                    └─< audit_logs (cif_no, action_id → action_requests)

action_requests (action_id) ─< api_call_logs (action_id)
action_requests (action_id) ─< audit_logs (action_id)

merchants (merchant_id) ─< transactions
billers (biller_id) ─< transactions, customer_biller_accounts
transaction_categories (category_id) ─< transactions
```

## Use Case → Table Mapping

| Use Case | Tables |
|----------|--------|
| Chuyen tien cho Minh | beneficiaries, transactions, action_requests |
| Spending analysis | transactions, transaction_categories, merchants |
| Card transactions | transactions, cards, merchants |
| Bill payment | billers, customer_biller_accounts, transactions, action_requests |
| Phone top-up | transactions, action_requests |
| Anomaly detection | transactions (amount, time, beneficiary_id=null) |
| Fee inquiry | transactions (type=FEE) |
| Salary check | transactions (type=SALARY) |

## Sample Text2SQL Queries

### 1. Thang nay toi tieu bao nhieu cho an uong?
```sql
SELECT SUM(t.amount) as total
FROM transactions t
JOIN transaction_categories tc ON t.category_id = tc.category_id
WHERE t.cif_no = :cif_no
  AND tc.category_code = 'FOOD'
  AND t.transaction_time >= '2026-05-01'
  AND t.direction = 'OUT';
```

### 2. 3 giao dich gan nhat cua toi la gi?
```sql
SELECT * FROM transactions
WHERE cif_no = :cif_no
ORDER BY transaction_time DESC
LIMIT 3;
```

### 3. 3 giao dich the gan nhat cua toi?
```sql
SELECT * FROM transactions
WHERE cif_no = :cif_no AND transaction_type = 'CARD_PAYMENT'
ORDER BY transaction_time DESC
LIMIT 3;
```

### 4. Toi da chuyen cho Minh bao nhieu tien thang truoc?
```sql
SELECT SUM(t.amount) as total
FROM transactions t
JOIN beneficiaries b ON t.beneficiary_id = b.beneficiary_id
WHERE t.cif_no = :cif_no
  AND b.beneficiary_name LIKE '%Minh%'
  AND t.transaction_time >= '2026-04-01'
  AND t.transaction_time < '2026-05-01'
  AND t.direction = 'OUT';
```

### 5. Tai khoan nao cua toi co so du cao nhat?
```sql
SELECT account_no, account_type, balance
FROM accounts
WHERE cif_no = :cif_no AND status = 'ACTIVE'
ORDER BY balance DESC
LIMIT 1;
```

### 6. Toi da thanh toan hoa don dien thang nay chua?
```sql
SELECT * FROM transactions t
JOIN billers b ON t.biller_id = b.biller_id
WHERE t.cif_no = :cif_no
  AND b.biller_type = 'ELECTRICITY'
  AND t.transaction_time >= '2026-05-01';
```

### 7. Toi nap dien thoai cho so nao gan nhat?
```sql
SELECT counterparty_name, amount, transaction_time
FROM transactions
WHERE cif_no = :cif_no AND transaction_type = 'PHONE_TOPUP'
ORDER BY transaction_time DESC
LIMIT 1;
```

### 8. Co giao dich nao tren 10 trieu trong 7 ngay qua khong?
```sql
SELECT * FROM transactions
WHERE cif_no = :cif_no
  AND amount > 10000000
  AND transaction_time >= '2026-05-25';
```

### 9. Toi chi bao nhieu cho Grab trong thang nay?
```sql
SELECT SUM(t.amount) as total
FROM transactions t
JOIN merchants m ON t.merchant_id = m.merchant_id
WHERE t.cif_no = :cif_no
  AND m.merchant_name LIKE '%Grab%'
  AND t.transaction_time >= '2026-05-01'
  AND t.direction = 'OUT';
```

### 10. Luong thang nay da vao chua?
```sql
SELECT * FROM transactions
WHERE cif_no = :cif_no
  AND transaction_type = 'SALARY'
  AND transaction_time >= '2026-05-01'
  AND direction = 'IN';
```

## API Payload Examples

### TRANSFER
```json
{{
  "from_account_no": "1234567890",
  "to_account_no": "9876543210",
  "to_bank_code": "VCB",
  "to_name": "Nguyen Van Minh",
  "amount": 2000000,
  "currency": "VND",
  "description": "Chuyen tien cho Minh"
}}
```

### PHONE_TOPUP
```json
{{
  "from_account_no": "1234567890",
  "phone_number": "0987654321",
  "telco": "VIETTEL",
  "amount": 100000,
  "currency": "VND"
}}
```

### BILL_PAYMENT
```json
{{
  "from_account_no": "1234567890",
  "biller_code": "EVN_HANOI",
  "customer_bill_code": "PD123456789",
  "amount": 1250000,
  "currency": "VND"
}}
```

### CARD_LOCK
```json
{{
  "card_id": "uuid-here",
  "masked_card_no": "**** **** **** 1234",
  "action": "LOCK",
  "reason": "USER_REQUEST"
}}
```

### CARD_LIMIT_CHANGE
```json
{{
  "card_id": "uuid-here",
  "masked_card_no": "**** **** **** 5678",
  "new_limit": 100000000,
  "currency": "VND"
}}
```
""".format(
        customers=len(customers),
        accounts=len(accounts),
        cards=len(cards),
        beneficiaries=len(beneficiaries),
        merchants=len(merchants),
        billers=len(billers),
        cba=len(customer_biller_accounts),
        categories=len(transaction_categories),
        transactions=len(transactions),
        actions=len(action_requests),
        api_logs=len(api_call_logs),
        audit_logs=len(audit_logs),
    )

    with open(OUTPUT_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


# ============================================================
# MAIN
# ============================================================

def main():
    # Create output dir
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating data...")
    print("  customers...")
    generate_customers()
    print("  accounts...")
    generate_accounts()
    print("  cards...")
    generate_cards()
    print("  beneficiaries...")
    generate_beneficiaries()
    print("  merchants...")
    generate_merchants()
    print("  billers...")
    generate_billers()
    print("  customer_biller_accounts...")
    generate_customer_biller_accounts()
    print("  transaction_categories...")
    generate_transaction_categories()
    print("  transactions...")
    generate_transactions()
    print("  action_requests...")
    generate_action_requests()
    print("  api_call_logs...")
    generate_api_call_logs()
    print("  audit_logs...")
    generate_audit_logs()
    print("  fraud_data...")
    generate_fraud_data()

    # Write CSVs
    print("\nWriting CSV files...")

    write_csv("customers.csv", customers,
              ["customer_id", "cif_no", "full_name", "phone_number", "email", "kyc_level", "status", "created_at"])

    write_csv("accounts.csv", accounts,
              ["account_id", "account_no", "cif_no", "account_type", "currency", "balance", "available_balance", "status", "opened_at"])

    write_csv("cards.csv", cards,
              ["card_id", "cif_no", "account_no", "masked_card_no", "card_type", "card_network", "credit_limit", "available_limit", "status", "issued_at"])

    write_csv("beneficiaries.csv", beneficiaries,
              ["beneficiary_id", "cif_no", "beneficiary_name", "beneficiary_account_no", "beneficiary_bank_code", "beneficiary_bank_name", "nickname", "is_saved", "last_used_at", "created_at"])

    write_csv("merchants.csv", merchants,
              ["merchant_id", "merchant_name", "merchant_category", "mcc_code", "city", "country", "status"])

    write_csv("billers.csv", billers,
              ["biller_id", "biller_code", "biller_name", "biller_type", "provider", "status"])

    write_csv("customer_biller_accounts.csv", customer_biller_accounts,
              ["customer_biller_account_id", "cif_no", "biller_id", "customer_bill_code", "alias", "status", "last_paid_at"])

    write_csv("transaction_categories.csv", transaction_categories,
              ["category_id", "category_code", "category_name", "category_group"])

    write_csv("transactions.csv", transactions,
              ["transaction_id", "transaction_ref", "cif_no", "account_no", "card_id", "transaction_time", "amount", "currency", "direction", "transaction_type", "category_id", "merchant_id", "biller_id", "beneficiary_id", "counterparty_account_no", "counterparty_bank_code", "counterparty_name", "channel", "description", "status", "balance_after", "external_reference", "created_at"])

    write_csv("action_requests.csv", action_requests,
              ["action_id", "cif_no", "action_type", "status", "user_text", "api_name", "api_payload", "resolved_entities", "missing_fields", "risk_score", "risk_tier", "requires_confirmation", "requires_otp", "created_at", "updated_at"])

    write_csv("api_call_logs.csv", api_call_logs,
              ["api_call_id", "action_id", "api_name", "request_payload", "response_payload", "http_status", "status", "created_at"])

    write_csv("audit_logs.csv", audit_logs,
              ["audit_id", "action_id", "cif_no", "event_type", "actor", "event_payload", "created_at"])

    write_csv("fraud_reports.csv", fraud_reports,
              ["report_id", "reporter_cif_no", "transaction_ref", "reported_account_no", "reported_bank_code",
               "reported_customer_cif", "fraud_type", "contact_channel", "aftermath", "reason_text",
               "has_evidence", "confidence_score", "status", "created_at"])

    write_csv("reported_accounts.csv", reported_accounts_list,
              ["reported_account_id", "account_no", "bank_code", "linked_customer_cif",
               "valid_report_count", "unique_reporter_count", "total_reported_amount",
               "avg_confidence_score", "risk_score", "risk_level", "status",
               "first_reported_at", "last_reported_at"])

    write_csv("reported_customers.csv", reported_customers_list,
              ["reported_customer_id", "cif_no", "reported_account_count", "valid_report_count",
               "total_reported_amount", "risk_score", "risk_level", "status", "created_at", "updated_at"])

    write_csv("fraud_decisions.csv", fraud_decisions_list,
              ["decision_id", "action_id", "receiver_account_no", "receiver_bank_code",
               "matched_report_count", "risk_score", "risk_level", "decision", "reason_codes", "created_at"])

    # Generate README
    print("  README.md...")
    generate_readme()

    # Validate
    print("\n" + "=" * 50)
    validate_data()
    print("=" * 50)

    # Summary
    print("\nSUMMARY:")
    print(f"  customers:               {len(customers):>6}")
    print(f"  accounts:                {len(accounts):>6}")
    print(f"  cards:                   {len(cards):>6}")
    print(f"  beneficiaries:           {len(beneficiaries):>6}")
    print(f"  merchants:               {len(merchants):>6}")
    print(f"  billers:                 {len(billers):>6}")
    print(f"  customer_biller_accounts:{len(customer_biller_accounts):>6}")
    print(f"  transaction_categories:  {len(transaction_categories):>6}")
    print(f"  transactions:            {len(transactions):>6}")
    print(f"  action_requests:         {len(action_requests):>6}")
    print(f"  api_call_logs:           {len(api_call_logs):>6}")
    print(f"  audit_logs:              {len(audit_logs):>6}")
    print(f"  fraud_reports:           {len(fraud_reports):>6}")
    print(f"  reported_accounts:       {len(reported_accounts_list):>6}")
    print(f"  reported_customers:      {len(reported_customers_list):>6}")
    print(f"  fraud_decisions:         {len(fraud_decisions_list):>6}")
    print(f"\nOutput: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
