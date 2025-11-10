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

# === SECRETS (DO NOT CHANGE) ===
# These are set in Streamlit > Settings > Secrets
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]
STRIPE_PUBLISHABLE_KEY = st.secrets["STRIPE_PUBLISHABLE_KEY"]
PRICE_ID = st.secrets["PRICE_ID"]
APP_URL = st.secrets["APP_URL"]

# === PRO STYLING ===
st.set_page_config(page_title="LinkedIn30 – AI Content Calendar", layout="centered")
st.markdown("""
<style>
    .main {background-color: #0e1117; color: white; padding: 2rem;}
    .stButton>button {background: #0A66C2; color: white; border-radius: 12px; padding: 12px 24px; font-weight: bold; border: none;}
    .stTextInput>div>div>input {background: #1a1a1a; color: white; border: 1px solid #0A66C2; border-radius: 12px; padding: 12px;}
    h1 {color: #0A66C2; text-align: center; font-size: 2.8rem; margin-bottom: 0;}
    .subtitle {text-align: center; color: #aaa; font-size: 1.2rem; margin-bottom: 2rem;}
    .footer {text-align: center; margin-top: 60px; color: #666; font-size: 0.9rem;}
    .pro-badge {background: #0A66C2; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>LinkedIn30</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Turn 1 blog → 30 <b>high-engagement</b> LinkedIn posts in 60s</p>", unsafe_allow_html=True)

# === SESSION STATE ===
if 'is_pro' not in st.session_state:
    st.session_state.is_pro = False
if 'generations_today' not in st.session_state:
    st.session_state.generations_today = 0

# === UPGRADE CTA ===
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.session_state.is_pro:
        st.markdown("<p class='pro-badge'>PRO USER – UNLIMITED</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style='text-align:center; padding:24px; background:#1a1a1a; border-radius:16px; border:2px solid #0A66C2;'>
            <h3>Go Pro</h3>
            <p style='margin:8px 0;'><s>£19/month</s> → <b style='font-size:1.4rem;'>£9 first month</b></p>
            <p style='margin:8px 0; font-size:0.95rem;'>Unlimited calendars • Priority support • Export to PDF</p>
            <button id="checkout-button" style='background:#0A66C2; color:white; border:none; padding:12px 24px; border-radius:12px; font-weight:bold; cursor:pointer;'>
                Upgrade Now
            </button>
        </div>
        """, unsafe_allow_html=True)
        
        # Stripe Checkout JS
        st.markdown(f"""
        <script src="https://js.stripe.com/v3/"></script>
        <script>
        const stripe = Stripe('{STRIPE_PUBLISHABLE_KEY}');
        document.getElementById('checkout-button').addEventListener('click', () => {{
            stripe.redirectToCheckout({{
                lineItems: [{{ price: '{PRICE_ID}', quantity: 1 }}],
                mode: 'subscription',
                successUrl: '{APP_URL}?session_id={{CHECKOUT_SESSION_ID}}',
                cancelUrl: '{APP_URL}',
            }});
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
                st.success("Payment successful! Welcome to Pro.")
                st.rerun()
        except:
            pass

verify_payment()

# === CONTENT LISTS ===
HOOKS = [
    "Ever feel like UK solopreneur life is a rollercoaster?",
    "'I quit my job to go solo... and spent 3 months on a logo.' Sound familiar?",
    "UK 2025 trend: No-code MVPs are the new black.",
    "Validating your idea? I cold-DM'd 10 strangers last week. 7 replied.",
    "Pitfall alert: Ignoring SEO as a solo founder = slow death.",
    "Automate or die: AI wrote my last 5 LinkedIn posts.",
    "From side-hustle to £5k/mo: My UK solopreneur blueprint.",
    "'Boundaries? What's that?' – Every burned-out founder ever.",
    "Scaling solo: Outsource to VAs before you crash.",
    "Weekend win: 50 new connections from one carousel."
]

VALUES = [
    "Key insight: Validate fast – interview 10 ideal customers in Week 1.",
    "MVP magic: Adalo for apps, Carrd for sites. Launched mine in 48hrs.",
    "LinkedIn algo hack: Post 3x/week with hooks + value.",
    "SEO basics for solos: Target 'UK [niche] guide' keywords.",
    "AI content tip: Prompt like 'Write a hook for [topic] targeting UK founders.'",
    "Burnout buster: Time-block 'deep work' mornings, admin afternoons.",
    "VA outsourcing: Upwork for £5–10/hr tasks.",
    "Metrics that matter: Track MRR, not likes.",
    "Networking win: Join UK Startup Slack – 5k members.",
    "Content repurposing: Blog → LinkedIn → Twitter thread."
]

CTAS = [
    "Loved this? DM 'GROW' for my free UK solopreneur checklist.",
    "Ready to validate? Book a 15-min call: [calendly]",
    "No-code newbie? Grab my Adalo template – £27. Link in bio.",
    "SEO audit? Reply 'AUDIT' – I'll review your site free.",
    "AI your content: Try LinkedIn30 for £9 first month.",
    "Burnout check: Take my 2-min quiz. DM 'QUIZ'.",
    "Scale hack: Outsource your first task today.",
    "Connections goal: Add 10 UK founders this week.",
    "Metrics mastery: Download my tracker sheet. £0.",
    "End-month boost: Share your biggest win from this calendar."
]

DAYS = ["Mon 8AM", "Tue 9AM", "Wed 10AM", "Thu 11AM", "Fri 12PM", "Sat 1PM", "Sun 2PM"] * 5

# === SCRAPE BLOG ===
def scrape_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        text = ' '.join([p.get_text() for p in soup.find_all('p')])
        return text[:3000]
    except:
        return "Sample blog: Starting a UK solopreneur business in 2025 is thrilling. Focus on validating your idea with 10 customer interviews. Build an MVP using no-code tools like Bubble or Adalo. Market via LinkedIn: share daily value posts. Scale by automating content with AI. Common pitfalls: ignoring SEO and burning out without boundaries."

# === GENERATE POSTS ===
def generate_posts(text):
    words = text.split()
    posts = []
    for i in range(30):
        day = DAYS[i]
        if i < 10:
            base = random.choice(HOOKS)
            post_type = "Hook"
        elif i < 20:
            base = random.choice(VALUES)
            post_type = "Value"
        else:
            base = random.choice(CTAS)
            post_type = "CTA"
        
        keywords = [w for w in set(words) if len(w) > 5 and w.lower() not in ['about', 'their', 'with']]
        injected = random.sample(keywords, k=min(2, len(keywords))) if keywords else []
        
        post = base
        for kw in injected:
            post = post.replace("UK", f"UK {kw}", 1) if "UK" in post else post.replace("your", f"your {kw}", 1)
        
        post += f" #UKStartup #SolopreneurLife"
        posts.append({"Day": f"Day {i+1}", "Type": post_type, "Post": post, "Time": day})
    return posts

# === PRO CAROUSEL DESIGN ===
def text_to_png(text, title):
    img = Image.new('RGB', (1080, 1080), color='#0A66C2')
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("Arial Bold.ttf", 80)
        body_font = ImageFont.truetype("Arial.ttf", 60)
    except:
        title_font = ImageFont.load_default()
        body_font = title_font
    
    draw.text((80, 80), title, fill='white', font=title_font)
    wrapped = textwrap.fill(text, width=35)
    draw.multiline_text((80, 220), wrapped, fill='white', font=body_font, spacing=20)
    draw.text((80, 920), "linkedin30.app | Built for UK Solopreneurs", fill='#ffffff88', font=body_font)
    draw.rectangle([0, 0, 1079, 1079], outline='white', width=8)
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# === MAIN APP ===
url = st.text_input("Paste your blog or YouTube URL:", placeholder="https://yourblog.com/post", key="url_input")

if st.button("Generate 30-Day LinkedIn Calendar", type="primary"):
    if not st.session_state.is_pro and st.session_state.generations_today >= 1:
        st.warning("Free limit reached (1/day). Upgrade to Pro for unlimited!")
    else:
        with st.spinner("Scraping + generating your 30-day plan..."):
            text = scrape_text(url)
            posts = generate_posts(text)
            df = pd.DataFrame(posts)
            
            st.success("Done! Here's your 30-day LinkedIn plan:")
            st.dataframe(df, use_container_width=True)
            
            # CSV
            csv = df.to_csv(index=False).encode()
            st.download_button("Download CSV Calendar", csv, "linkedin30_calendar.csv", "text/csv")
            
            # CAROUSELS
            st.markdown("### 5 Pro Carousel Images (1080×1080)")
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
                    png_data = text_to_png(text, title)
                    zf.writestr(f"carousel_{i+1}.png", png_data)
                    st.image(png_data, caption=f"{title}", width=300)
            
            st.download_button("Download All Carousels (ZIP)", zip_buffer.getvalue(), "linkedin30_carousels.zip", "application/zip")
            
            # Count generation
            if not st.session_state.is_pro:
                st.session_state.generations_today += 1

# === FOOTER ===
st.markdown("---")
st.markdown("<p class='footer'>© 2025 LinkedIn30 | Built for UK Solopreneurs</p>", unsafe_allow_html=True)
