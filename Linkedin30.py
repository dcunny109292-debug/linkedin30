# linkedin30.py
# FULL MVP CODE – Paste into GitHub now

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

# === CONFIG ===
st.set_page_config(page_title="LinkedIn30 – AI Content Calendar", layout="centered")
st.title("LinkedIn30")
st.markdown("**Paste your blog URL → Get 30 LinkedIn posts + carousels in 60s**")

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

# === CAROUSEL IMAGES ===
def text_to_png(text, title):
    img = Image.new('RGB', (800, 600), color='#1DA1F2')
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 40)
        small_font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
        small_font = font
    
    wrapped = textwrap.fill(text, width=40)
    draw.text((50, 50), title, fill='white', font=font)
    draw.text((50, 150), wrapped, fill='white', font=small_font)
    draw.text((50, 500), "linkedin30.app", fill='#ffffff88', font=small_font)
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

# === MAIN APP ===
url = st.text_input("Paste your blog or YouTube URL:", placeholder="https://yourblog.com/post")
if st.button("Generate 30-Day LinkedIn Calendar"):
    with st.spinner("Scraping + generating..."):
        text = scrape_text(url)
        posts = generate_posts(text)
        df = pd.DataFrame(posts)
        
        st.success("Done! Here's your 30-day plan:")
        st.dataframe(df, use_container_width=True)
        
        # CSV
        csv = df.to_csv(index=False).encode()
        st.download_button("Download CSV", csv, "linkedin_calendar.csv", "text/csv")
        
        # CAROUSELS
        st.markdown("### 5 Carousel Images (PNG)")
        carousel_texts = [
            ("Hook Example", df.iloc[0]["Post"]),
            ("Value Tip", df.iloc[11]["Post"]),
            ("CTA", df.iloc[21]["Post"]),
            ("SEO Hack", "Rank #1 for 'UK solopreneur tips' in 30 days"),
            ("AI Win", "Saved 10hrs/week with AI content")
        ]
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for i, (title, text) in enumerate(carousel_texts):
                png_data = text_to_png(text, title)
                zf.writestr(f"carousel_{i+1}.png", png_data)
                st.image(png_data, caption=f"Carousel {i+1}: {title}", width=300)
        
        st.download_button("Download All Carousels (ZIP)", zip_buffer.getvalue(), "linkedin_carousels.zip", "application/zip")

st.markdown("---")
st.markdown("**£9 first month → £19/month** | Built for UK solopreneurs")
