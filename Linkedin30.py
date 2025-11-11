import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import pandas as pd
from io import BytesIO
import zipfile
import textwrap
from PIL import Image, ImageDraw, ImageFont
import io
import stripe

# === SECRETS ===
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
STRIPE_PUBLISHABLE_KEY = st.secrets["STRIPE_PUBLISHABLE_KEY"]
PRICE_ID = st.secrets["PRICE_ID"]
APP_URL = st.secrets["APP_URL"]

# === PAGE CONFIG ===
st.set_page_config(page_title="LinkedIn30", layout="centered")
st.markdown("""
<style>
    .main {background:#0e1117; color:white; padding:2rem;}
    .stButton>button {background:#0A66C2; color:white; border-radius:12px; padding:12px 24px; font-weight:bold;}
    .stTextInput>div>div>input {background:#1a1a1a; color:white; border:1px solid #0A66C2; border-radius:12px; padding:12px;}
    h1 {color:#0A66C2; text-align:center; font-size:2.8rem; margin-bottom:0;}
    .subtitle {text-align:center; color:#aaa; font-size:1.2rem; margin-bottom:2rem;}
    .pro-badge {background:#0A66C2; color:white; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:bold;}
    .upgrade-box {text-align:center; padding:24px; background:#1a1a1a; border-radius:16px; border:2px solid #0A66C2;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>LinkedIn30</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Turn 1 blog to 30 high-engagement LinkedIn posts in 60s</p>", unsafe_allow_html=True)

# === SESSION STATE ===
if 'is_pro' not in st.session_state:
    st.session_state.is_pro = False
if 'generations_today' not in st.session_state:
    st.session_state.generations_today = 0

# === UPGRADE CTA (BUTTON ALWAYS VISIBLE) ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.is_pro:
        st.markdown("<p class='pro-badge'>PRO USER – UNLIMITED</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class='upgrade-box'>
            <h3>Go Pro</h3>
            <p style='margin:8px 0;'><s>£19/month</s> to <b style='font-size:1.4rem;'>£9 first month</b></p>
            <p style='margin:8px 0; font-size:0.95rem;'>Unlimited calendars • Priority support • Export to PDF</p>
            <div id="stripe-button-container"></div>
        </div>
        """, unsafe_allow_html=True)

        # STRIPE JS — BUTTON INJECTED DIRECTLY
        st.markdown(f"""
        <script src="https://js.stripe.com/v3/"></script>
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const stripe = Stripe('{STRIPE_PUBLISHABLE_KEY}');
            const container = document.getElementById('stripe-button-container');
            if (container) {{
                const button = document.createElement('button');
                button.textContent = 'Upgrade Now';
                button.style.cssText = 'background:#0A66C2; color:white; border:none; padding:14px 28px; border-radius:12px; font-weight:bold; font-size:1.1rem; cursor:pointer; margin-top:12px; width:100%;';
                button.onclick = function() {{
                    stripe.redirectToCheckout({{
                        lineItems: [{{ price: '{PRICE_ID}', quantity: 1 }}],
                        mode: 'subscription',
                        successUrl: '{APP_URL}?session_id={{CHECKOUT_SESSION_ID}}',
                        cancelUrl: '{APP_URL}'
                    }});
                }};
                container.appendChild(button);
            }}
        }});
        </script>
        """, unsafe_allow_html=True)

# === CHECK PAYMENT SUCCESS ===
def verify_payment():
    session_id = st.query_params.get("session_id")
    if session_id and not st.session_state.is_pro:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == "paid":
                st.session_state.is_pro = True
                st.success("Payment successful! You're now Pro.")
                st.rerun()
        except Exception as e:
            st.error("Payment verification failed. Try again.")
verify_payment()

# === CONTENT LISTS (UK SOLOPRENEUR FOCUSED) ===
HOOKS = ["Ever feel like UK solopreneur life is a rollercoaster?", "I quit my job to go solo... and spent 3 months on a logo.", "UK 2025 trend: No-code MVPs are the new black.", "Validating your idea? I cold-DM'd 10 strangers last week. 7 replied."]
VALUES = ["Key insight: Validate fast – interview 10 ideal customers in Week 1.", "MVP magic: Adalo for apps, Carrd for sites. Launched mine in 48hrs.", "LinkedIn algo hack: Post 3x/week with hooks + value.", "SEO basics for solos: Target 'UK [niche] guide' keywords."]
CTAS = ["Loved this? DM 'GROW' for my free UK solopreneur checklist.", "No-code newbie? Grab my Adalo template – £27. Link in bio.", "AI your content: Try LinkedIn30 for £9 first month.", "Connections goal: Add 10 UK founders this week."]

DAYS = ["Mon 8AM", "Tue 9AM", "Wed 10AM", "Thu 11AM", "Fri 12PM", "Sat 1PM", "Sun 2PM"] * 5

# === SCRAPE & GENERATE ===
def scrape_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        return ' '.join([p.get_text() for p in soup.find_all('p')])[:3000]
    except:
        return "Sample blog: Starting a UK solopreneur business in 2025 is thrilling. Focus on validating your idea with 10 customer interviews. Build an MVP using no-code tools like Bubble or Adalo. Market via LinkedIn: share daily value posts. Scale by automating content with AI."

def generate_posts(text):
    words = text.split()
    posts = []
    for i in range(30):
        day = DAYS[i]
        if i < 10: base = random.choice(HOOKS); ptype = "Hook"
        elif i < 20: base = random.choice(VALUES); ptype = "Value"
        else: base = random.choice(CTAS); ptype = "CTA"
        keywords = [w for w in set(words) if len(w) > 5 and w.lower() not in ['about', 'their', 'with']]
        if keywords: base = base.replace("UK", f"UK {random.choice(keywords)}", 1)
        post = base + " #UKStartup #SolopreneurLife"
        posts.append({"Day": f"Day {i+1}", "Type": ptype, "Post": post, "Time": day})
    return posts

def text_to_png(text, title):
    img = Image.new('RGB', (1080, 1080), '#0A66C2')
    draw = ImageDraw.Draw(img)
    try: title_font = ImageFont.truetype("Arial Bold.ttf", 80)
    except: title_font = ImageFont.load_default()
    try: body_font = ImageFont.truetype("Arial.ttf", 60)
    except: body_font = ImageFont.load_default()
    draw.text((80, 80), title, 'white', title_font)
    draw.multiline_text((80, 220), textwrap.fill(text, 35), 'white', body_font, 20)
    draw.text((80, 920), "linkedin30.app", '#ffffff88', body_font)
    draw.rectangle([0, 0, 1079, 1079], outline='white', width=8)
    buf = io.BytesIO(); img.save(buf, 'PNG'); return buf.getvalue()

# === MAIN APP ===
url = st.text_input("Paste your blog or YouTube URL:", placeholder="https://yourblog.com/post")

if st.button("Generate 30-Day LinkedIn Calendar", type="primary"):
    if not st.session_state.is_pro and st.session_state.generations_today >= 1:
        st.warning("Free limit reached (1/day). Upgrade to Pro for unlimited!")
    else:
        with st.spinner("Generating your 30-day plan..."):
            text = scrape_text(url)
            posts = generate_posts(text)
            df = pd.DataFrame(posts)
            st.success("Done! Here's your plan:")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode()
            st.download_button("Download CSV", csv, "linkedin30_calendar.csv", "text/csv")

            st.markdown("### 5 Pro Carousel Images")
            carousel_texts = [
                ("Hook Example", df.iloc[0]["Post"]),
                ("Value Tip", df.iloc[11]["Post"]),
                ("Call to Action", df.iloc[21]["Post"]),
                ("SEO Hack", "Rank #1 for 'UK solopreneur tips' in 30 days"),
                ("AI Win", "Saved 10hrs/week with AI content")
            ]
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for i, (title, text) in enumerate(carousel_texts):
                    png = text_to_png(text, title)
                    zf.writestr(f"carousel_{i+1}.png", png)
                    st.image(png, width=300)
            st.download_button("Download Carousels (ZIP)", zip_buffer.getvalue(), "linkedin30_carousels.zip", "application/zip")
            if not st.session_state.is_pro:
                st.session_state.generations_today += 1

# === FOOTER ===
st.markdown("---")
st.markdown("<p style='text-align:center; color:#666; font-size:0.9rem;'>© 2025 LinkedIn30 | Built for UK Solopreneurs</p>", unsafe_allow_html=True)
