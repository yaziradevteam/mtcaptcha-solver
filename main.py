import hashlib
import uuid
import time
import requests
import json
import base64
import re
import secrets
from urllib.parse import urlencode
from openai import OpenAI

SERVICE_DOMAIN = "service.mtcaptcha.com"
SITEKEY = "MTPublic-KzqLY1cKH"
HOSTNAME = "2captcha.com"
ACTION = ""
LANG = "en"
WIDGET_SIZE = "standard"
LF = 0

DEEPINFRA_API_KEY = "r0PoXqyr8b0yKaYAemz121kKqhb7LocS"
DEEPINFRA_BASE_URL = "https://api.deepinfra.com/v1/openai"
DEEPINFRA_MODEL = "Qwen/Qwen3-VL-235B-A22B-Instruct"

COOKIES = {
    "mtv1ConfSum": "{v:01|wdsz:std|thm:basic|lan:en|chlg:std|clan:1|cstyl:1|afv:0|afot:0|}",
    "jsV": "2026-05-04.21.34.59",
    "mtv1Pulse": "0001R1YCTf-lT8Y85AlfY3YSVt"
}

DEMO_COOKIES = {
    "i18next": "en",
    "guest_currency": "usd",
    "_gcl_au": "1.1.688933806.1782121444",
    "original_referer": "https://www.google.com/",
    "timezone": "Asia/Calcutta",
    "first_visited_page": "/demo/mtcaptcha",
    "last_visited_page": "/demo/mtcaptcha",
    "_clck": "qcthxd%5E2%5Eg74%5E0%5E2364",
    "user_country": "sg"
}

BASE64_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
BASE64_CHAR_MAP = {c: i for i, c in enumerate(BASE64_CHARS)}

def base64_char_to_int(ch):
    return BASE64_CHAR_MAP[ch]

def base64_int_to_char(i):
    return BASE64_CHARS[i]

def base64_str_to_int_array(s):
    return [base64_char_to_int(c) for c in s]

def to_signed32(x):
    x = x & 0xFFFFFFFF
    if x > 0x7FFFFFFF:
        x -= 0x100000000
    return x

def fold_base64_array(a1, fold_count):
    a2 = a1[::-1]
    a3 = a1[:]
    y = 0
    z = 0
    for i in range(fold_count):
        offset = i + 1
        for x in range(len(a1)):
            val = ((a3[x] + a2[(x + offset) % len(a2)]) * 73) // 8
            a3[x] = (val + y + z) % 64
            z = y // 2
            y = a3[x] // 2
    return a3

def hash_int_array(arr):
    h = 0
    for v in arr:
        h = ((h << 5) - h + v)
        h = to_signed32(h)
    if h < 0:
        h = -h
    return h

def solve_fold(fseed, fslots, fdepth):
    ints = base64_str_to_int_array(fseed)
    result_pairs = []
    for _ in range(fslots):
        ints = fold_base64_array(ints, 31)
        folded_again = fold_base64_array(ints, fdepth)
        h = hash_int_array(folded_again)
        val = h % 4096
        result_pairs.append(base64_int_to_char(val >> 6) + base64_int_to_char(val & 63))
    return ''.join(result_pairs)

def generate_kt():
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
    return ''.join(secrets.choice(alphabet) for _ in range(64))

def transaction_signature(sitekey, secret="mtcap@mtcaptcha.com"):
    return f"TH[{hashlib.md5((secret + sitekey).encode()).hexdigest()}]"

def new_session_id():
    return f"S0{uuid.uuid4()}"

def get_challenge(session_id):
    params = {
        "sk": SITEKEY,
        "bd": HOSTNAME,
        "rt": int(time.time() * 1000),
        "tsh": transaction_signature(SITEKEY),
        "act": ACTION if ACTION else "$",
        "ss": session_id,
        "lf": str(LF),
        "tl": "$",
        "lg": LANG,
        "tp": "s" if WIDGET_SIZE == "standard" else "m",
    }
    url = f"https://{SERVICE_DOMAIN}/mtcv1/api/getchallenge.json?{urlencode(params)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": f"https://{SERVICE_DOMAIN}/mtcv1/client/iframe.html?v=2026-05-04.21.34.59&sitekey={SITEKEY}&iframeId=mtcaptcha-iframe-1&widgetSize=standard&custom=false&widgetInstance=mtcaptcha&challengeType=standard&theme=basic&lang=en&action=&autoFadeOuterText=false&host=https%3A%2F%2F2captcha.com&hostname={HOSTNAME}&serviceDomain={SERVICE_DOMAIN}&textLength=0&lowFrictionInvisible=&enableMouseFlow=false"
    }
    resp = requests.get(url, headers=headers, cookies=COOKIES, timeout=15)
    resp.raise_for_status()
    return resp.json()

def get_image(ct, fa, session_id):
    params = {
        "sk": SITEKEY,
        "ct": ct,
        "fa": fa,
        "ss": session_id,
    }
    url = f"https://{SERVICE_DOMAIN}/mtcv1/api/getimage.json?{urlencode(params)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": f"https://{SERVICE_DOMAIN}/mtcv1/client/iframe.html?v=2026-05-04.21.34.59&sitekey={SITEKEY}&iframeId=mtcaptcha-iframe-1&widgetSize=standard&custom=false&widgetInstance=mtcaptcha&challengeType=standard&theme=basic&lang=en&action=&autoFadeOuterText=false&host=https%3A%2F%2F2captcha.com&hostname={HOSTNAME}&serviceDomain={SERVICE_DOMAIN}&textLength=0&lowFrictionInvisible=&enableMouseFlow=false"
    }
    resp = requests.get(url, headers=headers, cookies=COOKIES, timeout=15)
    resp.raise_for_status()
    return resp.json()

def ocr_with_deepinfra(image_path):
    with open(image_path, "rb") as f:
        base64_image = base64.b64encode(f.read()).decode("utf-8")
    client = OpenAI(api_key=DEEPINFRA_API_KEY, base_url=DEEPINFRA_BASE_URL)
    prompt = (
        "The image contains a CAPTCHA text consisting of exactly 4 characters, "
        "which may be uppercase or lowercase letters and/or digits. "
        "Respond with only the 4 characters exactly as they appear, "
        "no explanation, no punctuation, no spaces."
    )
    try:
        completion = client.chat.completions.create(
            model=DEEPINFRA_MODEL,
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        {"type": "text", "text": prompt},
                    ]
                }
            ],
        )
        raw = completion.choices[0].message.content.strip()
        text = re.sub(r'[^A-Za-z0-9]', '', raw)
        return text
    except Exception as e:
        print(f"OCR error: {e}")
        return ""

def solve_challenge(ct, answer, fa, session_id, fseed, kt):
    params = {
        "ct": ct,
        "sk": SITEKEY,
        "st": answer,
        "lf": str(LF),
        "bd": HOSTNAME,
        "rt": int(time.time() * 1000),
        "tsh": transaction_signature(SITEKEY),
        "fa": fa,
        "qh": "$",
        "act": ACTION if ACTION else "$",
        "ss": session_id,
        "tl": "$",
        "lg": LANG,
        "tp": "s" if WIDGET_SIZE == "standard" else "m",
        "kt": kt,
        "fs": fseed if fseed else "",
    }
    url = f"https://{SERVICE_DOMAIN}/mtcv1/api/solvechallenge.json?{urlencode(params)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": f"https://{SERVICE_DOMAIN}/mtcv1/client/iframe.html?v=2026-05-04.21.34.59&sitekey={SITEKEY}&iframeId=mtcaptcha-iframe-1&widgetSize=standard&custom=false&widgetInstance=mtcaptcha&challengeType=standard&theme=basic&lang=en&action=&autoFadeOuterText=false&host=https%3A%2F%2F2captcha.com&hostname={HOSTNAME}&serviceDomain={SERVICE_DOMAIN}&textLength=0&lowFrictionInvisible=&enableMouseFlow=false"
    }
    resp = requests.get(url, headers=headers, cookies=COOKIES, timeout=15)
    resp.raise_for_status()
    return resp.json()

def verify_token(token):
    url = "https://2captcha.com/api/v1/captcha-demo/mtcaptcha/verify"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Origin": "https://2captcha.com",
        "Referer": "https://2captcha.com/demo/mtcaptcha"
    }
    data = {"token": token}
    resp = requests.post(url, json=data, headers=headers, cookies=DEMO_COOKIES, timeout=15)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    session_id = new_session_id()
    print(f"Session ID: {session_id}")

    chal = get_challenge(session_id)
    if chal.get("code") != 1200:
        print("Challenge failed")
        exit(1)

    result = chal["result"]
    challenge = result["challenge"]
    ct = challenge["ct"]
    fold = challenge.get("foldChlg", {})
    fseed = fold.get("fseed", "")
    fslots = fold.get("fslots", 0)
    fdepth = fold.get("fdepth", 0)

    if fseed and fold.get("preRes"):
        fa = solve_fold(fseed, fslots, fdepth)
        print(f"Computed fa (length {len(fa)})")
    else:
        fa = "$"
        print("No fold challenge")

    img_data = get_image(ct, fa, session_id)
    if img_data.get("code") != 1200:
        print("Image fetch failed. Code:", img_data.get("code"))
        exit(1)

    img_b64 = img_data["result"]["img"]["image64"]
    image_path = "captcha_image.png"
    with open(image_path, "wb") as f:
        f.write(base64.b64decode(img_b64))

    answer_len = challenge['textChlg']['textlen']
    print(f"Expected answer length: {answer_len}")

    detected = ocr_with_deepinfra(image_path)
    print(f"OCR text: {detected}")

    if len(detected) != answer_len:
        print(f"Warning: detected length ({len(detected)}) != expected ({answer_len})")
        if len(detected) > answer_len:
            detected = detected[:answer_len]
            print(f"Truncated to: {detected}")

    kt = generate_kt()
    solve_result = solve_challenge(ct, detected, fa, session_id, fseed, kt)

    if solve_result.get("code") != 1200:
        print(f"Solve failed with code {solve_result.get('code')}")
        exit(1)

    if not solve_result.get("result", {}).get("verifyResult", {}).get("isVerified", False):
        print("Verification failed")
        exit(1)

    token = solve_result["result"]["verifyResult"]["verifiedToken"]["vt"]
    print(f"\nVerification token: {token}")

    demo_result = verify_token(token)
    if demo_result.get("status") == "ok" or demo_result.get("success"):
        print("\nToken verified by 2Captcha demo successfully!")
    else:
        print("\nDemo verification failed:", demo_result)