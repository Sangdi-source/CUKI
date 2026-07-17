import sqlite3

def koneksi_db():
    return sqlite3.connect("penjualan.db")

def buat_tabel():
    conn = koneksi_db()
    cursor = conn.cursor()
    
    # 1. Tabel Stok Barang
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_barang TEXT UNIQUE,
            harga_beli REAL,
            harga_jual REAL,
            stok_awal INTEGER,
            stok_sekarang INTEGER
        )
    ''')
    
    # 2. Tabel Transaksi Penjualan
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS penjualan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_pembeli TEXT,
            nama_barang TEXT,
            jumlah INTEGER,
            total_harga REAL,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(nama_barang) REFERENCES stok(nama_barang)
        )
    ''')

    # 3. TABEL BARU: Pengeluaran Bahan Baku / Pendukung
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pengeluaran_bahan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_bahan TEXT,
            biaya REAL,
            keterangan TEXT,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database berhasil diperbarui dengan tabel Pengeluaran!")

if __name__ == "__main__":
    buat_tabel()