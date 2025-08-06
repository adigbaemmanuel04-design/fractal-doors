import streamlit as st
import json, os, requests
from io import BytesIO
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ================== FAST CLEAN CSS ==================
st.set_page_config(page_title="Fractal Doors", page_icon="🚪", layout="centered")
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    :root{
        --primary:#0F3D3E; --accent:#F9B040; --bg:#FFFFFF;
    }
    .header {font-size:22px;font-weight:600;color:var(--primary);margin-bottom:20px;}
    .card {
        background:#FFFFFF;padding:18px;border-radius:8px;
        box-shadow:0 2px 4px rgba(0,0,0,0.04);margin-bottom:22px;
    }
    .stButton>button {
        background-color:var(--primary);border:none;color:white;border-radius:4px;padding:6px 14px;
    }
    .stButton>button:hover {
        background-color:var(--accent);color:black;
    }
    </style>
""", unsafe_allow_html=True)


# ================== CONFIG FILES ==================
PROFILE_FILE = "business_profile.json"
JOBS_FILE    = "jobs.json"
LOG_FILE     = "data_log.json"


# ================== BUSINESS PROFILE HANDLING ==================
def load_profile():
    return json.load(open(PROFILE_FILE)) if os.path.exists(PROFILE_FILE) else None

def save_profile(data):
    json.dump(data, open(PROFILE_FILE,"w"), indent=4)

profile = load_profile()
if not profile:
    st.markdown('<div class="header">Fractal Doors</div>', unsafe_allow_html=True)
    st.subheader("Business Profile Setup")
    name  = st.text_input("Business Name")
    ctype = st.selectbox("Company Type",["Carpenter/Joiner","Door Fabricator","Site Contractor","DIY/Individual"])
    addr  = st.text_area("Address")
    phone = st.text_input("Phone")
    email = st.text_input("Email")
    web   = st.text_input("Website (optional)")
    social= st.text_input("Social Media (optional)")
    if st.button("Sign up"):
        if not name or not phone or not email:
            st.error("Name / phone / email required")
        else:
            save_profile({"name":name,"type":ctype,"addr":addr,"phone":phone,"email":email,"website":web,"social":social})
            st.success("Profile created successfully ✅")
            st.rerun()
    st.stop()


# ================== HEADER + LOGOUT ==================
st.markdown(f'<div class="header">Fractal Doors</div>', unsafe_allow_html=True)
st.write(f"👤 Logged in as: **{profile['name']}**")

colL, colR = st.columns([6,1])
with colR:
    if st.button("Logout"):
        os.remove(PROFILE_FILE)
        st.rerun()


# ================== UTILS ==================
def load_jobs():  return json.load(open(JOBS_FILE)) if os.path.exists(JOBS_FILE) else {}
def save_job(jid,data):
    d = load_jobs(); d[jid] = data; json.dump(d,open(JOBS_FILE,"w"),indent=4)
def log_data(entry):
    log = json.load(open(LOG_FILE)) if os.path.exists(LOG_FILE) else []
    log.append(entry); json.dump(log,open(LOG_FILE,"w"),indent=4)
def calc_supplies(h,w,eff,thk):
    area=(h*w)/1e6; peri=(2*(h+w))/1000
    tape=peri*2; glue=area*0.2*(thk/35)
    return {"Edging Tape (m)":round(tape/eff,2),"Glue (L)":round(glue/eff,2)}


PRESETS = {
    "Simple":[
        {"n":"Top Rail","mat":"HDF","l":900,"w":100,"q":2},
        {"n":"Bottom Rail","mat":"HDF","l":900,"w":100,"q":2},
        {"n":"Left Stile","mat":"HDF","l":2100,"w":100,"q":2},
        {"n":"Right Stile","mat":"HDF","l":2100,"w":100,"q":2},
        {"n":"Center Panel","mat":"HDF","l":1800,"w":800,"q":1}],
    "Double Panel":[
        {"n":"Top Rail","mat":"HDF","l":900,"w":100,"q":2},
        {"n":"Bottom Rail","mat":"HDF","l":900,"w":100,"q":2},
        {"n":"Left Stile","mat":"HDF","l":2100,"w":100,"q":2},
        {"n":"Right Stile","mat":"HDF","l":2100,"w":100,"q":2},
        {"n":"Top Panel","mat":"HDF","l":800,"w":400,"q":1},
        {"n":"Bottom Panel","mat":"HDF","l":800,"w":400,"q":1}],
    "Flush":[
        {"n":"Face Sheet","mat":"MDF","l":2100,"w":900,"q":2},
        {"n":"Internal Frame","mat":"Plywood","l":2100,"w":40,"q":4}],
    "Louver":[
        {"n":"Left Stile","mat":"HDF","l":2100,"w":100,"q":2},
        {"n":"Right Stile","mat":"HDF","l":2100,"w":100,"q":2},
        {"n":"Louvers","mat":"HDF","l":600,"w":50,"q":12}],
    "Custom":[]
}


# ============= LOAD PREVIOUS JOB =============
with st.expander("📂 Load Saved Job"):
    jobs = load_jobs()
    if jobs:
        jobid = st.selectbox("Select Job",list(jobs.keys())[::-1])
        if st.button("Load Job"):
            st.session_state.loaded = jobs[jobid]
            st.success("Loaded ✅")
    else:
        st.info("No saved jobs")

data = st.session_state.get("loaded", {})


# STEP 1
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Step 1 – Opening & Thickness")
c1 = st.columns(3)
vl = c1[0].number_input("Left (mm)",1500,3000,data.get("vl",2100))
vc = c1[1].number_input("Centre (mm)",1500,3000,data.get("vc",2100))
vr = c1[2].number_input("Right (mm)",1500,3000,data.get("vr",2100))
c2 = st.columns(3)
hb = c2[0].number_input("Bottom (mm)",600,1500,data.get("hb",900))
hm = c2[1].number_input("Middle (mm)",600,1500,data.get("hm",900))
ht = c2[2].number_input("Top (mm)",600,1500,data.get("ht",900))
thickness=st.selectbox("Door Thickness",[30,35,40,45,50],index=1)
eff=st.slider("Efficiency",0.5,1.0,data.get("eff",0.85),0.01)
u_h=min(vl,vc,vr); u_w=min(hb,hm,ht)
st.info(f"Used: {u_w} × {u_h} mm @ {thickness}mm")
st.markdown('</div>',unsafe_allow_html=True)


# STEP 2
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Step 2 – Cutting List")
preset = st.selectbox("Preset Type", list(PRESETS.keys()))
components = PRESETS[preset].copy()
edited = []

for i, c in enumerate(components):
    nm = st.text_input("Name", c.get("n", ""), key=f"n{i}")
    mt = st.selectbox("Material", ["HDF","MDF","Plywood"], key=f"m{i}",
                      index=["HDF","MDF","Plywood"].index(c.get("mat","HDF")))
    ln = st.number_input("Length (mm)",100,3000,c.get("l",1000),key=f"l{i}")
    wd = st.number_input("Width (mm)",50,1500,c.get("w",100),key=f"w{i}")
    qt = st.number_input("Qty",1,10,c.get("q",1),key=f"q{i}")
    edited.append({"n":nm,"mat":mt,"l":ln,"w":wd,"q":qt})

if st.button("➕ Add Component"):
    edited.append({"n":"","mat":"HDF","l":1000,"w":100,"q":1})

st.markdown('</div>',unsafe_allow_html=True)


# STEP 3
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Step 3 – Hardware")
mode = st.radio("",["Standard","Custom"],horizontal=True)
defaultH = {'hinges':3,'lockset':1,'handle':1,'screws':20,'foam':1}
if mode == "Standard":
    hardware = defaultH
else:
    hardware = {}
    hardware['hinges']   = st.number_input("Hinges",1,10,defaultH['hinges'])
    hardware['lockset']  = st.number_input("Lockset",0,5,defaultH['lockset'])
    hardware['handle']   = st.number_input("Handle",0,5,defaultH['handle'])
    hardware['screws']   = st.number_input("Screws",0,200,defaultH['screws'])
    hardware['foam']     = st.number_input("Foam/Brush",0,10,defaultH['foam'])

st.markdown('</div>',unsafe_allow_html=True)


# GENERATE
if st.button("Generate Quote & Save"):
    supplies = calc_supplies(u_h,u_w,eff,thickness)
    full     = {**supplies,**hardware}

    buffer=BytesIO()
    styles=getSampleStyleSheet()
    doc=SimpleDocTemplate(buffer,pagesize=A4)
    el=[
        Paragraph(profile['name'],styles["Title"]),
        Paragraph(profile['addr'],styles["Normal"]),
        Paragraph(f"{profile['phone']} | {profile['email']}",styles["Normal"]),
        Paragraph((profile.get('website','') +' '+profile.get('social','')).strip(),styles["Normal"]),
        Spacer(1,8),
        Paragraph(f"Opening used: {u_w}×{u_h} @ {thickness}mm",styles["Normal"]),
        Paragraph(f"Preset: {preset}",styles["Normal"]),
        Spacer(1,6),
        Paragraph("CUTTING LIST",styles["Heading2"])
    ]
    tdata=[["Component","Mat","L","W","Q"]]+[[c['n'],c['mat'],c['l'],c['w'],c['q']] for c in edited]
    t=Table(tdata); t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),1,colors.grey)]))
    el.append(t); el.append(Spacer(1,6))
    el.append(Paragraph("SUPPLIES",styles["Heading2"]))
    t2=Table([["Item","Qty"]]+[[k,v] for k,v in full.items()])
    t2.setStyle(TableStyle([("GRID",(0,0),(-1,-1),1,colors.grey)]))
    el.append(t2)
    doc.build(el)

    jid=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_job(jid,{"vl":vl,"vc":vc,"vr":vr,"hb":hb,"hm":hm,"ht":ht,
                  "thick":thickness,"eff":eff,"preset":preset,
                  "components":edited,"hardware":hardware})

    try:
        ip=requests.get("https://api.ipify.org").text
    except:
        ip="unknown"
    log_data({"timestamp":jid,"ip":ip,"device_id":profile['name'],"version":profile['name'],
              "preset":preset,"height":u_h,"width":u_w,"thickness":thickness,
              "components":edited,"supplies":full})

    st.download_button("📥 Download Quote PDF",buffer.getvalue(),file_name=f"quote_{jid}.pdf")
    st.success("Saved & Logged ✅")
