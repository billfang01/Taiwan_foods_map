# -*- coding: utf-8 -*-
"""
Created on Sun Aug 25 07:20:55 2024

@author: python2
"""

#2024美食地圖 資料來源500碗&2024必比登

import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium

@st.cache_data
def load_geojson_data():
    geojson_file_path = 'taiwan_counties.geojson'
    gdf = gpd.read_file(geojson_file_path)
    return gdf

@st.cache_data
def load_csv_data(csv_file_path, encoding='big5'):
    df = pd.read_csv(csv_file_path, encoding=encoding)
    if '碗　　數' in df.columns and '2024必比登' in csv_file_path:
        df.rename(columns={'碗　　數': '星　　評'}, inplace=True)
    return df

def plot_map(gdf, df, dataset_choice, selected_county, selected_districts):
    if dataset_choice == "500碗":
        rating_column = '碗　　數'
    else:
        rating_column = '星　　評'

    required_columns = ["經度", "緯度", "名稱", "地　　址", "得獎菜色", rating_column, "縣市", "鄉鎮區"]
    if not all(col in df.columns for col in required_columns):
        st.error(f"CSV 文件缺少必需的欄位：{', '.join(required_columns)}")
        return

    df = df.dropna(subset=["經度", "緯度"])
    geometry = [Point(xy) for xy in zip(df["經度"], df["緯度"])]
    df_geo = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

    # 
    filtered_df_geo = df_geo[(df_geo["縣市"] == selected_county) & (df_geo["鄉鎮區"].isin(selected_districts))]

    filtered_gdf = gdf[gdf["COUNTYNAME"] == selected_county]

    if 'index_right' in filtered_df_geo.columns:
        filtered_df_geo = filtered_df_geo.drop(columns='index_right')
    if 'index_right' in filtered_gdf.columns:
        filtered_gdf = filtered_gdf.drop(columns='index_right')

    # 
    points_within_county = gpd.sjoin(filtered_df_geo, filtered_gdf, how="inner", predicate="within")

    center_lat = filtered_gdf.geometry.centroid.y.mean()
    center_lon = filtered_gdf.geometry.centroid.x.mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    folium.GeoJson(filtered_gdf).add_to(m)

    for _, row in points_within_county.iterrows():
        rating_display = row[rating_column]
        if dataset_choice == "2024必比登":
            rating_display = f"⭐ {row[rating_column]}"

        tooltip_text = f"{row['名稱']}\n{row['地　　址']}\n{row['得獎菜色']}\n{rating_column}: {rating_display}"
        popup_text = (
            f"<div style='width: 300px; height: 80px;'>"
            f"<span><strong>名稱:</strong> {row['名稱']}</span><br>"
            f"<span><strong>地　　址:</strong> {row['地　　址']}</span><br>"
            f"<span><strong>得獎菜色:</strong> {row['得獎菜色']}</span><br>"
            f"<span><strong>{rating_column}:</strong> {rating_display}</span>"
            f"</div>"
        )

        folium.Marker(
            location=[row["緯度"], row["經度"]],
            tooltip=tooltip_text,
            popup=popup_text
        ).add_to(m)

    st_folium(m, width=1000, height=900)

def main():
    st.title("行政區域美食地圖標記")

    dataset_choice = st.sidebar.selectbox("選擇美食名單", ["500碗", "2024必比登"])

    if dataset_choice == "500碗":
        df = load_csv_data('new500data.csv', encoding='utf-8')
    else:
        df = load_csv_data('2024必比登.csv', encoding='big5')

    gdf = load_geojson_data()

    
    counties = df['縣市'].unique()
    selected_county = st.sidebar.selectbox("選擇一個縣市", counties)

    
    districts = df[df['縣市'] == selected_county]['鄉鎮區'].unique()
    selected_districts = st.sidebar.multiselect("選擇行政區域", districts, default=districts)

    plot_map(gdf, df, dataset_choice, selected_county, selected_districts)

if __name__ == "__main__":
    main()

