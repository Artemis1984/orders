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


# Нужно обговорить в каком формате я буду получать заказ
def take_other_groups(order):

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
        # others = [i for i in cats[item['section']] if 'product_id' in i.keys() and (i['product_id'] == item['product_id']) and (i['spider'] != item['spider']) and (i['features']['Объем'] == item['Объем'])]
        others = [i for i in cats[item['section']] if 'product_id' in i.keys() and (i['product_id'] == item['product_id']) and (i['features']['Объем'] == item['Объем'])]
        for k in others:
            other_groups.append(k)

    keyfunc = lambda x: x['spider']
    grouped_shops = list(set([i[0] for i in groupby(other_groups, key=keyfunc)]))
    new_groups = {}

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
        unique_products = []
        if len(products) > len(set(products)):
            for j in set(products):
                min_price = min([n['price'] for n in updated_groups[i] if n['product_id'] == j])
                unique_products.append([r for r in updated_groups[i] if r['price'] == min_price and r['product_id'] == j][0])
            updated_groups[i] = unique_products
        else:
            unique_products.append({'order': updated_groups[i]})

    if len(set([i['spider'] for i in order])) == 1:
        updated_groups[order[0]['spider']] = {'order': order, 'confirmed': False}
        updated_groups['active'] = order[0]['spider']
    else:
        updated_groups['mixed'] = {'order': order, 'confirmed': False}

    updated_groups['order_num'] = order_num
    for i in updated_groups:
        if type(updated_groups[i]) != dict and i in grouped_shops:
            updated_groups[i] = {'order': updated_groups[i], 'confirmed': False}

    return updated_groups


# К такому виду нужно привести заказ для дальнейшей обработки
order = {"active": "mixed",
        "order_num": "1872658",
        "mixed": [{
            "price": 3634,
            "name": "Коньяк \"Hennessy\" V.S.O.P., with gift box, 0.7 л",
            "image": "https://s.wine.style/images_gen/225/2253/0_0_prod_desktop.jpg",
            "link": "https://winestyle.ru/products/Hennessy-VSOP-Privilege-700.html",
            "product_id": "2073930",
            "Объем": 0.7,
            "quantity": 2,
            "section": "Коньяк",
            "spider": "Winestyle"
          },
          {
            "price": 1215,
            "name": "Водка Русский Стандарт Платинум 1 л",
            "image": "https://static.decanter.ru/image/305139-vodka-russian-standard-platinum-1-l-f.jpg",
            "link": "https://decanter.ru/product/russian-standard-platinum-id1493",
            "product_id": "2080445",
            "Объем": 1,
            "quantity": 1,
            "section": "Водка",
            "spider": "Decanter"
          }]
}


# pprint(take_other_groups([order]))

# pprint()

# {'Decanter': {'confirmed': False,
#               'order': [{'image': 'https://static.decanter.ru/image/300885-kon-iak-hennessy-vsop-0-7-l-f.jpg',
#                          'link': 'https://decanter.ru/product/hennessy-vsop-privelege-id526',
#                          'name': 'Коньяк Hennessy VSOP 0.7 л в коробке',
#                          'price': 3680,
#                          'product_id': '2073930',
#                          'quantity': 2,
#                          'section': 'Коньяк',
#                          'spider': 'Decanter',
#                          'Объем': 0.7},
#                         {'image': 'https://static.decanter.ru/image/305139-vodka-russian-standard-platinum-1-l-f.jpg',
#                          'link': 'https://decanter.ru/product/russian-standard-platinum-id1493',
#                          'name': 'Водка Русский Стандарт Платинум 1 л',
#                          'price': 1215,
#                          'product_id': '2080445',
#                          'quantity': 1,
#                          'section': 'Водка',
#                          'spider': 'Decanter',
#                          'Объем': 1}]},
#  'Winestreet': {'confirmed': False,
#                 'order': [{'image': 'https://static.winestreet.ru/off-line/goods_file/125834/file_L.jpg',
#                            'link': 'https://winestreet.ru/cognac/hennessy/asto885.html',
#                            'name': 'Коньяк французский «Hennessy VSOP» в '
#                                    'подарочной упаковке, 0.7 л',
#                            'price': 6201,
#                            'product_id': '2073930',
#                            'quantity': 2,
#                            'section': 'Коньяк',
#                            'spider': 'Winestreet',
#                            'Объем': 0.7},
#                           {'image': 'https://static.winestreet.ru/off-line/goods_file/31865/file_L.jpg',
#                            'link': 'https://winestreet.ru/vodka/russki_standart/rusv95_944_01_10_14.html',
#                            'name': 'Водка «Русский Стандарт Платинум», 1 л',
#                            'price': 1173,
#                            'product_id': '2080445',
#                            'quantity': 1,
#                            'section': 'Водка',
#                            'spider': 'Winestreet',
#                            'Объем': 1}]},
#  'Winestyle': {'confirmed': False,
#                'order': [{'image': 'https://s3.winestyle.ru/images_gen/225/2253/0_0_orig.jpg',
#                           'link': 'https://winestyle.ru/products/Hennessy-VSOP-Privilege-700.html',
#                           'name': 'Коньяк "Hennessy" V.S.O.P., with gift box, '
#                                   '0.7 л',
#                           'price': 3634,
#                           'product_id': '2073930',
#                           'quantity': 2,
#                           'section': 'Коньяк',
#                           'spider': 'Winestyle',
#                           'Объем': 0.7},
#                          {'image': 'https://s.winestyle.ru/images_gen/417/4172/0_0_orig.jpg',
#                           'link': 'https://winestyle.ru/products/Russian-Standard-Platinum-1000.html',
#                           'name': 'Водка "Русский Стандарт" Платинум, 1 л',
#                           'price': 1156,
#                           'product_id': '2080445',
#                           'quantity': 1,
#                           'section': 'Водка',
#                           'spider': 'Winestyle',
#                           'Объем': 1}]},
#  'mixed': {'confirmed': False,
#            'order': [{'image': 'https://s.wine.style/images_gen/225/2253/0_0_prod_desktop.jpg',
#                       'link': 'https://winestyle.ru/products/Hennessy-VSOP-Privilege-700.html',
#                       'name': 'Коньяк "Hennessy" V.S.O.P., with gift box, 0.7 '
#                               'л',
#                       'price': 3634,
#                       'product_id': '2073930',
#                       'quantity': 2,
#                       'section': 'Коньяк',
#                       'spider': 'Winestyle',
#                       'Объем': 0.7},
#                      {'image': 'https://static.decanter.ru/image/305139-vodka-russian-standard-platinum-1-l-f.jpg',
#                       'link': 'https://decanter.ru/product/russian-standard-platinum-id1493',
#                       'name': 'Водка Русский Стандарт Платинум 1 л',
#                       'price': 1215,
#                       'product_id': '2080445',
#                       'quantity': 1,
#                       'section': 'Водка',
#                       'spider': 'Decanter',
#                       'Объем': 1}]},
#  'order_num': '1872658'}
