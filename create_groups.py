import json
from pprint import pprint
from itertools import groupby


def read_file(file_name):
    with open(file_name) as f:
        file = f.read()
        file = json.loads(file)
        f.close()
    return file


def write_file(file_name, data):
    with open(file_name, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.close()
    return


# order = [{'name': 'Шампанское Moet & Chandon, Brut "Imperial", gift box',
#          'Артикул': 'в2752',
#          'image': 'https://s.wine.style/images_gen/275/2752/0_0_prod_desktop.jpg',
#          'link': 'https://winestyle.ru/products/Moet-Chandon-Brut-Imperial-in-gift-box.html',
#          'Объем': 0.75,
#          'quantity': 2,
#          'section': 'Шампанское и игристое вино',
#          'product_id': '8361938',
#          'spider': 'Winestyle',
#          'price': 3986},
#          {'name': 'Виски "Macallan" Double Cask 12 Years Old, gift box, 0.7 л',
#          'Артикул': 'в71280',
#          'image': 'https://s.wine.style/images_gen/712/71280/0_0_prod_desktop.jpg',
#          'link': 'https://winestyle.ru/products/Macallan-Double-Cask-12-Years-Old-gift-box.html',
#          'Объем': 0.7,
#          'quantity': 3,
#          'section': 'Виски',
#          'product_id': '6290152',
#          'spider': 'Winestyle',
#          'price': 4576},
#          {'name': 'Виски "Jameson", 0.7 л',
#          'Артикул': 'в14220',
#          'image': 'https://s.wine.style/images_gen/142/14220/0_0_prod_desktop.jpg',
#          'link': 'https://winestyle.ru/products/Jameson-700.html',
#          'Объем': 0.7,
#          'quantity': 1,
#          'section': 'Виски',
#          'product_id': '8388019',
#          'spider': 'Winestyle',
#          'price': 1412}
# ]

# Нужно обговорить в каком формате я буду получать заказ
def take_other_groups(order):

    # order = read_file('order.json')
    order_num = order[0]['order_num']
    order = order[0][order[0]['active']]

    champagne = read_file('champagne.json')
    whiskey = read_file('whiskey.json')
    vodka = read_file('vodka.json')
    cognac = read_file('cognac.json')

    cats = {'Виски': whiskey, 'Шампанское и игристое вино': champagne, 'Водка': vodka, 'Коньяк': cognac}
    other_groups = []
    sections = set([i['section'] for i in order])

    for item in order:
        # Исключаем поставщика, которому принадлежит ордер, но в случае смешанного заказа, нужно будет не исключать и взять всех
        others = [i for i in cats[item['section']] if 'product_id' in i.keys() and (i['product_id'] == item['product_id']) and (i['spider'] != item['spider']) and (i['features']['Объем'] == item['Объем'])]
        for k in others:
            other_groups.append(k)

    keyfunc = lambda x: x['spider']
    grouped_shops = list(set([i[0] for i in groupby(other_groups, key=keyfunc)]))

    new_groups = {}
    items = []

    for i in grouped_shops:
        found = [k for k in other_groups if k['spider'] == i]
        sect = len(set([r['section'] for r in found]))
        if sect == len(sections):
            new_groups[i] = found

    updated_groups = {}
    for i in new_groups:
        updated_groups[i] = []
        for j in new_groups[i]:
            new_dict = {}
            new_dict['price'] = j['price']
            new_dict['name'] = j['name']
            new_dict['image'] = j['image']
            new_dict['link'] = j['link']
            new_dict['product_id'] = j['product_id']
            new_dict['Объем'] = j['features']['Объем']
            if 'Артикул' in j.keys():
                new_dict['Артикул'] = j['article']
            quantity = [k['quantity'] for k in order if k['product_id'] == j['product_id']][0]
            new_dict['quantity'] = quantity
            section = [k['section'] for k in order if k['product_id'] == j['product_id']][0]
            new_dict['section'] = section
            new_dict['spider'] = j['spider']
            updated_groups[i].append(new_dict)

    for i in updated_groups:
        products = [k['product_id'] for k in updated_groups[i]]
        product_id_list = []
        unique_products = []
        if len(products) > len(set(products)):
            for j in set(products):
                min_price = min([n['price'] for n in updated_groups[i] if n['product_id'] == j])
                unique_products.append([r for r in updated_groups[i] if r['price'] == min_price and r['product_id'] == j][0])
            updated_groups[i] = unique_products
        else:
            unique_products.append({'order': updated_groups[i]})

    # min_price = 0
    # for i in updated_groups:
    #     min_ = sum([k['price'] for k in updated_groups[i]])
    #     min_ = float(min_) if '.' in str(min_) else int(min_)
    #     if min_price < min_:
    #         min_price = min_
    #
    # for i in updated_groups:
    #     if sum([k['price'] for k in updated_groups[i]]) == min_price:
    #         order = [k for k in updated_groups[i]]


    # updated_groups['order_num'] = '1872658'

    # write_file('order.json', order)

    # pprint(updated_groups)

    if len(set([i['spider'] for i in order])) == 1:
        updated_groups[order[0]['spider']] = {'order': order, 'confirmed': False}
        updated_groups['active'] = order[0]['spider']
        # updated_groups['confirmed'] = dict()
        # for i in updated_groups.keys():
        #     updated_groups['confirmed'][i] = False
        # print(order[0]['spider'])
        # updated_groups['confirmed'].pop('confirmed')

    # pprint([i for i in updated_groups.keys()])

    updated_groups['order_num'] = order_num
    for i in updated_groups:
        if type(updated_groups[i]) != dict and i in grouped_shops:
            # print(i, updated_groups[i])
            updated_groups[i] = {'order': updated_groups[i], 'confirmed': False}

    return updated_groups


# [
#   {
#     "price": 1932,
#     "name": "Виски ирландский «Jameson», 0.7 л",
#     "image": "https://static.winestreet.ru/off-line/goods_file/31984/file_L.jpg",
#     "link": "https://winestreet.ru/wiskey/jameson/5011007003005.html",
#     "product_id": "8388019",
#     "Объем": 0.7,
#     "quantity": 1,
#     "section": "Виски",
#     "spider": "Winestreet"
#   },
#   {
#     "price": 4637,
#     "name": "Виски шотландский «Macallan Double Cask 12 Years Old» в подарочной упаковке",
#     "image": "https://static.winestreet.ru/off-line/goods_file/42654/file_L.jpg",
#     "link": "https://winestreet.ru/wiskey/macallan/goods_72814-macallan-double-cask-12-years-old-v-podarochno-upakovke.html",
#     "product_id": "6290152",
#     "Объем": 0.7,
#     "quantity": 3,
#     "section": "Виски",
#     "spider": "Winestreet"
#   },
#   {
#     "price": 6121,
#     "name": "Шампанское белое брют «Moet & Chandon Imperial», 0.75 л",
#     "image": "https://static.winestreet.ru/off-line/goods_file/5721/file_L.jpg",
#     "link": "https://winestreet.ru/champagne-and-sparkling-wines/moet-chandon/asto2263.html",
#     "product_id": "8361938",
#     "Объем": 0.75,
#     "quantity": 2,
#     "section": "Шампанское и игристое вино",
#     "spider": "Winestreet"
#   }
# ]
