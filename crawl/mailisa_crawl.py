import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

tat_ca_sp = []
tat_ca_sp_url = "https://mailisa.com/san-pham-mailisa"
tat_ca_sp_response = requests.get(tat_ca_sp_url)
tat_ca_sp_soup = BeautifulSoup(tat_ca_sp_response.text, "html.parser")

# Tìm tất cả các thẻ <div> có class "product_new_item" trong trang
product_new_items = tat_ca_sp_soup.find_all("div", class_="product_new_item")

# Duyệt qua từng sản phẩm
for item in tqdm(product_new_items, desc="Đang lấy thông tin sản phẩm"):
    # lấy link image sản phẩm
    image_tag = item.find("img")
    image_url = image_tag["src"]
    # lấy thẻ <a> chứa link chi tiết sản phẩm
    link_tag = item.find("a")
    # truy cập vào link chi tiết sản phẩm
    link_buy = link_tag["href"]
    sp_response = requests.get(link_buy)
    sp_soup = BeautifulSoup(sp_response.text, "html.parser")
    # lấy thẻ h1 có class là "product_title"
    title_tag = sp_soup.find("h1", class_="product_title")
    sp_name = title_tag.text.strip()
    # lấy thẻ <div> có class là "product_sku"
    product_sku_tag = sp_soup.find("div", class_="product_sku")
    sp_sku = None
    if product_sku_tag:
        # tìm thẻ <span> có class là "sku"
        sku_tag = product_sku_tag.find("span", class_="sku")
        if sku_tag:
            sp_sku = sku_tag.text.strip()
    # lấy thẻ <div> có class là "product_description"
    description_tag = sp_soup.find("div", class_="product_description")
    sp_description = description_tag.text.strip()
    # lấy thẻ <p> có class là "product_price"
    price_tag = sp_soup.find("p", class_="product_price")
    # tìm thẻ <del> trong thẻ <p> để lấy giá cũ
    old_price_tag = price_tag.find("del")
    if old_price_tag:
        sp_old_price = old_price_tag.text.strip()
    else:
        sp_old_price = None
    # lấy giá mới
    new_price_tag = price_tag.find("ins")
    sp_new_price = new_price_tag.text.strip()

    # lấy thẻ <div> có class là "product_tabs"
    product_tabs_tag = sp_soup.find("div", class_="product_tabs")
    # lấy thẻ <div> có class là "tabs_content" trong thẻ <div> này
    tabs_content_tag = product_tabs_tag.find("div", class_="tabs_content")
    # lấy thẻ <div> có class là "content_post" trong thẻ <div> này
    content_post_tag = tabs_content_tag.find("div", class_="content_post")

    if content_post_tag:
        # Chuyển nội dung HTML thành chuỗi và parse bằng BeautifulSoup
        content_post_soup = BeautifulSoup(
            content_post_tag.decode_contents(), "html.parser"
        )

        # Loại bỏ thẻ inline nhưng giữ nguyên nội dung
        for tag in content_post_soup.find_all(["b", "strong", "span"]):
            tag.unwrap()

        # Tìm thẻ <hr> cuối cùng
        last_hr = (
            content_post_soup.find_all("hr")[-1]
            if content_post_soup.find("hr")
            else None
        )

        # Nếu có <hr>, xóa toàn bộ nội dung sau nó
        if last_hr:
            for tag in last_hr.find_all_next():
                tag.decompose()  # Xóa hoàn toàn các thẻ sau <hr> cuối cùng

            last_hr.decompose()  # Xóa luôn thẻ <hr> cuối cùng nếu không muốn giữ lại

        # Lấy nội dung từ các thẻ block, mỗi thẻ xuống dòng
        blocks = [
            block.get_text(separator=" ").strip()
            for block in content_post_soup.find_all(["p", "div", "li"])
        ]

        # Kết hợp lại thành chuỗi, mỗi đoạn văn tách nhau bằng dấu xuống dòng
        sp_detail = "\n".join(blocks).strip()
    sp_name_skus = sp_name.split("-")[0].split()
    if sp_name_skus[0].strip().lower() == "bộ":
        sp_sku = sp_name_skus[1].strip()
    else:
        sp_sku = sp_name_skus[0].strip()
    sp_price_unit = sp_old_price.split()[1]
    sp_old_price = float(sp_old_price.split()[0].replace(".", "").replace(",", ""))
    sp_new_price = float(sp_new_price.split()[0].replace(".", "").replace(",", ""))
    # Lưu thông tin sản phẩm vào danh sách
    tat_ca_sp.append(
        {
            "product_name": sp_name,
            "sku_code": sp_sku,
            "brief_description": sp_description,
            "original_price": sp_old_price,
            "discounted_price": sp_new_price,
            "price_unit": sp_price_unit,
            "discount_rate": round(
                (1 - float(sp_new_price) / float(sp_old_price)) * 100, 2
            ),
            "image_url": image_url,
            "purchase link": link_buy,
            "user_manual": sp_detail,
        }
    )

# Chuyển đổi danh sách thành DataFrame
df = pd.DataFrame(tat_ca_sp)
# Xuất DataFrame ra file excel
df.to_excel("products.xlsx", index=False)
