"""
generate_diagram.py
====================
Membuat diagram arsitektur sistem sebagai file gambar
untuk dimasukkan ke README sebagai screenshot.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

fig, ax = plt.subplots(1, 1, figsize=(14, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis('off')
fig.patch.set_facecolor('#0F1117')
ax.set_facecolor('#0F1117')

# ─── Warna ────────────────────────────────────────────────────────
C_LC   = '#1E6FFF'   # LangChain — biru
C_LG   = '#7C3AED'   # LangGraph — ungu
C_LS   = '#059669'   # LangSmith — hijau
C_BG   = '#1A1D2E'   # background node
C_TEXT = '#E2E8F0'
C_MUTED= '#94A3B8'
C_GOLD = '#F59E0B'

def box(ax, x, y, w, h, color, label, sublabel=None, radius=0.3):
    fancy = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle=f"round,pad=0.05,rounding_size={radius}",
                           facecolor=C_BG, edgecolor=color, linewidth=2.5, zorder=3)
    ax.add_patch(fancy)
    ay = y + (0.18 if sublabel else 0)
    ax.text(x, ay, label, ha='center', va='center', fontsize=10,
            color=C_TEXT, fontweight='bold', zorder=4)
    if sublabel:
        ax.text(x, y - 0.28, sublabel, ha='center', va='center', fontsize=7.5,
                color=color, zorder=4)

def arrow(ax, x1, y1, x2, y2, color='#475569'):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=2.0),
                zorder=2)

def badge(ax, x, y, w, h, color, text):
    r = FancyBboxPatch((x - w/2, y - h/2), w, h,
                       boxstyle="round,pad=0.03,rounding_size=0.2",
                       facecolor=color, edgecolor='none', alpha=0.2, zorder=3)
    ax.add_patch(r)
    ax.text(x, y, text, ha='center', va='center', fontsize=8,
            color=color, fontweight='bold', zorder=4)

# ══════════════════════════════════════════════════════════════════
# JUDUL
# ══════════════════════════════════════════════════════════════════
ax.text(7, 9.5, 'ARIA — Asisten Pribadi Berbasis Perintah Bahasa Indonesia',
        ha='center', va='center', fontsize=13, color=C_TEXT,
        fontweight='bold')
ax.text(7, 9.0, 'Arsitektur Sistem: LangChain  ×  LangGraph  ×  LangSmith',
        ha='center', va='center', fontsize=9, color=C_MUTED)

# ══════════════════════════════════════════════════════════════════
# LAYER 1 — INPUT
# ══════════════════════════════════════════════════════════════════
ax.text(1.2, 8.2, 'INPUT', ha='center', fontsize=8, color=C_MUTED, style='italic')
box(ax, 7, 8.1, 4.5, 0.75, C_GOLD, '👤 Pengguna', 'Perintah Bahasa Indonesia')

# ══════════════════════════════════════════════════════════════════
# LAYER 2 — LANGCHAIN
# ══════════════════════════════════════════════════════════════════
lc_y = 6.8
ax.text(1.2, lc_y + 0.7, 'LANGCHAIN', ha='center', fontsize=8, color=C_LC, fontweight='bold')

# Background LangChain area
lc_bg = FancyBboxPatch((1.5, lc_y - 0.55), 11, 1.1,
                        boxstyle="round,pad=0.1,rounding_size=0.3",
                        facecolor='#1E6FFF', edgecolor=C_LC, linewidth=1.5,
                        alpha=0.07, zorder=1)
ax.add_patch(lc_bg)

box(ax, 3.2, lc_y, 2.8, 0.75, C_LC, '📝 ChatPromptTemplate', 'System + History + Human')
box(ax, 7.0, lc_y, 2.8, 0.75, C_LC, '🧠 ChatOpenAI (LLM)', 'gpt-4o-mini')
box(ax, 10.8, lc_y, 2.8, 0.75, C_LC, '💾 ConversationMemory', 'Buffer Riwayat Chat')

arrow(ax, 7, 7.73, 7, 7.18, C_GOLD)   # user → langchain
arrow(ax, 4.6, lc_y, 5.6, lc_y, C_LC)
arrow(ax, 8.4, lc_y, 9.4, lc_y, C_LC)

# ══════════════════════════════════════════════════════════════════
# LAYER 3 — LANGGRAPH
# ══════════════════════════════════════════════════════════════════
lg_y_top = 5.5
ax.text(1.2, lg_y_top + 0.2, 'LANGGRAPH', ha='center', fontsize=8, color=C_LG, fontweight='bold')

# Background LangGraph area
lg_bg = FancyBboxPatch((1.5, 2.6), 11, 2.7,
                        boxstyle="round,pad=0.1,rounding_size=0.3",
                        facecolor='#7C3AED', edgecolor=C_LG, linewidth=1.5,
                        alpha=0.07, zorder=1)
ax.add_patch(lg_bg)

# START
box(ax, 7, 5.3, 1.6, 0.55, C_LG, '▶ START', '')
arrow(ax, 7, 6.43, 7, 5.58, C_LC)

# Node klasifikasi
box(ax, 7, 4.5, 3.0, 0.7, C_LG, '🔍 node_klasifikasi', 'Routing: tool / chat / exit')
arrow(ax, 7, 5.03, 7, 4.85, C_LG)

# Routing fork
arrow(ax, 5.5, 4.5, 3.8, 3.75, C_LG)   # → tool
arrow(ax, 7.0, 4.15, 7.0, 3.75, C_LG)  # → percakapan
arrow(ax, 8.5, 4.5, 10.2, 3.75, C_LG)  # → selesai

# Tiga node akhir
box(ax, 3.5, 3.4, 3.0, 0.65, C_LC, '🔧 node_proses_tool', 'LLM + Tools')
box(ax, 7.0, 3.4, 3.0, 0.65, C_LG, '💬 node_percakapan', 'LLM biasa')
box(ax, 10.5, 3.4, 3.0, 0.65, C_MUTED, '🚪 node_selesai', 'Pesan perpisahan')

# Tools sub-nodes
box(ax, 2.2, 2.85, 1.4, 0.45, C_LC, '🔢 kalkulator', '')
box(ax, 3.5, 2.85, 1.4, 0.45, C_LC, '⏰ waktu', '')
box(ax, 4.8, 2.85, 1.4, 0.45, C_LC, '📌 pengingat', '')

for tx in [2.2, 3.5, 4.8]:
    arrow(ax, 3.5, 3.08, tx, 3.08, C_LC)

# END
box(ax, 7, 2.75, 1.6, 0.55, C_LG, '⏹ END', '')
arrow(ax, 3.5, 3.08, 7, 2.75, C_LG)
arrow(ax, 7.0, 3.08, 7, 3.03, C_LG)
arrow(ax, 10.5, 3.08, 7, 2.75, C_LG)

# ══════════════════════════════════════════════════════════════════
# LAYER 4 — LANGSMITH
# ══════════════════════════════════════════════════════════════════
ls_y = 1.7
ax.text(1.2, ls_y + 0.55, 'LANGSMITH', ha='center', fontsize=8, color=C_LS, fontweight='bold')

ls_bg = FancyBboxPatch((1.5, ls_y - 0.45), 11, 0.9,
                        boxstyle="round,pad=0.1,rounding_size=0.3",
                        facecolor='#059669', edgecolor=C_LS, linewidth=1.5,
                        alpha=0.07, zorder=1)
ax.add_patch(ls_bg)

box(ax, 3.5, ls_y, 2.8, 0.65, C_LS, '🔍 Tracing', 'Log setiap node & LLM call')
box(ax, 7.0, ls_y, 2.8, 0.65, C_LS, '📊 Monitoring', 'Latency, token, error rate')
box(ax, 10.5, ls_y, 2.8, 0.65, C_LS, '🧪 Evaluation', 'Dataset & scoring otomatis')

arrow(ax, 7, 2.48, 7, ls_y + 0.33, '#475569')  # END → LangSmith

# ══════════════════════════════════════════════════════════════════
# OUTPUT
# ══════════════════════════════════════════════════════════════════
box(ax, 7, 0.85, 4.5, 0.55, C_GOLD, '🤖 Respons ARIA (Bahasa Indonesia)', '')
arrow(ax, 7, ls_y - 0.33, 7, 1.13, C_LS)

# ══════════════════════════════════════════════════════════════════
# LEGEND
# ══════════════════════════════════════════════════════════════════
legend_items = [
    (C_LC, 'LangChain'),
    (C_LG, 'LangGraph'),
    (C_LS, 'LangSmith'),
    (C_GOLD, 'User I/O'),
]
for i, (color, label) in enumerate(legend_items):
    lx = 2.0 + i * 2.8
    badge(ax, lx, 0.25, 2.2, 0.38, color, f'■ {label}')

plt.tight_layout()
plt.savefig('/home/claude/asisten-pribadi/screenshots/arsitektur_sistem.png',
            dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print("✅ Diagram arsitektur berhasil dibuat!")
