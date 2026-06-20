"""
Demonstrasi eksplisit komponen-komponen utama:
LANGCHAIN:
- ChatPromptTemplate
- ConversationBufferMemory
- Tool definition (@tool decorator)
- LLM binding dengan tools

LANGGRAPH:
- StateGraph
- Node functions
- Conditional edges (routing)
- Graph compilation & visualization
"""

import os
from typing import TypedDict, Annotated, List
import operator

# LangChain 
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory

# LangGraph 
from langgraph.graph import StateGraph, END

print("=" * 60)
print("DEMONSTRASI LANGCHAIN & LANGGRAPH")
print("Asisten Pribadi Berbasis Perintah Bahasa Indonesia")
print("=" * 60)


# BAGIAN 1: LANGCHAIN — Prompt Templates

print("\n📦 LANGCHAIN — ChatPromptTemplate")
print("-" * 40)

# Template prompt multi-turn dengan history
prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Anda adalah ARIA, asisten pribadi cerdas berbahasa Indonesia.
Selalu respond dalam Bahasa Indonesia yang baik dan benar.
Tanggal hari ini: {tanggal}"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{perintah}"),
])

print("✅ ChatPromptTemplate berhasil dibuat:")
print("   • System message dengan variable {tanggal}")
print("   • Placeholder untuk chat_history (multi-turn)")
print("   • Human message dengan {perintah}")

# format prompt
from datetime import datetime
contoh_prompt = prompt_template.format_messages(
    tanggal=datetime.now().strftime("%d %B %Y"),
    chat_history=[
        HumanMessage(content="Halo!"),
        AIMessage(content="Halo! Ada yang bisa saya bantu?")
    ],
    perintah="Siapa kamu?"
)
print(f"\n   Preview prompt ({len(contoh_prompt)} pesan):")
for msg in contoh_prompt:
    tipe = type(msg).__name__
    isi = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
    print(f"   [{tipe}]: {isi}")


# BAGIAN 2: LANGCHAIN — Memory

print("\n\n📦 LANGCHAIN — ChatMessageHistory (Conversation Memory)")
print("-" * 40)

# LangChain versi terbaru menggunakan ChatMessageHistory
memory = ChatMessageHistory()

# Simulasi percakapan yang tersimpan di memory
memory.add_user_message("Nama saya Budi")
memory.add_ai_message("Senang berkenalan dengan Anda, Budi!")
memory.add_user_message("Apa yang bisa kamu bantu?")
memory.add_ai_message("Saya bisa membantu menghitung, mengingat jadwal, dan menjawab pertanyaan!")

riwayat = memory.messages
print(f"✅ Memory berhasil dibuat dan diisi:")
print(f"   • Jumlah pesan tersimpan: {len(riwayat)}")
print(f"   • Tipe memory: ChatMessageHistory (langchain_community)")
print(f"   • Prefix human: 'Pengguna' | Prefix AI: 'ARIA'")
print(f"   • Pesan pertama: '{riwayat[0].content}'")


# BAGIAN 3: LANGCHAIN — Tools

print("\n\n📦 LANGCHAIN — Tool Definitions")
print("-" * 40)

@tool
def hitung_bmi(berat_kg: float, tinggi_cm: float) -> str:
    """
    Menghitung BMI (Body Mass Index) berdasarkan berat dan tinggi badan.
    Parameter:
        berat_kg: Berat badan dalam kilogram
        tinggi_cm: Tinggi badan dalam sentimeter
    """
    tinggi_m = tinggi_cm / 100
    bmi = berat_kg / (tinggi_m ** 2)
    
    if bmi < 18.5:
        kategori = "Kurus (Underweight)"
    elif bmi < 25:
        kategori = "Normal (Healthy Weight)"
    elif bmi < 30:
        kategori = "Gemuk (Overweight)"
    else:
        kategori = "Obesitas (Obese)"
    
    return f"BMI Anda: {bmi:.1f} — Kategori: {kategori}"


@tool
def konversi_suhu(nilai: float, dari: str, ke: str) -> str:
    """
    Mengkonversi suhu antar satuan (Celsius, Fahrenheit, Kelvin).
    Parameter:
        nilai: nilai suhu yang akan dikonversi
        dari: satuan asal (C/F/K)
        ke: satuan tujuan (C/F/K)
    """
    dari = dari.upper()
    ke = ke.upper()
    
    # Konversi ke Celsius dulu
    if dari == "C":
        celsius = nilai
    elif dari == "F":
        celsius = (nilai - 32) * 5/9
    elif dari == "K":
        celsius = nilai - 273.15
    else:
        return f"Satuan '{dari}' tidak dikenal."
    
    # Konversi dari Celsius ke tujuan
    if ke == "C":
        hasil = celsius
    elif ke == "F":
        hasil = celsius * 9/5 + 32
    elif ke == "K":
        hasil = celsius + 273.15
    else:
        return f"Satuan '{ke}' tidak dikenal."
    
    return f"{nilai}°{dari} = {hasil:.2f}°{ke}"


semua_tools = [hitung_bmi, konversi_suhu]
print("✅ Tools berhasil didefinisikan:")
for t in semua_tools:
    print(f"   • @tool '{t.name}': {t.description[:60]}...")

# Demo penggunaan tool langsung
print("\n   Demo langsung (tanpa LLM):")
print(f"   {hitung_bmi.invoke({'berat_kg': 70, 'tinggi_cm': 170})}")
print(f"   {konversi_suhu.invoke({'nilai': 100, 'dari': 'C', 'ke': 'F'})}")

# Binding tools ke LLM
if os.environ.get("OPENAI_API_KEY"):
    llm = ChatGroq(model="llama-3.3-70b-versatile")
    llm_dengan_tools = llm.bind_tools(semua_tools)
    print(f"\n   ✅ Tools berhasil di-bind ke LLM ({len(semua_tools)} tools)")
else:
    print("\n   ⚠️  OPENAI_API_KEY tidak ditemukan — binding tools dilewati")


# BAGIAN 4: LANGGRAPH — StateGraph

print("\n\n📦 LANGGRAPH — StateGraph dengan Conditional Edges")
print("-" * 40)


class StateDemo(TypedDict):
    """State sederhana untuk demonstrasi."""
    pesan: str
    kategori: str
    hasil: str


def node_analisis(state: StateDemo) -> StateDemo:
    """Node 1: Menganalisis dan mengkategorikan pesan."""
    pesan = state["pesan"].lower()
    
    if any(kata in pesan for kata in ["hitung", "berapa", "+", "-", "*", "/"]):
        kategori = "matematika"
    elif any(kata in pesan for kata in ["waktu", "jam", "tanggal", "hari"]):
        kategori = "waktu"
    elif any(kata in pesan for kata in ["halo", "hai", "apa kabar", "selamat"]):
        kategori = "sapaan"
    else:
        kategori = "umum"
    
    print(f"   [Node: analisis] Kategori terdeteksi: '{kategori}'")
    return {**state, "kategori": kategori}


def node_jawab_matematika(state: StateDemo) -> StateDemo:
    """Node 2a: Menangani pertanyaan matematika."""
    print(f"   [Node: jawab_matematika] Memproses: '{state['pesan']}'")
    return {**state, "hasil": "✅ [Matematika] Saya akan menghitung itu untuk Anda!"}


def node_jawab_waktu(state: StateDemo) -> StateDemo:
    """Node 2b: Menangani pertanyaan waktu."""
    print(f"   [Node: jawab_waktu] Memproses: '{state['pesan']}'")
    waktu = datetime.now().strftime("%H:%M")
    return {**state, "hasil": f"✅ [Waktu] Sekarang pukul {waktu} WIB"}


def node_jawab_sapaan(state: StateDemo) -> StateDemo:
    """Node 2c: Menangani sapaan."""
    print(f"   [Node: jawab_sapaan] Memproses: '{state['pesan']}'")
    return {**state, "hasil": "✅ [Sapaan] Halo! Senang bertemu dengan Anda! 😊"}


def node_jawab_umum(state: StateDemo) -> StateDemo:
    """Node 2d: Menangani pertanyaan umum."""
    print(f"   [Node: jawab_umum] Memproses: '{state['pesan']}'")
    return {**state, "hasil": "✅ [Umum] Saya akan mencoba membantu Anda!"}


def routing_kategori(state: StateDemo) -> str:
    """Fungsi routing berdasarkan kategori."""
    return state["kategori"]


# Membangun graph
graph_demo = StateGraph(StateDemo)

# Tambah nodes
graph_demo.add_node("analisis", node_analisis)
graph_demo.add_node("matematika", node_jawab_matematika)
graph_demo.add_node("waktu", node_jawab_waktu)
graph_demo.add_node("sapaan", node_jawab_sapaan)
graph_demo.add_node("umum", node_jawab_umum)

# Entry point
graph_demo.set_entry_point("analisis")

# Conditional edges (routing)
graph_demo.add_conditional_edges(
    "analisis",
    routing_kategori,
    {
        "matematika": "matematika",
        "waktu": "waktu",
        "sapaan": "sapaan",
        "umum": "umum"
    }
)

# End edges
for node in ["matematika", "waktu", "sapaan", "umum"]:
    graph_demo.add_edge(node, END)

# Kompilasi
graph_terkompilasi = graph_demo.compile()

print("✅ StateGraph berhasil dibangun & dikompilasi:")
print("   Struktur graph:")
print("   START → [analisis]")
print("              ├─ matematika → [node_jawab_matematika] → END")
print("              ├─ waktu      → [node_jawab_waktu]      → END")
print("              ├─ sapaan     → [node_jawab_sapaan]     → END")
print("              └─ umum       → [node_jawab_umum]       → END")

# Demo menjalankan graph
print("\n   Demo menjalankan graph:")
test_inputs = [
    "Hitung 10 + 5",
    "Jam berapa sekarang?",
    "Halo, apa kabar?",
    "Ceritakan tentang Indonesia"
]

for pesan in test_inputs:
    print(f"\n   Input: '{pesan}'")
    hasil = graph_terkompilasi.invoke({
        "pesan": pesan,
        "kategori": "",
        "hasil": ""
    })
    print(f"   Output: {hasil['hasil']}")


print("\n" + "=" * 60)
print("✅ Demonstrasi LangChain & LangGraph selesai!")
print("=" * 60)
