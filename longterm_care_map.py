import folium
from longterm_care_db import LongTermCareDB
from flask import render_template_string


def create_longtermcare_map(city, dist):
    ltc_list_dict = []
    ltc_datas = LongTermCareDB().find_by_city_dist(city, dist)

    for data in ltc_datas:
        ltc_list_dict.append({
            'id': data['id'],
            'name': data['name'],
            'address': data['address'],
            'lat': data['latitude'],
            'lng': data['longitude'],
        })

    # 空值視為 flase
    if not ltc_list_dict:
        return None
    
    center_lat = sum([item['lat'] for item in ltc_list_dict]) / len(ltc_list_dict)
    center_lng = sum([item['lng'] for item in ltc_list_dict]) / len(ltc_list_dict)
    m = folium.Map(location=[center_lat,center_lng], zoom_start=14)

    for item in ltc_list_dict:
        folium.Marker(
            location=[item['lat'],item['lng']],
            popup= folium.Popup(
                f"機構名稱: {item['name']}<br>地址: {item['address']}",
                max_width=300)
        ).add_to(m)
    
    return render_template_string(m.get_root().render())
    
    # 轉成 html 語法, 會產生<iframe> 標籤, heroku 有時候沒辦法載入
    # return m._repr_html_()

if __name__ == '__main__':
    city = '高雄市'
    dist = '前金區'
    
    datas = create_longtermcare_map(city, dist)

