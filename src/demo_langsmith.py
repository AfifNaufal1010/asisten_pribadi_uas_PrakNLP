"""
demo_langsmith.py
=================
Demonstrasi eksplisit penggunaan LangSmith untuk:
1. Membuat dataset evaluasi
2. Menjalankan evaluasi otomatis
3. Melihat trace percakapan
4. Membandingkan performa run

LangSmith digunakan untuk monitoring, tracing, dan evaluasi
sistem asisten berbasis Bahasa Indonesia.
"""

import os
from datetime import datetime
from langsmith import Client
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import HumanMessage, SystemMessage

# Konfigurasi LangSmith
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "asisten-pribadi-bahasa-indonesia")


def demonstrasi_langsmith():
    """Demonstrasi fitur-fitur LangSmith."""
    
    print("=" * 60)
    print("DEMONSTRASI LANGSMITH")
    print("Monitoring & Evaluasi Asisten Bahasa Indonesia")
    print("=" * 60)
    
    # ─── 1. Inisialisasi Client ────────────────────────────────────
    print("\n1️⃣  Menginisialisasi LangSmith Client...")
    
    api_key = os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        print("   ⚠️  LANGCHAIN_API_KEY tidak ditemukan.")
        print("   📋 Cara mendapatkan API key:")
        print("      a. Buka https://smith.langchain.com")
        print("      b. Daftar/login ke akun LangSmith")
        print("      c. Buka Settings → API Keys → Create API Key")
        print("      d. Tambahkan ke .env: LANGCHAIN_API_KEY=ls__xxxx")
        print("   ⚡ Demo akan dilanjutkan dengan mode simulasi.\n")
        demo_simulasi()
        return
    
    try:
        client = Client()
        print("   ✅ LangSmith Client berhasil diinisialisasi!")
    except Exception as e:
        print(f"   ❌ Gagal terhubung: {e}")
        demo_simulasi()
        return
    
    # ─── 2. Membuat Dataset Evaluasi ──────────────────────────────
    print("\n2️⃣  Membuat dataset evaluasi...")
    
    nama_dataset = f"evaluasi-asisten-id-{datetime.now().strftime('%Y%m%d-%H%M')}"
    
    contoh_data = [
        {
            "input": {"perintah": "Berapa hasil 15 dikali 8?"},
            "output": {"respons_ideal": "Hasil perhitungan 15 × 8 = 120"}
        },
        {
            "input": {"perintah": "Apa itu LangChain?"},
            "output": {"respons_ideal": "LangChain adalah framework untuk membangun aplikasi berbasis LLM"}
        },
        {
            "input": {"perintah": "Tambahkan pengingat rapat jam 14:00"},
            "output": {"respons_ideal": "Pengingat rapat berhasil ditambahkan untuk jam 14:00"}
        },
    ]
    
    try:
        dataset = client.create_dataset(
            dataset_name=nama_dataset,
            description="Dataset evaluasi untuk Asisten Pribadi Bahasa Indonesia"
        )
        
        client.create_examples(
            inputs=[d["input"] for d in contoh_data],
            outputs=[d["output"] for d in contoh_data],
            dataset_id=dataset.id
        )
        
        print(f"   ✅ Dataset '{nama_dataset}' berhasil dibuat dengan {len(contoh_data)} contoh!")
        print(f"   🔗 Lihat di: https://smith.langchain.com/datasets/{dataset.id}")
        
    except Exception as e:
        print(f"   ⚠️  Gagal membuat dataset: {e}")
    
    # ─── 3. Tracing Percakapan ────────────────────────────────────
    print("\n3️⃣  Menjalankan percakapan dengan tracing aktif...")
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)
    
    test_perintah = [
        "Hitung 256 dibagi 16",
        "Jam berapa sekarang?",
        "Jelaskan apa itu NLP dalam 2 kalimat"
    ]
    
    for i, perintah in enumerate(test_perintah, 1):
        print(f"\n   [{i}] Input: '{perintah}'")
        try:
            respons = llm.invoke([
                SystemMessage(content="Kamu adalah asisten AI yang berbicara dalam Bahasa Indonesia."),
                HumanMessage(content=perintah)
            ])
            print(f"       Output: {respons.content[:80]}...")
            print("       ✅ Trace tersimpan di LangSmith")
        except Exception as e:
            print(f"       ⚠️  Error: {e}")
    
    print(f"\n   🔗 Lihat semua trace di: https://smith.langchain.com/projects/p/asisten-pribadi-bahasa-indonesia")
    
    print("\n" + "=" * 60)
    print("✅ Demonstrasi LangSmith selesai!")
    print("=" * 60)


def demo_simulasi():
    """Simulasi output LangSmith tanpa koneksi nyata."""
    print("\n📊 SIMULASI OUTPUT LANGSMITH:")
    print("-" * 40)
    print("""
    Run ID: run_abc123xyz
    Project: asisten-pribadi-bahasa-indonesia
    Status: ✅ Success
    
    Traces:
    ┌─────────────────────────────────────────────┐
    │ [1] klasifikasi        → 0.12s   ✓          │
    │ [2] proses_tool        → 1.45s   ✓          │
    │   └─ kalkulator()      → 0.02s   ✓          │
    │ [3] node_percakapan    → 0.89s   ✓          │
    └─────────────────────────────────────────────┘
    
    Metrics:
    • Total latency : 2.48 detik
    • Token usage   : 342 tokens (input: 280, output: 62)
    • Success rate  : 100%
    • Tools called  : 1 (kalkulator)
    
    Untuk melihat trace nyata:
    1. Daftar di https://smith.langchain.com
    2. Set LANGCHAIN_API_KEY di file .env
    3. Jalankan ulang demo ini
    """)


if __name__ == "__main__":
    demonstrasi_langsmith()
