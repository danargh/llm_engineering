"""
=============================================================
  SIMULASI CARA KERJA TRANSFORMER (LLM) — Bahan Belajar
=============================================================
Menyederhanakan arsitektur Transformer supaya bisa dipahami
secara visual dan intuitif. Setiap langkah divisualisasikan.

Langkah yang disimulasikan:
  1. Tokenisasi kalimat
  2. Embedding token ke vektor
  3. Positional Encoding
  4. Attention Scores (Q, K, V)
  5. Output prediksi token berikutnya
=============================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import warnings
warnings.filterwarnings('ignore')

# ── warna tema gelap yang nyaman ──────────────────────────
BG      = "#0f1117"
PANEL   = "#1a1d27"
BLUE    = "#4a9eff"
TEAL    = "#2dd4bf"
AMBER   = "#fbbf24"
CORAL   = "#f87171"
PURPLE  = "#a78bfa"
WHITE   = "#e2e8f0"
GRAY    = "#475569"
LGRAY   = "#94a3b8"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor":   PANEL,
    "axes.edgecolor":   GRAY,
    "axes.labelcolor":  LGRAY,
    "text.color":       WHITE,
    "xtick.color":      LGRAY,
    "ytick.color":      LGRAY,
    "grid.color":       "#2d3748",
    "grid.linewidth":   0.5,
    "font.family":      "monospace",
})

np.random.seed(42)

# ─────────────────────────────────────────────────────────
#  KALIMAT INPUT
# ─────────────────────────────────────────────────────────
sentence = "kucing makan ikan"
tokens   = sentence.split()
n_tokens = len(tokens)
d_model  = 8   # dimensi embedding (kecil agar mudah divisualisasi)

print("=" * 55)
print("  SIMULASI TRANSFORMER — LLM SEDERHANA")
print("=" * 55)
print(f"\nKalimat input : '{sentence}'")
print(f"Token         : {tokens}")
print(f"Dimensi model : {d_model}")

# ─────────────────────────────────────────────────────────
#  STEP 1 — EMBEDDING
#  Setiap token dipetakan ke vektor angka (embedding lookup)
# ─────────────────────────────────────────────────────────
vocab = {
    "kucing": np.array([0.9,  0.2, -0.4,  0.7,  0.1, -0.3,  0.8,  0.5]),
    "makan":  np.array([0.1,  0.8,  0.3, -0.2,  0.9,  0.4, -0.1,  0.3]),
    "ikan":   np.array([0.4, -0.1,  0.7,  0.5, -0.3,  0.8,  0.2,  0.6]),
}

embeddings = np.array([vocab[t] for t in tokens])  # shape: (3, 8)

print("\n[1] EMBEDDING")
for i, t in enumerate(tokens):
    print(f"   '{t}' → {np.round(embeddings[i], 2)}")

# ─────────────────────────────────────────────────────────
#  STEP 2 — POSITIONAL ENCODING
#  Tambahkan info posisi agar model tahu urutan token
# ─────────────────────────────────────────────────────────
def positional_encoding(n_pos, d_model):
    PE = np.zeros((n_pos, d_model))
    for pos in range(n_pos):
        for i in range(0, d_model, 2):
            PE[pos, i]   = np.sin(pos / (10000 ** (i / d_model)))
            if i + 1 < d_model:
                PE[pos, i+1] = np.cos(pos / (10000 ** (i / d_model)))
    return PE

PE = positional_encoding(n_tokens, d_model)
X  = embeddings + PE   # embedding + posisi

print("\n[2] POSITIONAL ENCODING")
for i, t in enumerate(tokens):
    print(f"   pos[{i}] '{t}' → {np.round(X[i], 2)}")

# ─────────────────────────────────────────────────────────
#  STEP 3 — SELF-ATTENTION  (Q, K, V)
#  Query : "aku sedang mencari apa?"
#  Key   : "aku punya info apa?"
#  Value : "ini info yang aku bawa"
#
#  Score = softmax(Q · Kᵀ / √d_k) · V
# ─────────────────────────────────────────────────────────
d_k = 4   # dimensi Q, K, V (setengah d_model)

# Bobot W (biasanya di-train; kita pakai random untuk demo)
W_Q = np.random.randn(d_model, d_k) * 0.3
W_K = np.random.randn(d_model, d_k) * 0.3
W_V = np.random.randn(d_model, d_k) * 0.3

Q = X @ W_Q   # (3, 4)
K = X @ W_K   # (3, 4)
V = X @ W_V   # (3, 4)

# Attention scores
scores_raw = Q @ K.T / np.sqrt(d_k)   # (3, 3)

def softmax(x):
    e = np.exp(x - x.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)

attention_weights = softmax(scores_raw)   # (3, 3)
output_attention  = attention_weights @ V  # (3, 4)

print("\n[3] SELF-ATTENTION WEIGHTS")
print("   Seberapa besar setiap token 'memperhatikan' token lain:")
print("   " + "        ".join(tokens))
for i, t in enumerate(tokens):
    row = [f"{w:.3f}" for w in attention_weights[i]]
    print(f"   {t:<8} → {row}")

# ─────────────────────────────────────────────────────────
#  STEP 4 — FEED FORWARD (sederhana)
#  Linear layer kecil setelah attention
# ─────────────────────────────────────────────────────────
def relu(x):
    return np.maximum(0, x)

W1 = np.random.randn(d_k, d_k * 2) * 0.3
W2 = np.random.randn(d_k * 2, d_k) * 0.3
ff_out = relu(output_attention @ W1) @ W2   # (3, 4)

# ─────────────────────────────────────────────────────────
#  STEP 5 — OUTPUT / PREDIKSI TOKEN BERIKUTNYA
#  Proyeksikan vektor output ke vocab
# ─────────────────────────────────────────────────────────
vocab_list = ["kucing", "makan", "ikan", "tidur", "lari", "berlompat"]
W_out = np.random.randn(d_k, len(vocab_list)) * 0.4

# Gunakan vektor output token terakhir untuk prediksi
last_hidden = ff_out[-1]                 # vektor token "ikan"
logits = last_hidden @ W_out             # skor mentah untuk setiap vocab
probs  = softmax(logits.reshape(1, -1)).flatten()

print("\n[4] PREDIKSI TOKEN BERIKUTNYA (setelah 'ikan')")
for w, p in sorted(zip(vocab_list, probs), key=lambda x: -x[1]):
    bar = "█" * int(p * 30)
    print(f"   {w:<12} {p:.4f}  {bar}")

# ─────────────────────────────────────────────────────────
#  VISUALISASI LENGKAP — 5 panel
# ─────────────────────────────────────────────────────────
fig = plt.figure(figsize=(18, 13), facecolor=BG)
fig.suptitle(
    "SIMULASI CARA KERJA TRANSFORMER (LLM) — Bahan Belajar",
    fontsize=16, fontweight="bold", color=WHITE, y=0.98
)

gs = gridspec.GridSpec(
    3, 3,
    figure=fig,
    hspace=0.52, wspace=0.38,
    top=0.93, bottom=0.05, left=0.05, right=0.97
)

# ────────────────────────────────────────────────
#  Panel 0 — Alur Transformer (diagram teks)
# ────────────────────────────────────────────────
ax0 = fig.add_subplot(gs[0, :])
ax0.set_xlim(0, 10)
ax0.set_ylim(0, 1)
ax0.axis("off")

steps = [
    ("INPUT\nKalimat", 0.7,  LGRAY),
    ("TOKENISASI\n+ Embedding", 2.1,  BLUE),
    ("POSITIONAL\nEncoding", 3.7,  TEAL),
    ("SELF-\nATTENTION", 5.3,  AMBER),
    ("FEED\nFORWARD", 6.9,  CORAL),
    ("OUTPUT\nPrediksi", 8.5,  PURPLE),
]

for label, x, color in steps:
    ax0.add_patch(FancyBboxPatch(
        (x - 0.55, 0.18), 1.1, 0.65,
        boxstyle="round,pad=0.05",
        facecolor=color + "33", edgecolor=color, linewidth=1.5
    ))
    ax0.text(x, 0.51, label, ha="center", va="center",
             fontsize=8.5, color=color, fontweight="bold", linespacing=1.4)

for i in range(len(steps) - 1):
    x1 = steps[i][1] + 0.57
    x2 = steps[i+1][1] - 0.57
    ax0.annotate("", xy=(x2, 0.51), xytext=(x1, 0.51),
        arrowprops=dict(arrowstyle="->", color=LGRAY, lw=1.5))

ax0.text(5, 0.05, f"Input: \"{sentence}\"   |   Token: {tokens}   |   Dimensi embedding: {d_model}",
         ha="center", fontsize=9, color=LGRAY)

# ────────────────────────────────────────────────
#  Panel 1 — Embedding Matrix
# ────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[1, 0])
im = ax1.imshow(embeddings, aspect="auto", cmap="Blues", vmin=-1, vmax=1)
ax1.set_xticks(range(d_model))
ax1.set_xticklabels([f"d{i}" for i in range(d_model)], fontsize=7)
ax1.set_yticks(range(n_tokens))
ax1.set_yticklabels(tokens, fontsize=9, color=BLUE)
ax1.set_title("① Token Embedding", color=BLUE, fontsize=10, pad=8)
for i in range(n_tokens):
    for j in range(d_model):
        ax1.text(j, i, f"{embeddings[i,j]:.1f}", ha="center", va="center",
                 fontsize=6.5, color=WHITE)
plt.colorbar(im, ax=ax1, fraction=0.04)

# ────────────────────────────────────────────────
#  Panel 2 — Positional Encoding
# ────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1, 1])
PE_full = positional_encoding(20, d_model)  # tampilkan 20 posisi
im2 = ax2.imshow(PE_full, aspect="auto", cmap="RdBu", vmin=-1, vmax=1)
ax2.set_xticks(range(d_model))
ax2.set_xticklabels([f"d{i}" for i in range(d_model)], fontsize=7)
ax2.set_yticks(range(0, 20, 4))
ax2.set_yticklabels([f"pos {i}" for i in range(0, 20, 4)], fontsize=7)
ax2.set_title("② Positional Encoding\n(pola sin/cos per posisi)", color=TEAL, fontsize=10, pad=8)

# Tandai posisi token kita
for i in range(n_tokens):
    ax2.axhline(y=i, color=AMBER, linewidth=1.5, alpha=0.6, linestyle="--")
    ax2.text(d_model + 0.1, i, tokens[i], fontsize=7, color=AMBER, va="center")

plt.colorbar(im2, ax=ax2, fraction=0.04)

# ────────────────────────────────────────────────
#  Panel 3 — Attention Weight Heatmap
# ────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[1, 2])
im3 = ax3.imshow(attention_weights, cmap="YlOrRd", vmin=0, vmax=1)
ax3.set_xticks(range(n_tokens))
ax3.set_yticks(range(n_tokens))
ax3.set_xticklabels(tokens, fontsize=9)
ax3.set_yticklabels(tokens, fontsize=9)
ax3.set_xlabel("Key (info dari token ini)", fontsize=8)
ax3.set_ylabel("Query (token yang bertanya)", fontsize=8)
ax3.set_title("③ Self-Attention Weights\n(seberapa kuat token saling berhubungan)", color=AMBER, fontsize=10, pad=8)

for i in range(n_tokens):
    for j in range(n_tokens):
        w = attention_weights[i, j]
        ax3.text(j, i, f"{w:.2f}", ha="center", va="center",
                 fontsize=10, color="black" if w > 0.5 else WHITE, fontweight="bold")

plt.colorbar(im3, ax=ax3, fraction=0.04)

# ────────────────────────────────────────────────
#  Panel 4 — Q, K, V vectors scatter
# ────────────────────────────────────────────────
ax4 = fig.add_subplot(gs[2, 0])
colors_token = [BLUE, TEAL, CORAL]
markers_qkv  = {"Q": "o", "K": "s", "V": "^"}
data_qkv     = {"Q": Q, "K": K, "V": V}

for label, mat in data_qkv.items():
    for i, t in enumerate(tokens):
        ax4.scatter(mat[i, 0], mat[i, 1],
                    s=90, marker=markers_qkv[label],
                    color=colors_token[i],
                    alpha=0.85,
                    label=f"{label}:{t}" if label == "Q" else None)
        if label == "Q":
            ax4.annotate(t, (mat[i, 0], mat[i, 1]),
                         textcoords="offset points", xytext=(5, 4),
                         fontsize=7.5, color=colors_token[i])

# Legend tipe marker
for lbl, mk in markers_qkv.items():
    ax4.scatter([], [], marker=mk, color=LGRAY, label=f"● = {lbl}", s=60)

ax4.legend(fontsize=7, labelcolor=LGRAY, facecolor=PANEL, edgecolor=GRAY,
           loc="upper right")
ax4.set_title("④ Vektor Q, K, V (dim 0 vs 1)\nTiap token punya Query, Key, Value berbeda",
              color=PURPLE, fontsize=10, pad=8)
ax4.grid(True)

# ────────────────────────────────────────────────
#  Panel 5 — Perubahan embedding setelah attention
# ────────────────────────────────────────────────
ax5 = fig.add_subplot(gs[2, 1])
bar_w = 0.25
x_idx = np.arange(d_k)

for i, (t, color) in enumerate(zip(tokens, colors_token)):
    ax5.bar(x_idx + i * bar_w, output_attention[i],
            width=bar_w, color=color, alpha=0.8, label=t)

ax5.set_xticks(x_idx + bar_w)
ax5.set_xticklabels([f"dim {i}" for i in range(d_k)], fontsize=8)
ax5.set_title("⑤ Output Attention per Token\n(representasi baru setelah 'memperhatikan' konteks)",
              color=CORAL, fontsize=10, pad=8)
ax5.legend(fontsize=8, labelcolor=LGRAY, facecolor=PANEL, edgecolor=GRAY)
ax5.axhline(0, color=GRAY, linewidth=0.8)
ax5.grid(True, axis="y")

# ────────────────────────────────────────────────
#  Panel 6 — Probabilitas prediksi token berikutnya
# ────────────────────────────────────────────────
ax6 = fig.add_subplot(gs[2, 2])
sorted_idx   = np.argsort(probs)[::-1]
sorted_vocab = [vocab_list[i] for i in sorted_idx]
sorted_probs = probs[sorted_idx]
bar_colors   = [PURPLE if i == 0 else BLUE + "99" for i in range(len(sorted_vocab))]

bars = ax6.barh(sorted_vocab, sorted_probs, color=bar_colors, edgecolor="none")
ax6.set_xlim(0, sorted_probs[0] * 1.35)

for bar, prob in zip(bars, sorted_probs):
    ax6.text(prob + 0.003, bar.get_y() + bar.get_height() / 2,
             f"{prob:.3f}", va="center", fontsize=8.5,
             color=PURPLE if prob == sorted_probs[0] else LGRAY,
             fontweight="bold" if prob == sorted_probs[0] else "normal")

ax6.set_title(f"⑥ Prediksi Token Berikutnya\n(setelah '{tokens[-1]}', kemungkinan token selanjutnya)",
              color=PURPLE, fontsize=10, pad=8)
ax6.invert_yaxis()
ax6.grid(True, axis="x")
ax6.set_xlabel("Probabilitas", fontsize=8)

# ── watermark ────────────────────────────────────
fig.text(0.99, 0.01, "Transformer Simulation — Educational",
         ha="right", va="bottom", fontsize=7, color=GRAY)

plt.savefig("/mnt/user-data/outputs/transformer_simulation.png",
            dpi=150, bbox_inches="tight", facecolor=BG)
print("\n✅ Visualisasi disimpan: transformer_simulation.png")
plt.show()
