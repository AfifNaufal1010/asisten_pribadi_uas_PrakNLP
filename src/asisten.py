"""
Asisten Pribadi Berbasis Perintah Bahasa Indonesia
===================================================
Sistem asisten cerdas yang menerima perintah dalam Bahasa Indonesia
menggunakan LangChain, LangGraph, dan LangSmith.

LLM Provider: Groq (gratis, cepat)
Model       : llama-3.3-70b-versatile

Fitur:
- Memahami perintah Bahasa Indonesia secara natural
- Multi-turn conversation memory
- Routing cerdas berdasarkan jenis perintah (LangGraph)
- Monitoring & tracing via LangSmith
- Tools: kalkulator, pengingat, waktu, informasi
"""

import os
from datetime import datetime
from typing import TypedDict, Annotated, List
import operator
from dotenv import load_dotenv

# Load .env
load_dotenv()

# ─── LangChain + Groq ─────────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

# ─── LangGraph ────────────────────────────────────────────────────────────────
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# ─── LangSmith ────────────────────────────────────────────────────────────────
from langsmith import Client as LangSmithClient

# ─── Konfigurasi LangSmith ────────────────────────────────────────────────────
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "asisten-pribadi-bahasa-indonesia")


# ══════════════════════════════════════════════════════════════════════════════
# TOOLS
# ══════════════════════════════════════════════════════════════════════════════

@tool
def kalkulator(ekspresi: str) -> str:
    """
    Menghitung ekspresi matematika yang diberikan dalam string.
    Contoh: '2 + 2', '10 * 5', '100 / 4', '2 ** 10'
    """
    try:
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in ekspresi):
            return "Error: Ekspresi tidak valid. Hanya angka dan operator matematika yang diizinkan."
        hasil = eval(ekspresi)
        return f"Hasil perhitungan '{ekspresi}' = {hasil}"
    except ZeroDivisionError:
        return "Error: Pembagian dengan nol tidak diizinkan."
    except Exception as e:
        return f"Error dalam perhitungan: {str(e)}"


@tool
def dapatkan_waktu_sekarang() -> str:
    """Mendapatkan waktu dan tanggal saat ini dalam Bahasa Indonesia."""
    now = datetime.now()
    hari   = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    bulan  = ["Januari","Februari","Maret","April","Mei","Juni",
              "Juli","Agustus","September","Oktober","November","Desember"]
    return (
        f"Sekarang adalah hari {hari[now.weekday()]}, {now.day} {bulan[now.month-1]} {now.year}, "
        f"pukul {now.strftime('%H:%M:%S')} WIB."
    )


_daftar_pengingat: List[dict] = []

@tool
def tambah_pengingat(judul: str, waktu: str) -> str:
    """
    Menambahkan pengingat baru ke daftar.
    Parameter:
      - judul: judul/isi pengingat
      - waktu: waktu pengingat (contoh: '14:00', 'besok pagi')
    """
    pengingat = {
        "id": len(_daftar_pengingat) + 1,
        "judul": judul,
        "waktu": waktu,
        "dibuat": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    _daftar_pengingat.append(pengingat)
    return f"Pengingat berhasil ditambahkan!\n  >> '{judul}' pada {waktu}"


@tool
def lihat_pengingat() -> str:
    """Menampilkan semua pengingat yang tersimpan."""
    if not _daftar_pengingat:
        return "Belum ada pengingat yang tersimpan."
    hasil = "Daftar Pengingat Anda:\n"
    for p in _daftar_pengingat:
        hasil += f"  [{p['id']}] {p['judul']} -- {p['waktu']}\n"
    return hasil.strip()


@tool
def informasi_umum(topik: str) -> str:
    """
    Memberikan informasi umum tentang topik tertentu.
    Parameter:
      - topik: topik yang ingin diketahui
    """
    return f"[INFO] Jelaskan secara lengkap dalam Bahasa Indonesia tentang topik: {topik}"


TOOLS = [
    kalkulator,
    dapatkan_waktu_sekarang,
    tambah_pengingat,
    lihat_pengingat,
    informasi_umum
]

# ══════════════════════════════════════════════════════════════════════════════
# STATE
# ══════════════════════════════════════════════════════════════════════════════

class AsistenState(TypedDict):
    messages:          Annotated[List, operator.add]
    perintah_pengguna: str
    jenis_perintah:    str
    respons_akhir:     str


# ══════════════════════════════════════════════════════════════════════════════
# LLM (GROQ)
# ══════════════════════════════════════════════════════════════════════════════

def buat_llm(temperature: float = 0.7) -> ChatGroq:
    """Inisialisasi model Groq — llama-3.1-8b-instant."""
    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=temperature,
        groq_api_key=os.environ.get("GROQ_API_KEY"),
    )


SYSTEM_PROMPT = """Anda adalah ARIA (Asisten Responsif Indonesia dengan AI), asisten pribadi
yang cerdas dan ramah. Anda berkomunikasi SELALU dalam Bahasa Indonesia yang baik dan benar.

Kemampuan Anda:
1. Kalkulator  -- menghitung ekspresi matematika
2. Waktu       -- memberitahu waktu dan tanggal sekarang
3. Pengingat   -- menambah dan melihat daftar pengingat
4. Informasi   -- menjawab pertanyaan umum
5. Percakapan  -- berbicara santai dalam Bahasa Indonesia

Panduan:
- Selalu sapa dengan hangat dan profesional
- Gunakan Bahasa Indonesia yang natural dan mudah dipahami
- Jika ada tool yang sesuai, gunakan tool tersebut
- Berikan respons yang jelas, ringkas, dan membantu
"""

KLASIFIKASI_PROMPT = """Klasifikasikan perintah pengguna berikut ke dalam salah satu kategori:
- 'tool': pengguna membutuhkan tool TEKNIS — kalkulator (hitung/berapa), waktu (jam/tanggal), atau pengingat (ingatkan/reminder/tambah pengingat)
- 'percakapan': pengguna bertanya informasi/pengetahuan (apa itu, jelaskan, ceritakan), mengobrol, atau pertanyaan umum
- 'selesai': pengguna ingin mengakhiri (keluar, exit, selesai, bye, sampai jumpa)

Contoh 'tool'      : "Berapa 10 dikali 5", "Jam berapa sekarang", "Ingatkan aku meeting jam 3", "Tampilkan pengingat"
Contoh 'percakapan': "Apa itu NLP", "Jelaskan machine learning", "Halo apa kabar", "Siapa kamu", "Ceritakan tentang AI"

Perintah: "{perintah}"

Jawab HANYA dengan satu kata: tool, percakapan, atau selesai."""


# ══════════════════════════════════════════════════════════════════════════════
# NODE-NODE LANGGRAPH
# ══════════════════════════════════════════════════════════════════════════════

def node_klasifikasi(state: AsistenState) -> AsistenState:
    """Node: mengklasifikasikan jenis perintah pengguna."""
    llm = buat_llm(temperature=0.0)
    prompt = KLASIFIKASI_PROMPT.format(perintah=state["perintah_pengguna"])
    respons = llm.invoke([HumanMessage(content=prompt)])
    jenis = respons.content.strip().lower()
    if jenis not in ["tool", "percakapan", "selesai"]:
        jenis = "percakapan"
    return {**state, "jenis_perintah": jenis}


def node_proses_tool(state: AsistenState) -> AsistenState:

    perintah = state["perintah_pengguna"].lower()

    # TOOL WAKTU
    if any(k in perintah for k in [
        "jam berapa",
        "waktu sekarang",
        "tanggal",
        "hari ini",
        "jam sekarang"
    ]):
        hasil = dapatkan_waktu_sekarang.invoke({})
        return {
            **state,
            "messages": [AIMessage(content=hasil)],
            "respons_akhir": hasil
        }

    # TOOL LIHAT PENGINGAT
    if any(k in perintah for k in [
        "lihat pengingat",
        "tampilkan pengingat",
        "daftar pengingat"
    ]):
        hasil = lihat_pengingat.invoke({})
        return {
            **state,
            "messages": [AIMessage(content=hasil)],
            "respons_akhir": hasil
        }

    # TOOL KALKULATOR
    if any(k in perintah for k in [
        "hitung",
        "berapa"
    ]):

        ekspresi = (
            perintah
            .replace("berapa", "")
            .replace("hitung", "")
            .strip()
        )

        hasil = kalkulator.invoke({"ekspresi": ekspresi})

        return {
            **state,
            "messages": [AIMessage(content=hasil)],
            "respons_akhir": hasil
        }

    # FALLBACK KE LLM
    llm = buat_llm()

    messages = [
        SystemMessage(content=SYSTEM_PROMPT)
    ] + state["messages"]

    respons = llm.invoke(messages)

    return {
        **state,
        "messages": [respons],
        "respons_akhir": respons.content
    }

def node_percakapan(state: AsistenState) -> AsistenState:
    """Node: percakapan biasa tanpa tool."""
    llm = buat_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    respons = llm.invoke(messages)
    return {**state, "messages": [respons], "respons_akhir": respons.content}


def node_selesai(state: AsistenState) -> AsistenState:
    """Node: penutup percakapan."""
    pesan = "Terima kasih telah menggunakan ARIA! Sampai jumpa lagi!"
    return {**state, "messages": [AIMessage(content=pesan)], "respons_akhir": pesan}


def routing_logic(state: AsistenState) -> str:
    jenis = state.get("jenis_perintah", "percakapan")
    if jenis == "tool":     return "proses_tool"
    elif jenis == "selesai": return "selesai"
    else:                    return "percakapan"


# ══════════════════════════════════════════════════════════════════════════════
# MEMBANGUN GRAPH
# ══════════════════════════════════════════════════════════════════════════════

def buat_graph() -> StateGraph:
    """
    Membangun dan mengkompilasi StateGraph LangGraph.
    Alur: START -> klasifikasi -> [routing] -> proses_tool / percakapan / selesai -> END
    """
    graph = StateGraph(AsistenState)

    graph.add_node("klasifikasi", node_klasifikasi)
    graph.add_node("proses_tool", node_proses_tool)
    graph.add_node("percakapan",  node_percakapan)
    graph.add_node("selesai",     node_selesai)

    graph.set_entry_point("klasifikasi")
    graph.add_conditional_edges(
        "klasifikasi",
        routing_logic,
        {"proses_tool": "proses_tool", "percakapan": "percakapan", "selesai": "selesai"}
    )

    graph.add_edge("proses_tool", END)
    graph.add_edge("percakapan",  END)
    graph.add_edge("selesai",     END)

    return graph.compile()


# ══════════════════════════════════════════════════════════════════════════════
# KELAS UTAMA
# ══════════════════════════════════════════════════════════════════════════════

class AsistenPribadi:
    """
    Kelas utama Asisten Pribadi Berbasis Perintah Bahasa Indonesia.
    - LangChain  : LLM (Groq), Prompt Templates, Tools
    - LangGraph  : StateGraph dengan routing cerdas
    - LangSmith  : Monitoring, tracing, evaluasi
    """

    def __init__(self):
        self.graph = buat_graph()
        self.riwayat_pesan: List = []
        self.langsmith_client = None
        self._inisialisasi_langsmith()
        print("=" * 60)
        print("  ARIA - Asisten Responsif Indonesia dengan AI")
        print("  Powered by: LangChain | LangGraph | LangSmith | Groq")
        print("=" * 60)

    def _inisialisasi_langsmith(self):
        try:
            if os.environ.get("LANGCHAIN_API_KEY"):
                self.langsmith_client = LangSmithClient()
                print("[LangSmith] Terhubung -- monitoring aktif")
            else:
                print("[LangSmith] LANGCHAIN_API_KEY tidak ada -- monitoring nonaktif")
        except Exception as e:
            print(f"[LangSmith] Gagal terhubung: {e}")

    def proses_perintah(self, perintah: str) -> str:
        if not perintah.strip():
            return "Maaf, perintah tidak boleh kosong. Silakan coba lagi."

        self.riwayat_pesan.append(HumanMessage(content=perintah))

        state_awal: AsistenState = {
            "messages":          self.riwayat_pesan.copy(),
            "perintah_pengguna": perintah,
            "jenis_perintah":    "",
            "respons_akhir":     ""
        }

        try:
            state_akhir = self.graph.invoke(state_awal)
            respons = state_akhir.get("respons_akhir", "Maaf, terjadi kesalahan.")
            self.riwayat_pesan.append(AIMessage(content=respons))
            if len(self.riwayat_pesan) > 20:
                self.riwayat_pesan = self.riwayat_pesan[-20:]
            return respons
        except Exception as e:
            print(f"[ERROR] {e}")
            return f"Maaf, terjadi kesalahan: {str(e)}"

    def jalankan(self):
        print("\nKetik perintah dalam Bahasa Indonesia. Ketik 'keluar' untuk berhenti.\n")
        sambutan = self.proses_perintah("Halo, perkenalkan dirimu!")
        print(f"ARIA: {sambutan}\n")

        while True:
            try:
                perintah = input("Anda: ").strip()
                if not perintah:
                    continue
                respons = self.proses_perintah(perintah)
                print(f"\nARIA: {respons}\n")
                kata_keluar = ["keluar", "exit", "selesai", "bye", "sampai jumpa"]
                if any(k in perintah.lower() for k in kata_keluar):
                    break
            except KeyboardInterrupt:
                print("\nARIA: Sampai jumpa!")
                break
            except EOFError:
                break


if __name__ == "__main__":
    asisten = AsistenPribadi()
    asisten.jalankan()
