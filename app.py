import streamlit as st
from rdkit import Chem
from rdkit.Chem import AllChem, rdMolDescriptors

# Draw requires Cairo — handle gracefully if unavailable
try:
    from rdkit.Chem import Draw
    HAS_DRAW = True
except Exception:
    HAS_DRAW = False

# ── Page config ──
st.set_page_config(
    page_title="ChiralSense — Stereochemistry Analyzer",
    page_icon="🔬",
    layout="centered"
)

# ── Custom CSS ──
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #34d399, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 4px;
    }
    .hero-sub {
        text-align: center;
        color: #94a3b8;
        font-size: 0.95rem;
        margin-bottom: 28px;
    }
    .stat-row {
        display: flex;
        gap: 12px;
        justify-content: center;
        flex-wrap: wrap;
        margin: 20px 0;
    }
    .stat-box {
        background: #0f1623;
        border: 1px solid rgba(52,211,153,0.25);
        border-radius: 12px;
        padding: 16px 28px;
        text-align: center;
        min-width: 130px;
    }
    .stat-num {
        font-size: 2rem;
        font-weight: 800;
        color: #34d399;
        line-height: 1;
    }
    .stat-lbl {
        font-size: 0.7rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }
    .config-R {
        background: rgba(52,211,153,0.15);
        color: #34d399;
        padding: 2px 10px;
        border-radius: 99px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .config-S {
        background: rgba(59,130,246,0.15);
        color: #3b82f6;
        padding: 2px 10px;
        border-radius: 99px;
        font-weight: 700;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Default SMILES ──
DEFAULT_SMILES = "CC1=C2C(=C(C=C1O)O)C(=O)C3=C(C2=O)C=C(C=C3O)O[C@H]4C[C@H](O)[C@@H](O[C@@H]5C[C@H](N(C)C)[C@@H](O)[C@H](O)C5O)O4"

# ── Hero ──
st.markdown('<div class="hero-title">🔬 ChiralSense</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Detect chiral centers &amp; assign R/S configuration using RDKit</div>', unsafe_allow_html=True)

# ── Student Info ──
st.markdown("""
<div style="
    background: linear-gradient(135deg, rgba(52,211,153,0.1), rgba(59,130,246,0.1));
    border: 1px solid rgba(52,211,153,0.3);
    border-radius: 12px;
    padding: 18px 28px;
    text-align: center;
    margin: 10px 0 20px 0;
">
    <p style="margin:4px 0; font-size:1.1rem; font-weight:700; color:#e2e8f0;">
        👤 NAME &nbsp;— &nbsp;ROHITH V
    </p>
    <p style="margin:4px 0; font-size:1rem; font-weight:600; color:#94a3b8;">
        🎓 REGISTER NUMBER &nbsp;— &nbsp;RA2511026050047
    </p>
</div>
""", unsafe_allow_html=True)

# ── Input ──
smiles = st.text_area(
    "**SMILES String**",
    value=DEFAULT_SMILES,
    height=100,
    help="Enter any valid isomeric SMILES string"
)

col1, col2 = st.columns([3, 1])
with col1:
    if st.button("💊 Load Doxorubicin Example"):
        smiles = DEFAULT_SMILES
with col2:
    analyze = st.button("🔍 Analyze", type="primary", use_container_width=True)

st.divider()

# ── Analysis ──
if analyze or smiles:
    if not smiles.strip():
        st.error("⚠️ Please enter a SMILES string.")
        st.stop()

    mol = Chem.MolFromSmiles(smiles.strip())

    if mol is None:
        st.error("❌ Invalid SMILES string. Please check the input and try again.")
        st.stop()

    # Assign stereochemistry
    Chem.AssignStereochemistry(mol, force=True, cleanIt=True)

    # Find chiral centers
    chiral_centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True)

    # Molecular formula
    formula = rdMolDescriptors.CalcMolFormula(mol)
    num_atoms = mol.GetNumAtoms()
    r_count = sum(1 for _, c in chiral_centers if c == "R")
    s_count = sum(1 for _, c in chiral_centers if c == "S")

    # ── Stats ──
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box"><div class="stat-num">{len(chiral_centers)}</div><div class="stat-lbl">Chiral Centers</div></div>
        <div class="stat-box"><div class="stat-num" style="color:#34d399">{r_count}</div><div class="stat-lbl">R Config</div></div>
        <div class="stat-box"><div class="stat-num" style="color:#3b82f6">{s_count}</div><div class="stat-lbl">S Config</div></div>
        <div class="stat-box"><div class="stat-num" style="color:#a855f7">{num_atoms}</div><div class="stat-lbl">Total Atoms</div></div>
        <div class="stat-box"><div class="stat-num" style="font-size:1rem;letter-spacing:-0.5px">{formula}</div><div class="stat-lbl">Formula</div></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Two columns: table + image ──
    left, right = st.columns([1, 1])

    with left:
        st.subheader("📊 Chiral Centers")
        if chiral_centers:
            table_data = []
            for i, (idx, config) in enumerate(chiral_centers):
                atom = mol.GetAtomWithIdx(idx)
                table_data.append({
                    "#": i + 1,
                    "Atom Index": idx,
                    "Element": atom.GetSymbol(),
                    "Config": config
                })
            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No chiral centers found in this molecule.")

    with right:
        st.subheader("⚛ 2D Structure")
        if HAS_DRAW:
            try:
                highlight_atoms = [idx for idx, _ in chiral_centers]
                img = Draw.MolToImage(
                    mol,
                    size=(400, 300),
                    highlightAtoms=highlight_atoms,
                    kekulize=True
                )
                st.image(img, use_container_width=True, caption="Chiral centers highlighted")
            except Exception as e:
                st.warning(f"Could not render molecule: {e}")
        else:
            st.info("🖼️ Molecule visualization unavailable on this environment.\nAnalysis results are fully accurate above.")

    # ── Summary ──
    st.success(f"✅ Analysis complete — **{len(chiral_centers)} chiral centers** found in `{formula}`")


