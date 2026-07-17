import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px  # Library baru untuk membuat grafik
from database import buat_tabel  # Fungsi pembuat tabel

# --- 0. PASTIKAN DATABASE & TABEL SUDAH ADA ---
# Wajib dipanggil setiap kali app start, karena Streamlit Cloud
# menggunakan filesystem sementara (ephemeral) yang bisa reset.
buat_tabel()

# --- 1. FUNGSI PENDUKUNG DATABASE ---
def ambil_data(query):
    conn = sqlite3.connect("penjualan.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def jalankan_query(query, params=()):
    conn = sqlite3.connect("penjualan.db")
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    conn.close()

# --- 2. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(page_title="Sistem Penjualan & HPP", layout="wide")
st.title("📊 Dashboard Penjualan, HPP & Bahan Baku")

# --- 3. NAVIGASI SIDEBAR ---
st.sidebar.header("Navigasi")
menu = st.sidebar.radio(
    "Pilih Halaman:", 
    ["Dashboard & Untung Rugi", "Input Stok Barang", "Input Transaksi Baru", "Input Pengeluaran Bahan", "🗑️ Hapus Data"]
)

# ==================== HALAMAN 1: DASHBOARD & UNTUNG RUGI ====================
if menu == "Dashboard & Untung Rugi":
    st.header("📈 Performa Bisnis & Analisis HPP")
    
    # Mengambil semua data dari 3 tabel
    df_stok = ambil_data("SELECT * FROM stok")
    df_penjualan = ambil_data("""
        SELECT p.*, s.harga_beli, s.harga_jual 
        FROM penjualan p 
        JOIN stok s ON p.nama_barang = s.nama_barang
    """)
    df_pengeluaran = ambil_data("SELECT * FROM pengeluaran_bahan")
    
    # Perhitungan Dasar Omzet & HPP Produk Terjual
    if not df_penjualan.empty:
        total_omzet = df_penjualan['total_harga'].sum()
        hpp_produk = (df_penjualan['harga_beli'] * df_penjualan['jumlah']).sum()
    else:
        total_omzet = 0.0
        hpp_produk = 0.0
        
    # Perhitungan Pengeluaran Bahan Baku / Pendukung
    total_biaya_bahan = df_pengeluaran['biaya'].sum() if not df_pengeluaran.empty else 0.0
    
    # Akumulasi Total HPP & Keuntungan Bersih
    # Akumulasi Total HPP & Keuntungan Bersih
    total_hpp_akumulasi = hpp_produk + total_biaya_bahan
    total_untung_bersih = total_omzet - total_hpp_akumulasi

    # --- PENAMBAHAN FITUR SALDO KAS ---
    SALDO_AWAL = 358800.0
    # Saldo Kas = Saldo Awal + Total Uang Masuk (Omzet) - Total Uang Keluar (Biaya Bahan)
    saldo_kas_aktif = SALDO_AWAL + total_omzet - total_biaya_bahan

    # Menampilkan Kartu Informasi Bisnis (Metrics menjadi 4 kolom)
    col1, col2, col3, col4 = st.columns(4)
    
    # Kolom 1: Informasi Saldo Kas saat ini
    col1.metric(
        label="💰 Saldo Kas Sekarang", 
        value=f"Rp {saldo_kas_aktif:,.0f}",
        help="Rumus: Saldo Awal (Rp 358.800) + Total Omzet - Total Pengeluaran Bahan"
    )
    
    col2.metric("Total Omzet (Penjualan)", f"Rp {total_omzet:,.0f}")
    col3.metric("Total HPP (Modal + Bahan)", f"Rp {total_hpp_akumulasi:,.0f}", help="Harga Beli Produk Terjual + Pengeluaran Bahan Baku")
    
    status_toko = "Untung Bersih" if total_untung_bersih >= 0 else "Rugi Bersih"
    col4.metric(
        status_toko, f"Rp {total_untung_bersih:,.0f}", 
        delta="Positif" if total_untung_bersih >= 0 else "Negatif",
        delta_color="normal" if total_untung_bersih >= 0 else "inverse"
    )
    
    st.markdown("---")
    
    # ==================== SEKSI GRAFIK PENJUALAN ====================
    st.subheader("📈 Visualisasi Grafik Penjualan")
    
    if not df_penjualan.empty:
        # Prapemrosesan data tanggal agar dikelompokkan per hari saja
        df_penjualan['tanggal_bersih'] = pd.to_datetime(df_penjualan['tanggal']).dt.date
        
        # 1. Menyiapkan Data Tren Penjualan Harian
        df_tren = df_penjualan.groupby('tanggal_bersih')['total_harga'].sum().reset_index()
        df_tren.columns = ['Tanggal', 'Total Penjualan (Rp)']
        
        # 2. Menyiapkan Data Penjualan Per Produk
        df_produk = df_penjualan.groupby('nama_barang')['total_harga'].sum().reset_index()
        df_produk.columns = ['Nama Produk', 'Total Omzet (Rp)']
        df_produk = df_produk.sort_values(by='Total Omzet (Rp)', ascending=False)

        # Menampilkan Grafik Berdampingan (Kiri dan Kanan)
        grafik_col1, grafik_col2 = st.columns(2)
        
        with grafik_col1:
            st.markdown("**Tren Omzet Penjualan Harian**")
            fig_tren = px.line(
                df_tren, 
                x='Tanggal', 
                y='Total Penjualan (Rp)', 
                markers=True,
                template="plotly_white"
            )
            fig_tren.update_traces(line_color='#0083B0', line_width=3)
            st.plotly_chart(fig_tren, use_container_width=True)
            
        with grafik_col2:
            st.markdown("**Kontribusi Omzet per Produk**")
            fig_produk = px.bar(
                df_produk, 
                x='Nama Produk', 
                y='Total Omzet (Rp)',
                text_auto=',.0f',
                template="plotly_white"
            )
            fig_produk.update_traces(marker_color='#00B4DB')
            st.plotly_chart(fig_produk, use_container_width=True)
            
    else:
        st.info("💡 Grafik penjualan akan muncul secara otomatis setelah Anda menginput data transaksi pembelian pertama.")
        
    st.markdown("---")
    
    # Layout Grid untuk tabel-tabel data
    tab1, tab2, tab3 = st.tabs(["📦 Status Stok", "🛍️ Transaksi", "📝 Log Pengeluaran Bahan"])
    
    with tab1:
        st.dataframe(df_stok, use_container_width=True, hide_index=True)
    with tab2:
        if not df_penjualan.empty:
            st.dataframe(df_penjualan[['id', 'nama_pembeli', 'nama_barang', 'jumlah', 'total_harga', 'tanggal']], use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data penjualan.")
    with tab3:
        if not df_pengeluaran.empty:
            st.dataframe(df_pengeluaran, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada pengeluaran bahan baku yang dicatat.")

# ==================== HALAMAN 2: INPUT STOK BARANG ====================
elif menu == "Input Stok Barang":
    st.header("➕ Tambah Stok Barang Baru")
    with st.form("form_tambah_stok", clear_on_submit=True):
        nama_barang = st.text_input("Nama Barang / Produk")
        harga_modal = st.number_input("Harga Beli Semula (Modal Per Unit)", min_value=0.0, step=1000.0)
        harga_jual = st.number_input("Harga Jual Ke Konsumen", min_value=0.0, step=1000.0)
        jumlah_stok = st.number_input("Jumlah Stok Masuk Gudang", min_value=1, step=1)
        
        if st.form_submit_button("Simpan Data ke Gudang"):
            if nama_barang.strip():
                try:
                    jalankan_query(
                        "INSERT INTO stok (nama_barang, harga_beli, harga_jual, stok_awal, stok_sekarang) VALUES (?, ?, ?, ?, ?)",
                        (nama_barang, harga_modal, harga_jual, jumlah_stok, jumlah_stok)
                    )
                    st.success(f"Sukses mendaftarkan '{nama_barang}'!")
                except sqlite3.IntegrityError:
                    st.error("Nama barang sudah ada!")
            else:
                st.warning("Nama barang wajib diisi!")

# ==================== HALAMAN 3: INPUT TRANSAKSI BARU ====================
elif menu == "Input Transaksi Baru":
    st.header("🛒 Catat Pembelian Baru")
    df_pilihan = ambil_data("SELECT nama_barang, harga_jual, stok_sekarang FROM stok WHERE stok_sekarang > 0")
    
    if df_pilihan.empty:
        st.warning("Gudang kosong. Silakan isi stok barang terlebih dahulu.")
    else:
        list_nama_barang = df_pilihan['nama_barang'].tolist()
        with st.form("form_transaksi", clear_on_submit=True):
            nama_pembeli = st.text_input("Nama Lengkap Pembeli")
            barang_dipilih = st.selectbox("Pilih Produk", list_nama_barang)
            
            detail_barang = df_pilihan[df_pilihan['nama_barang'] == barang_dipilih].iloc[0]
            st.caption(f"Stok Tersedia: {detail_barang['stok_sekarang']} unit | Harga Satuan: Rp {detail_barang['harga_jual']:,.0f}")
            
            jumlah_beli = st.number_input("Jumlah Beli", min_value=1, max_value=int(detail_barang['stok_sekarang']), step=1)
            
            if st.form_submit_button("Proses Nota Transaksi"):
                if nama_pembeli.strip():
                    total_tagihan = jumlah_beli * detail_barang['harga_jual']
                    stok_akhir = int(detail_barang['stok_sekarang']) - jumlah_beli
                    
                    jalankan_query("UPDATE stok SET stok_sekarang = ? WHERE nama_barang = ?", (stok_akhir, barang_dipilih))
                    jalankan_query("INSERT INTO penjualan (nama_pembeli, nama_barang, jumlah, total_harga) VALUES (?, ?, ?, ?)",
                                   (nama_pembeli, barang_dipilih, jumlah_beli, total_tagihan))
                    st.success(f"Transaksi atas nama '{nama_pembeli}' sukses diproses!")
                else:
                    st.warning("Nama pembeli wajib diisi!")

# ==================== HALAMAN 4: INPUT PENGELUARAN BAHAN ====================
elif menu == "Input Pengeluaran Bahan":
    st.header("🛠️ Catat Pengeluaran Bahan Baku / Pendukung")
    with st.form("form_pengeluaran_bahan", clear_on_submit=True):
        nama_bahan = st.text_input("Nama Bahan Baku / Kebutuhan Operasional", placeholder="Contoh: Kardus Packing, Bahan Mentah Kain")
        biaya_dikeluarkan = st.number_input("Total Biaya Pengeluaran (Rp)", min_value=0.0, step=5000.0)
        keterangan = st.text_area("Keterangan Tambahan")
        
        if st.form_submit_button("Catat Pengeluaran"):
            if nama_bahan.strip() and biaya_dikeluarkan > 0:
                jalankan_query(
                    "INSERT INTO pengeluaran_bahan (nama_bahan, biaya, keterangan) VALUES (?, ?, ?)",
                    (nama_bahan, biaya_dikeluarkan, keterangan)
                )
                st.success(f"Berhasil mencatat pengeluaran untuk '{nama_bahan}'!")
            else:
                st.warning("Nama bahan wajib diisi dan biaya harus lebih dari Rp 0!")

# ==================== HALAMAN 5: HAPUS DATA (PER ITEM) ====================
elif menu == "🗑️ Hapus Data":
    st.header("🗑️ Hapus Data Per Item")
    st.caption("Pilih tabel, lalu pilih baris yang ingin dihapus. Tindakan ini tidak bisa dibatalkan.")

    tab_stok, tab_transaksi, tab_pengeluaran = st.tabs(
        ["📦 Hapus Stok", "🛍️ Hapus Transaksi", "📝 Hapus Pengeluaran Bahan"]
    )

    # --- HAPUS DATA STOK ---
    with tab_stok:
        df_stok_hapus = ambil_data("SELECT * FROM stok")
        if df_stok_hapus.empty:
            st.info("Belum ada data stok.")
        else:
            st.dataframe(df_stok_hapus, use_container_width=True, hide_index=True)
            opsi_stok = {
                f"#{row.id} — {row.nama_barang} (sisa {row.stok_sekarang})": row.id
                for row in df_stok_hapus.itertuples()
            }
            pilihan_stok = st.selectbox("Pilih barang yang mau dihapus", list(opsi_stok.keys()), key="pilih_stok")
            id_stok = opsi_stok[pilihan_stok]

            st.warning("⚠️ Menghapus barang di sini juga akan menghapus semua riwayat transaksi barang tersebut (agar data tetap konsisten).")
            konfirmasi_stok = st.checkbox("Saya yakin ingin menghapus barang ini", key="konfirmasi_stok")
            if st.button("Hapus Barang Ini", key="btn_hapus_stok", disabled=not konfirmasi_stok):
                nama_barang_dihapus = df_stok_hapus.loc[df_stok_hapus['id'] == id_stok, 'nama_barang'].values[0]
                jalankan_query("DELETE FROM penjualan WHERE nama_barang = ?", (nama_barang_dihapus,))
                jalankan_query("DELETE FROM stok WHERE id = ?", (id_stok,))
                st.success(f"Barang '{nama_barang_dihapus}' beserta riwayat transaksinya berhasil dihapus.")
                st.rerun()

    # --- HAPUS DATA TRANSAKSI ---
    with tab_transaksi:
        df_transaksi_hapus = ambil_data("SELECT * FROM penjualan ORDER BY id DESC")
        if df_transaksi_hapus.empty:
            st.info("Belum ada data transaksi.")
        else:
            st.dataframe(
                df_transaksi_hapus[['id', 'nama_pembeli', 'nama_barang', 'jumlah', 'total_harga', 'tanggal']],
                use_container_width=True, hide_index=True
            )
            opsi_transaksi = {
                f"#{row.id} — {row.nama_pembeli} | {row.nama_barang} x{row.jumlah} | Rp {row.total_harga:,.0f} | {row.tanggal}": row.id
                for row in df_transaksi_hapus.itertuples()
            }
            pilihan_transaksi = st.selectbox("Pilih transaksi yang mau dihapus", list(opsi_transaksi.keys()), key="pilih_transaksi")
            id_transaksi = opsi_transaksi[pilihan_transaksi]

            kembalikan_stok = st.checkbox("Kembalikan jumlah barang ini ke stok gudang", value=True, key="kembalikan_stok")
            konfirmasi_transaksi = st.checkbox("Saya yakin ingin menghapus transaksi ini", key="konfirmasi_transaksi")
            if st.button("Hapus Transaksi Ini", key="btn_hapus_transaksi", disabled=not konfirmasi_transaksi):
                baris = df_transaksi_hapus.loc[df_transaksi_hapus['id'] == id_transaksi].iloc[0]
                if kembalikan_stok:
                    jalankan_query(
                        "UPDATE stok SET stok_sekarang = stok_sekarang + ? WHERE nama_barang = ?",
                        (int(baris['jumlah']), baris['nama_barang'])
                    )
                jalankan_query("DELETE FROM penjualan WHERE id = ?", (id_transaksi,))
                st.success(f"Transaksi #{id_transaksi} berhasil dihapus.")
                st.rerun()

    # --- HAPUS DATA PENGELUARAN BAHAN ---
    with tab_pengeluaran:
        df_pengeluaran_hapus = ambil_data("SELECT * FROM pengeluaran_bahan ORDER BY id DESC")
        if df_pengeluaran_hapus.empty:
            st.info("Belum ada data pengeluaran bahan.")
        else:
            st.dataframe(df_pengeluaran_hapus, use_container_width=True, hide_index=True)
            opsi_pengeluaran = {
                f"#{row.id} — {row.nama_bahan} | Rp {row.biaya:,.0f} | {row.tanggal}": row.id
                for row in df_pengeluaran_hapus.itertuples()
            }
            pilihan_pengeluaran = st.selectbox("Pilih pengeluaran yang mau dihapus", list(opsi_pengeluaran.keys()), key="pilih_pengeluaran")
            id_pengeluaran = opsi_pengeluaran[pilihan_pengeluaran]

            konfirmasi_pengeluaran = st.checkbox("Saya yakin ingin menghapus pengeluaran ini", key="konfirmasi_pengeluaran")
            if st.button("Hapus Pengeluaran Ini", key="btn_hapus_pengeluaran", disabled=not konfirmasi_pengeluaran):
                jalankan_query("DELETE FROM pengeluaran_bahan WHERE id = ?", (id_pengeluaran,))
                st.success(f"Pengeluaran #{id_pengeluaran} berhasil dihapus.")
                st.rerun()
