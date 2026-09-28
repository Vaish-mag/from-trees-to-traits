"""
app.py - the project website.   Run it with:   streamlit run app.py

Three pages: what the project is, the analysis itself, and how it works.
Nothing here is pre-baked - main.py computes every number while you watch.
"""
import io
import os
import re

import streamlit as st

import main
import figures

figures.SAVE_PNG = False        # draw charts on the page instead of saving files

CHARTS = [
    ("fig1_dna_structure",      "🧬 The DNA",     "The real DNA at the best spot."),
    ("fig2_phylogeny",          "🌳 Family tree", "The red names should sit on separate branches."),
    ("fig3_phylog2p",           "📊 The result",  "A dot at 1.0 is a spot only the marked species share."),
    ("fig4_pangenome_graph",    "🕸 The map",     "Where the path splits, the species differ."),
    ("fig5_pangenome_openness", "📈 How varied",  "Red line climbing = every species adds new DNA."),
    ("fig6_structure_mapping",  "🔬 3D shape",    "The red balls are the spots, on the real protein."),
]
TEAM = ["Vaishnavi Magadum", "Adarsh Madivala", "Bhavya Pandya",
        "Avatar Pacharane", "Sakshi Paradkar"]

st.set_page_config("From Trees to Traits", "🧬", layout="wide")
st.markdown("""<style>
[data-testid='stAppDeployButton'], #MainMenu, footer {display: none}
.stApp {background: #F4F7FB}
section[data-testid='stSidebar'] {background: #12304D}
section[data-testid='stSidebar'] * {color: #DCE6F2}
.hero {background: linear-gradient(105deg, #12304D, #2E7DD1); color: #fff;
       padding: 1.5rem 2rem; border-radius: 14px; margin-bottom: 1.1rem}
.hero h1 {color: #fff; margin: 0; font-size: 2rem}
.hero p  {color: #CFE0F3; margin: .4rem 0 0; font-size: 1.05rem}
.card {background: #fff; border: 1px solid #E1E8F0; border-radius: 12px;
       padding: 1rem 1.2rem; height: 100%}
.card h4 {margin: .1rem 0 .5rem; color: #12304D}
.card p  {margin: 0; color: #46586B; font-size: .94rem}
[data-testid='stMetric'] {background: #fff; border: 1px solid #E1E8F0;
       border-radius: 12px; padding: .8rem 1rem}
</style>""", unsafe_allow_html=True)


def hero(title, sub=""):
    st.markdown(f"<div class='hero'><h1>{title}</h1>"
                + (f"<p>{sub}</p>" if sub else "") + "</div>",
                unsafe_allow_html=True)


def card(col, title, body):
    col.markdown(f"<div class='card'><h4>{title}</h4><p>{body}</p></div>",
                 unsafe_allow_html=True)


def headline(ds):
    """The RESULT line of an earlier command-line run, if there is one."""
    path = f"results/{ds}/report.txt"
    for line in open(path) if os.path.exists(path) else []:
        if line.startswith("RESULT:"):
            return line[7:].strip()
    return "not run yet"


def png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=170, bbox_inches="tight")
    return buf.getvalue()


def read_fasta_upload(file):
    """A dropped FASTA file -> {name: DNA} and {name: what its header says}.

    Only the name and the DNA are analysed. The rest of the header (organism,
    accession, trait) is shown to you so you can see whose gene each one is.
    """
    seqs, info, name = {}, {}, None
    for line in file.getvalue().decode("utf-8", "replace").splitlines():
        if line.startswith(">"):
            bits = line[1:].split()
            name = bits[0]
            org = re.search(r"organism=([A-Za-z]+ [A-Za-z]+)", line)
            tr = re.search(r"trait=(\d)", line)
            seqs[name] = ""
            info[name] = dict(
                accession=bits[1] if len(bits) > 1 and "=" not in bits[1] else "—",
                organism=org.group(1) if org else "—",
                trait=int(tr.group(1)) if tr else 0)
        elif name:
            seqs[name] += re.sub(r"[^ACGTacgt]", "", line).upper()
    return seqs, info


# ------------------------------------------------------------- sidebar -----
with st.sidebar:
    st.markdown("## 🧬 From Trees to Traits")
    st.caption("Comparative genomics & pan-genomes")
    page = st.radio("Go to", ["🏠 Home", "🔬 Run the analysis", "📖 How it works"],
                    label_visibility="collapsed")
    st.divider()
    st.caption("**Group**\n\n" + "\n\n".join(TEAM))

# ---------------------------------------------------------------- home -----
if page == "🏠 Home":
    hero("From Trees to Traits",
         "Which DNA letters let bats and dolphins hunt using echoes?")
    a, b, c = st.columns(3)
    card(a, "What is PhyloG2P?",
         "A way to link DNA to a feature. If animals that are <b>not related</b> "
         "evolved the same feature and share the same DNA letter, that letter "
         "cannot be inherited - each group changed it on its own.")
    card(b, "What is a pan-genome graph?",
         "Instead of one animal's DNA as 'the reference', every animal's DNA is "
         "kept in one map. Where they differ, the map forks and joins again. "
         "Nothing gets thrown away.")
    card(c, "What does this project do?",
         "It downloads real DNA from NCBI, lines it up, builds the family tree, "
         "scores every position, tests it 10,000 times and draws the result. "
         "Five genes, 9-11 mammals each.")
    st.write("")
    st.subheader("The five genes")
    st.table([{"Gene": main.DATASETS[d]["gene"],
               "What this gene does": main.DATASETS[d].get("plain", ""),
               "Feature tested": main.DATASETS[d]["trait"],
               "Result": headline(d)} for d in main.DATASETS])
    st.caption("Three hearing genes each find something. GAPDH (an unrelated "
               "housekeeping gene) and myoglobin correctly find nothing - those "
               "are the controls that show the method is honest.")

# ----------------------------------------------------------------- run -----
elif page == "🔬 Run the analysis":
    hero("Run the analysis")
    gene = st.selectbox("Choose a gene", list(main.DATASETS),
                        format_func=lambda k: f"{k}  ({main.DATASETS[k]['gene']})")
    cfg = main.DATASETS[gene]
    st.caption(f"**{cfg.get('plain', '')}**  ·  {cfg['note']}")
    up = st.file_uploader("…or drag and drop your own FASTA file here",
                          type=["fasta", "fa", "fna", "txt"])
    cds, info = read_fasta_upload(up) if up else (None, {})

    with st.expander("📁 No FASTA file of your own? Take a real one"):
        for col, ds in zip(st.columns(len(main.DATASETS)), main.DATASETS):
            path = f"data/{ds}_cds.fasta"
            if os.path.exists(path):
                text = open(path, "rb").read()
                col.download_button(f"⬇ {main.DATASETS[ds]['gene']}", text,
                                    file_name=f"{ds}.fasta", key=f"dl_{ds}",
                                    width="stretch")
                col.caption(f"{text.count(b'>')} species")
            else:
                col.caption(f"{main.DATASETS[ds]['gene']} — press Deploy once "
                            "to download it")

    if cds:
        st.success(f"Read {len(cds)} sequences from **{up.name}**")
        st.write("**What is in your file:**")
        st.table([{"Species": n, "Organism": info[n]["organism"],
                   "NCBI accession": info[n]["accession"],
                   "DNA letters": len(s),
                   "Protein letters": len(main.translate(s))}
                  for n, s in cds.items()])
        st.write("**Tick the species that have the feature:**")
        cols = st.columns(4)
        trait = {n: cols[i % 4].checkbox(n, value=bool(info[n]["trait"]),
                                         key=f"tick_{n}")
                 for i, n in enumerate(cds)}
        if any(info[n]["trait"] for n in cds):
            st.caption("Ticks were filled in from the `trait=` note in your file. "
                       "Change them if you want to ask a different question.")
        ref = st.selectbox("Compare everything against", list(cds))
        if sum(trait.values()) in (0, len(trait)):
            st.error("Tick at least one species, and leave at least one unticked.")
            st.stop()

    if st.button("🚀 Deploy", type="primary", width="stretch"):
        with st.spinner("Downloading the DNA, lining it up, testing it 10,000 times…"):
            if cds:
                meta = dict(name="upload", gene="your gene", positive="has it",
                            negative="does not have it", phenotype="the feature",
                            note="Your uploaded file.", pdb=None, uniprot=None)
                r = main.analyse(cds, {n: int(v) for n, v in trait.items()}, ref, meta)
            else:
                r = main.run(gene)
            st.session_state.r = r
            st.session_state.figs = figures.make_all(r)

    r = st.session_state.get("r")
    if r:
        st.divider()
        figs = st.session_state.figs
        for tab, (key, label, hint) in zip(st.tabs([c[1] for c in CHARTS]), CHARTS):
            with tab:
                if figs.get(key) is None:
                    st.caption("This dataset has no 3D structure solved in a lab.")
                else:
                    st.caption(hint)
                    st.pyplot(figs[key], width="stretch")
                    st.download_button("⬇ Download this chart", png(figs[key]),
                                       file_name=f"{key}.png", key=f"png_{key}")

        with st.expander("📄 All the numbers"):
            st.code(main.report(r))
        st.download_button("⬇ Download the full report", main.report(r),
                           file_name=f"{r['name']}_report.txt")

# -------------------------------------------------------- how it works -----
else:
    hero("How it works", "Five steps, all on real sequence data.")
    st.markdown("""
**1. Get the DNA.** The coding sequence of one gene is downloaded for every
species from NCBI RefSeq and cached in `data/`. Nothing is simulated.

**2. Line it up.** Each sequence is translated to protein, aligned against the
reference species, and put back into a codon-aware DNA alignment, so no gap can
ever shift the reading frame.

**3. Build the family tree.** Jukes-Cantor distances, then a neighbour-joining
tree. The tree is what tells us whether the feature evolved once or many times.

**4. Score every position (PhyloG2P).** For each position:
`score = how common a letter is in the marked species − how common it is in the
rest`. A score of 1.0 means a perfect split. The p-value comes from shuffling
the labels across the same species 10,000 times.

**5. Build the pan-genome graph.** Identical stretches collapse into one shared
node; differences open a bubble with one node per version. Nodes are labelled
core / shell / cloud, and the graph measures how much sequence a single linear
reference cannot represent.
""")
    st.subheader("Honest limitations")
    st.markdown("""
* A simple star alignment, not a full progressive MSA.
* The score is presence/absence, not a substitution-rate model like RERconverge
  or PhyloAcc.
* One gene and 9-11 species per run, not a genome-wide scan.
* A convergent letter is a **candidate**, not proof of cause. That needs lab work.
""")
    st.subheader("Data sources")
    st.markdown("""
* Coding sequences — **NCBI RefSeq** (E-utilities)
* Structure — **RCSB PDB 7LGU**, human prestin, cryo-EM
* Domains & topology — **UniProt** (e.g. P58743)
""")
