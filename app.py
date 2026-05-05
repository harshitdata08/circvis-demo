import base64
import json
import os
import re
 
import anthropic
import streamlit as st
from PIL import Image
 
# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CIRCVIS Demo",
    page_icon="♻️",
    layout="wide",
)
 
# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');
 
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }
 
.main { background: #0a0e0a; }
 
.stApp { background: #0a0e0a; color: #e8f5e8; }
 
h1 { 
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    color: #4ade80 !important;
    letter-spacing: -1px !important;
}
 
.badge {
    display: inline-block;
    background: #22c55e22;
    border: 1px solid #4ade8066;
    border-radius: 100px;
    padding: 4px 16px;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: #4ade80;
    letter-spacing: 2px;
    margin-bottom: 8px;
}
 
.result-box {
    background: #1a231a;
    border: 1px solid #4ade80;
    border-radius: 14px;
    padding: 20px 24px;
    margin-top: 12px;
}
 
.class-label {
    font-size: 2.2rem;
    font-weight: 800;
    color: #4ade80;
    text-transform: uppercase;
    letter-spacing: -1px;
}
 
.reasoning-box {
    background: #121812;
    border: 1px solid #2a3d2a;
    border-radius: 10px;
    padding: 14px 16px;
    font-family: 'Space Mono', monospace;
    font-size: 12px;
    color: #a0b8a0;
    line-height: 1.7;
    margin-top: 14px;
}
 
.mono { font-family: 'Space Mono', monospace; font-size: 12px; color: #6b8f6b; }
</style>
""", unsafe_allow_html=True)
 
# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
CLASSES = ["cardboard", "glass", "metal", "paper", "plastic", "trash"]
EMOJIS  = {
    "cardboard": "📦",
    "glass":     "🍶",
    "metal":     "🥫",
    "paper":     "📄",
    "plastic":   "🧴",
    "trash":     "🗑️",
}
 
CLASSIFY_PROMPT = """You are CIRCVIS — a waste classification AI for circular economy cities.
 
Analyze this waste image and classify it into exactly one of these 6 categories:
cardboard, glass, metal, paper, plastic, trash
 
Respond ONLY with valid JSON (no markdown, no extra text):
{
  "class": "<one of the 6 classes>",
  "confidence": <float 0.0–1.0>,
  "probabilities": {
    "cardboard": <float>,
    "glass": <float>,
    "metal": <float>,
    "paper": <float>,
    "plastic": <float>,
    "trash": <float>
  },
  "reasoning": "<2–3 sentences in Hinglish explaining which visual features led to this prediction>"
}
 
All 6 probability values must sum to exactly 1.0.
The predicted class must have the highest probability."""
 
 
# ─────────────────────────────────────────────
#  HELPER: image → base64
# ─────────────────────────────────────────────
def image_to_base64(pil_img: Image.Image) -> str:
    import io
    buf = io.BytesIO()
    pil_img.convert("RGB").save(buf, format="JPEG")
    return base64.standard_b64encode(buf.getvalue()).decode()
 
 
# ─────────────────────────────────────────────
#  HELPER: call Claude API
# ─────────────────────────────────────────────
def classify_image(api_key: str, pil_img: Image.Image) -> dict:
    client = anthropic.Anthropic(api_key=api_key)
    b64 = image_to_base64(pil_img)
 
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": CLASSIFY_PROMPT,
                    },
                ],
            }
        ],
    )
 
    raw = message.content[0].text.strip()
    # strip possible ```json fences
    raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    return json.loads(raw)
 
 
# ─────────────────────────────────────────────
#  UI — HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="badge">● CIRCVIS LIVE DEMO</div>', unsafe_allow_html=True)
st.title("♻️ CIRCVIS — Waste Classification")
st.caption("Context-Aware Waste Classification for Circular Cities · Powered by Claude AI")
 
st.markdown("---")
 
# ─────────────────────────────────────────────
#  UI — API KEY (sidebar)
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 API Key Setup")
 
    # Pehle Streamlit Secrets se try karo (Streamlit Cloud ke liye)
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") if hasattr(st, "secrets") else ""
 
    # Agar secrets mein nahi mila toh manually input lo
    if not api_key:
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-api03-...",
            help="console.anthropic.com pe jaake free key banao",
        )
        if api_key:
            if api_key.startswith("sk-ant-"):
                st.success("✅ Key ready hai!")
            else:
                st.error("❌ Invalid key format")
    else:
        st.success("✅ Key Secrets se load hui!")
 
    st.markdown("---")
    st.markdown("**Supported Categories**")
    for cls in CLASSES:
        st.markdown(f"{EMOJIS[cls]} `{cls}`")
 
    st.markdown("---")
    st.markdown(
        '<p class="mono">CIRCVIS v2.0<br>Claude AI Vision</p>',
        unsafe_allow_html=True,
    )
 
# ─────────────────────────────────────────────
#  UI — MAIN CONTENT
# ─────────────────────────────────────────────
col_upload, col_result = st.columns([1, 1], gap="large")
 
with col_upload:
    st.subheader("📸 Image Upload")
    uploaded = st.file_uploader(
        "Waste ki image select karo",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
 
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, caption="Uploaded Image", use_container_width=True)
        st.markdown(
            f'<p class="mono">Size: {img.size[0]}×{img.size[1]} px | Format: {uploaded.type}</p>',
            unsafe_allow_html=True,
        )
 
with col_result:
    st.subheader("🤖 AI Prediction")
 
    if not uploaded:
        st.info("⬅️ Pehle ek waste image upload karo")
    elif not api_key or not api_key.startswith("sk-ant-"):
        st.warning("🔑 Sidebar mein apna Anthropic API key daalo")
    else:
        classify_btn = st.button(
            "🔍 Classify Karo — AI Se",
            use_container_width=True,
            type="primary",
        )
 
        if classify_btn:
            with st.spinner("Claude AI analyze kar raha hai..."):
                try:
                    result = classify_image(api_key, img)
 
                    predicted = result["class"].lower()
                    confidence = result["confidence"]
                    probs = result["probabilities"]
                    reasoning = result.get("reasoning", "—")
 
                    # ── Result box ──
                    st.markdown(
                        f"""
                        <div class="result-box">
                            <div style="font-family:Space Mono,monospace;font-size:11px;color:#6b8f6b;letter-spacing:2px;">PREDICTED CLASS</div>
                            <div class="class-label">{EMOJIS.get(predicted,'♻️')} {predicted.upper()}</div>
                            <div style="font-family:Space Mono,monospace;font-size:12px;color:#6b8f6b;margin-top:4px;">
                                Confidence: {confidence*100:.1f}%
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
 
                    # ── Probability bars ──
                    st.markdown("**Class Probabilities**")
                    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                    for label, prob in sorted_probs:
                        is_top = label == predicted
                        bar_col, val_col = st.columns([5, 1])
                        with bar_col:
                            st.progress(
                                float(prob),
                                text=f"{EMOJIS.get(label,'♻️')} {label}",
                            )
                        with val_col:
                            color = "#a3e635" if is_top else "#6b8f6b"
                            st.markdown(
                                f'<div style="font-family:Space Mono,monospace;font-size:12px;color:{color};padding-top:8px;">{prob*100:.1f}%</div>',
                                unsafe_allow_html=True,
                            )
 
                    # ── Reasoning ──
                    st.markdown(
                        f'<div class="reasoning-box"><b style="color:#4ade80;font-size:10px;letter-spacing:2px;">AI REASONING</b><br><br>{reasoning}</div>',
                        unsafe_allow_html=True,
                    )
 
                except json.JSONDecodeError:
                    st.error("❌ AI response parse nahi hua — dobara try karo")
                except anthropic.AuthenticationError:
                    st.error("❌ Invalid API key — check karo")
                except anthropic.APIError as e:
                    st.error(f"❌ API Error: {e}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
 
