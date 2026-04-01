import os
import io
import base64
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from rdkit import Chem
from rdkit.Chem import Draw, AllChem, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D

app = Flask(__name__)
CORS(app)

DEFAULT_SMILES = "CC1=C2C(=C(C=C1O)O)C(=O)C3=C(C2=O)C=C(C=C3O)O[C@H]4C[C@H](O)[C@@H](O[C@@H]5C[C@H](N(C)C)[C@@H](O)[C@H](O)C5O)O4"


def analyze_molecule(smiles: str):
    """Core RDKit analysis: chiral centers + R/S + molecule image."""
    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        return None, "Invalid SMILES string. Please check the input."

    # Add Hs and assign stereochemistry for accurate CIP labels
    mol_h = Chem.AddHs(mol)
    AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv3())
    Chem.AssignStereochemistry(mol, force=True, cleanIt=True)

    # Find all chiral centers (including unassigned ones)
    chiral_centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True)

    # Build per-atom details
    centers = []
    for atom_idx, config in chiral_centers:
        atom = mol.GetAtomWithIdx(atom_idx)
        centers.append({
            "atom_index": atom_idx,
            "element": atom.GetSymbol(),
            "configuration": config,
        })

    # Highlight chiral atoms in the 2D drawing
    highlight_atoms = [c["atom_index"] for c in centers]
    highlight_colors = {
        idx: (0.2, 0.8, 0.6) for idx in highlight_atoms  # teal highlights
    }

    drawer = rdMolDraw2D.MolDraw2DSVG(700, 420)
    drawer.drawOptions().addStereoAnnotation = True
    drawer.drawOptions().addAtomIndices = False
    try:
        rdMolDraw2D.PrepareMolForDrawing(mol)
        drawer.DrawMolecule(
            mol,
            highlightAtoms=highlight_atoms,
            highlightAtomColors=highlight_colors,
        )
    except Exception:
        drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    svg_data = drawer.GetDrawingText()

    # Encode SVG as base64 for safe JSON transport
    svg_b64 = base64.b64encode(svg_data.encode("utf-8")).decode("utf-8")

    # Molecular formula
    formula = rdMolDescriptors.CalcMolFormula(mol)

    return {
        "formula": formula,
        "num_atoms": mol.GetNumAtoms(),
        "num_chiral_centers": len(centers),
        "chiral_centers": centers,
        "molecule_svg": svg_b64,
    }, None


@app.route("/")
def index():
    return render_template("index.html", default_smiles=DEFAULT_SMILES)


@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True)
    smiles = data.get("smiles", "").strip()

    if not smiles:
        return jsonify({"error": "No SMILES string provided."}), 400

    result, error = analyze_molecule(smiles)
    if error:
        return jsonify({"error": error}), 422

    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
