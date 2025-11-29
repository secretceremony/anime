import streamlit as st
import pandas as pd
import requests
import altair as alt

# Konfigurasi halaman Streamlit
st.set_page_config(
    page_title="Visualisasi Top Manga (Praktikum ABD)",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Judul dan Deskripsi
st.title("📚 Visualisasi Data Top 20 Manga (Jikan API)")
st.markdown("---")

# Poin +: Gambar dan Penjelasan
# Menggunakan gambar dari URL yang Anda berikan, dengan lebar dibatasi
st.image("https://dukaan.b-cdn.net/1000x1000/webp/media/2d463869-39a1-434e-bfe5-0d0fde49bd7a.jpeg", caption="Ilustrasi Top Anime/Manga", width=1000)
st.subheader("Tugas Praktikum Analisis & Big Data Interaktif")
st.markdown("""
Aplikasi ini menampilkan visualisasi interaktif dari data 20 manga teratas (top 20) yang diambil secara real-time dari **Jikan API** (sebuah API tidak resmi untuk MyAnimeList).
Gunakan *dropdown* di bawah untuk memilih **5 jenis chart** yang berbeda: Bar, Line/Area, Pie, Total Chapter, dan Scatter Plot. Data yang digunakan lebih dari 10 titik data.
""")
st.markdown("---")

# Fungsi untuk mengambil data dari Jikan API (menggunakan cache untuk performa)
@st.cache_data(ttl=3600) # Data di-cache selama 1 jam
def fetch_top_manga_data():
    """Mengambil 20 data Manga teratas dari Jikan API."""
    try:
        # Mengambil 20 data teratas
        url = "https://api.jikan.moe/v4/top/manga"
        response = requests.get(url)
        response.raise_for_status() # Cek jika ada error HTTP
        data = response.json()
        
        # Ekstrak data yang relevan ke dalam list
        manga_list = []
        # Batasi hingga 20 data
        for item in data.get('data', [])[:20]: 
            manga_list.append({
                'rank': item.get('rank'),
                'title': item.get('title'),
                'score': item.get('score'),
                'members': item.get('members'),
                'type': item.get('type'),
                'chapters': item.get('chapters') or 0,
            })
            
        df = pd.DataFrame(manga_list)
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Gagal mengambil data dari API: {e}. Pastikan koneksi internet Anda aktif.")
        return pd.DataFrame()

# ----------------------------------------------------
# FUNGSI VISUALISASI MENGGUNAKAN ALTAIR (5 JENIS)
# ----------------------------------------------------

# 1. BAR CHART
def bar_chart_viz(df):
    """Visualisasi Bar Chart: Peringkat vs Skor"""
    st.subheader("📊 1. Bar Chart: Skor Manga Berdasarkan Peringkat")
    st.write("Visualisasi ini membandingkan skor (rating) dari 20 manga teratas. Manga dengan peringkat yang lebih tinggi (nilai 'Rank' yang lebih kecil) cenderung memiliki skor yang lebih tinggi.")
    
    chart = alt.Chart(df).mark_bar(opacity=0.8, color='#1E88E5').encode(
        x=alt.X('rank:O', axis=alt.Axis(title='Peringkat (Rank)')), 
        y=alt.Y('score:Q', axis=alt.Axis(title='Skor (Rating)'), scale=alt.Scale(domain=[df['score'].min() - 0.1, df['score'].max() + 0.1])),
        tooltip=['title', 'score', 'rank']
    ).properties(
        title="Skor Rata-Rata Manga"
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

# 2. LINE/AREA CHART
def line_area_chart_viz(df):
    """Visualisasi Line/Area Chart: Angka Member Berdasarkan Peringkat"""
    st.subheader("📈 2. Line/Area Chart: Angka Pengguna (Members) Kumulatif per Peringkat")
    st.write("Visualisasi ini menunjukkan tren jumlah anggota (members) yang melacak atau membaca manga, diurutkan berdasarkan peringkat. Area Chart memperlihatkan akumulasi popularitas.")
    
    df_sorted = df.sort_values(by='rank', ascending=True)
    df_sorted['cumulative_members'] = df_sorted['members'].cumsum()
    
    # Area Chart
    area = alt.Chart(df_sorted).mark_area(opacity=0.7, color='#FFC107').encode(
        x=alt.X('rank:O', axis=alt.Axis(title='Peringkat (Rank)')),
        y=alt.Y('cumulative_members:Q', axis=alt.Axis(title='Total Members Kumulatif'), stack=None),
        tooltip=['title', 'rank', 'members', 'cumulative_members']
    )
    
    # Line Chart
    line = alt.Chart(df_sorted).mark_line(color='#D81B60').encode(
        x='rank:O',
        y='members:Q',
        tooltip=['title', 'rank', 'members']
    )
    
    chart = (area + line).properties(
        title="Tren Jumlah Anggota Kumulatif"
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

# 3. PIE CHART
def pie_chart_viz(df):
    """Visualisasi Pie Chart: Distribusi Tipe Manga"""
    st.subheader("🥧 3. Pie Chart: Distribusi Tipe Manga")
    st.write("Visualisasi ini menunjukkan proporsi (persentase) dari berbagai tipe format manga (misalnya, Manga, One-Shot, Doujinshi) dalam data top 20.")
    
    # Agregasi data berdasarkan Tipe
    type_counts = df['type'].value_counts().reset_index()
    type_counts.columns = ['type', 'count']
    
    base = alt.Chart(type_counts).encode(
        theta=alt.Theta("count", stack=True)
    )

    pie = base.mark_arc(outerRadius=120).encode(
        color=alt.Color("type:N", title="Tipe Manga"),
        order=alt.Order("count", sort="descending"),
        tooltip=["type", "count", alt.Tooltip("count", format=".1%")]
    )

    text = base.mark_text(radius=140).encode(
        text=alt.Text("count:Q"),
        order=alt.Order("count", sort="descending"),
        color=alt.value("black")
    )
    
    # Gabungkan Pie Chart dan Teks. configure_scale yang error telah dihapus.
    chart = (pie + text).properties(
        title="Proporsi Tipe Manga Top 20"
    )
    
    st.altair_chart(chart, use_container_width=True)


# 4. STACKED BAR CHART (Total Chapters)
def stacked_bar_viz(df):
    """Visualisasi Stacked Bar Chart: Total Chapter per Tipe Manga"""
    st.subheader("📚 4. Stacked Bar Chart: Total Chapter per Tipe Manga")
    st.write("Visualisasi ini menunjukkan total jumlah chapter yang disumbangkan oleh setiap Tipe Manga (Manga, Manhwa, dll.) dari 20 manga teratas.")
    
    # Grouping by type and summing chapters
    df_agg = df.groupby('type')['chapters'].sum().reset_index()
    df_agg.columns = ['type', 'total_chapters']

    chart = alt.Chart(df).mark_bar().encode(
        # X: Total Chapter (dijumlahkan per tipe)
        x=alt.X('sum(chapters):Q', axis=alt.Axis(title='Total Chapter')),
        # Y: Tipe Manga
        y=alt.Y('type:N', axis=alt.Axis(title='Tipe Manga')),
        # Warna berdasarkan Tipe
        color=alt.Color('type:N', legend=alt.Legend(title="Tipe")),
        tooltip=['type', alt.Tooltip('sum(chapters)', title='Total Chapter')]
    ).properties(
        title="Total Chapter Berdasarkan Tipe Manga"
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


# 5. SCATTER PLOT
def scatter_plot_viz(df):
    """Visualisasi Scatter Plot: Korelasi Score vs Members"""
    st.subheader("⚫ 5. Scatter Plot: Korelasi Skor (Score) vs Jumlah Anggota (Members)")
    st.write("Visualisasi ini mengeksplorasi hubungan antara skor rating manga dan jumlah anggota yang melacaknya. Semakin besar ukuran titik, semakin tinggi jumlah chapternya.")
    
    chart = alt.Chart(df).mark_circle().encode(
        x=alt.X('members:Q', axis=alt.Axis(title='Jumlah Anggota (Members)')),
        y=alt.Y('score:Q', axis=alt.Axis(title='Skor (Rating)')),
        # Ukuran lingkaran berdasarkan jumlah chapters
        size=alt.Size('chapters:Q', title='Jumlah Chapter', scale=alt.Scale(range=[50, 500])),
        # Warna berdasarkan Tipe
        color=alt.Color('type:N', legend=alt.Legend(title="Tipe")),
        tooltip=['title', 'score', 'members', 'chapters']
    ).properties(
        title="Korelasi Skor dan Anggota"
    ).interactive()

    st.altair_chart(chart, use_container_width=True)


# ----------------------------------------------------
# LOGIKA UTAMA APLIKASI
# ----------------------------------------------------

# Ambil data
manga_df = fetch_top_manga_data()

if not manga_df.empty:
    
    # Dropdown interaktif (sekarang 5 pilihan)
    chart_choice = st.selectbox(
        "Pilih Jenis Visualisasi (Total 5 Tipe):",
        (
            "1. Bar Chart (Skor vs Rank)",
            "2. Line/Area Chart (Members Kumulatif)",
            "3. Pie Chart (Distribusi Tipe)",
            "4. Stacked Bar (Total Chapters)",
            "5. Scatter Plot (Skor vs Members)",
        )
    )
    
    # Tampilkan chart berdasarkan pilihan dropdown
    if chart_choice == "1. Bar Chart (Skor vs Rank)":
        bar_chart_viz(manga_df)
    
    elif chart_choice == "2. Line/Area Chart (Members Kumulatif)":
        line_area_chart_viz(manga_df)

    elif chart_choice == "3. Pie Chart (Distribusi Tipe)":
        pie_chart_viz(manga_df)
    
    elif chart_choice == "4. Stacked Bar (Total Chapters)":
        stacked_bar_viz(manga_df)

    elif chart_choice == "5. Scatter Plot (Skor vs Members)":
        scatter_plot_viz(manga_df)

    # Tampilkan 10 Data Awal
    st.markdown("---")
    st.subheader("Data Mentah (10 Entri Pertama)")
    st.dataframe(manga_df.head(10)) 

else:
    st.warning("Dataframe kosong. Silakan cek status koneksi atau API.")