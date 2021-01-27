import json
from pprint import pprint
from itertools import groupby
import requests


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
    # sections = set([i['section'] for i in order])
    order_ids = set([i['product_id'] for i in order])

    for item in order:
        # Исключаем поставщика, которому принадлежит ордер, но в случае смешанного заказа, нужно будет не исключать и взять всех
        # others = [i for i in cats[item['section']] if 'product_id' in i.keys() and (i['product_id'] == item['product_id']) and (i['spider'] != item['spider']) and (i['features']['Объем'] == item['Объем'])]
        others = [i for i in cats[item['section']] if 'product_id' in i.keys() and (i['product_id'] == item['product_id']) and ('Объем' in i['features'].keys() and i['features']['Объем'] == item['Объем'])]
        for k in others:
            other_groups.append(k)

    # pprint(other_groups)

    keyfunc = lambda x: x['spider']
    grouped_shops = list(set([i[0] for i in groupby(other_groups, key=keyfunc)]))
    new_groups = {}

    for i in grouped_shops:
        found = [k for k in other_groups if k['spider'] == i]
        # sect = len(set([r['section'] for r in found]))
        # found_ids = len(set([i['product_id'] for i in found]))
        # if found_ids == len(order_ids):
        pprint(found)
        for item in order:
            if not [k for k in found if k['product_id'] == item['product_id'] and (k['features']['Объем'] == item['Объем'])]:
                break
        else:
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
            # for j in set(products):
            for j in order:
                # min_price = min([n['price'] for n in updated_groups[i] if n['product_id'] == j])
                min_price = min([n['price'] for n in updated_groups[i] if n['product_id'] == j['product_id'] and n['Объем'] == j['Объем']])
                temp = [r for r in updated_groups[i] if r['price'] == min_price and r['product_id'] == j['product_id']]
                if temp:
                    unique_products.append(temp[0])
            updated_groups[i] = unique_products
        else:
            unique_products.append({'order': updated_groups[i]})

    if len(set([i['spider'] for i in order])) == 1:
        updated_groups[order[0]['spider']] = {'order': order, 'confirmed': False}
        updated_groups['active'] = order[0]['spider']
    else:
        updated_groups['active'] = 'Mixed'
        updated_groups['Mixed'] = {'order': order, 'confirmed': False}

    updated_groups['order_num'] = order_num
    for i in updated_groups:
        if type(updated_groups[i]) != dict and i in grouped_shops:
        # if type(updated_groups[i]) != dict and i in grouped_shops and (len(updated_groups[i]) == len(order)):
            updated_groups[i] = {'order': updated_groups[i], 'confirmed': False}

    return updated_groups


def get_orders():
    response = requests.get('https://alko.www-technologies.ru/api/orders')
    response = json.loads(response.text)
    return response


def prepare_orders(order):

    whiskey = read_file('whiskey.json')
    champagne = read_file('champagne.json')
    vodka = read_file('vodka.json')
    cognac = read_file('cognac.json')

    order_dict = dict()
    order_dict['order'] = order['items']
    for item in order_dict['order']:
        found = [k for k in whiskey if 'id' in k.keys() and k['id'] == item['item_id']]
        if found:
            found = found[0]
            new_item = dict()
            new_item['price'] = item['price']
            new_item['name'] = found['name']
            new_item['image'] = found['image']
            new_item['section'] = found['section']
            new_item['link'] = found['link']
            new_item['product_id'] = found['product_id']
            new_item['Объем'] = found['features']['Объем']
            new_item['quantity'] = item['quantity']
            new_item['spider'] = found['spider']

            order_dict['order'][order_dict['order'].index(item)] = new_item

    order['order_num'] = order.pop('order_id')
    order['items'] = order_dict['order']
    order_head_name = list(set([i['spider'] for i in order['items']]))
    if len(order_head_name) == 1:
        order[order_head_name[0]] = order.pop('items')
        order['active'] = order_head_name[0]
    else:
        order['Mixed'] = order.pop('items')
        order['active'] = 'Mixed'

    return order


# orders = read_file('orders.json')
# new_one = {'order_num': '11',
#           'active': 'Mixed',
#           'Mixed': [{'image': 'https://amwine.ru/upload/iblock/f0d/f0d4bb11af6ae7c8fe57ca4176a6f00e.png',
#                     'link': 'https://amwine.ru/catalog/krepkie_napitki/viski/makkalan_dabl_kask_18_let_v_p_u/',
#                     'name': 'Виски Маккалан дабл каск 18 лет в п/у 0.7 л',
#                     'price': 11635,
#                     'product_id': '4185023',
#                     'quantity': 1,
#                     'section': 'Виски',
#                     'spider': 'Amwine',
#                     'Объем': 0.7},
#                    {'image': 'https://static.decanter.ru/image/292916-viski-fox-and-dogs-0-5-l-f.jpg',
#                     'link': 'https://decanter.ru/product/fox-and-dogs-id83074',
#                     'name': 'Виски Fox and Dogs 0.5 л',
#                     'price': 504,
#                     'product_id': '2093337',
#                     'quantity': 1,
#                     'section': 'Виски',
#                     'spider': 'Decanter',
#                     'Объем': 0.5},
#                    {'image': 'https://static.decanter.ru/image/300109-viski-fox-and-dogs-0-7-l-f.jpg',
#                     'link': 'https://decanter.ru/product/fox-and-dogs-id109008',
#                     'name': 'Виски Fox and Dogs 0.7 л',
#                     'price': 706,
#                     'product_id': '2093337',
#                     'quantity': 1,
#                     'section': 'Виски',
#                     'spider': 'Decanter',
#                     'Объем': 0.7}]}

# orders.append(new_one)
# write_file('orders.json', orders)

# К такому виду нужно привести заказ для дальнейшей обработки
# order = {"active": "mixed",
#         "order_num": "1872658",
#         "mixed": [{
#             "price": 3634,
#             "name": "Коньяк \"Hennessy\" V.S.O.P., with gift box, 0.7 л",
#             "image": "https://s.wine.style/images_gen/225/2253/0_0_prod_desktop.jpg",
#             "link": "https://winestyle.ru/products/Hennessy-VSOP-Privilege-700.html",
#             "product_id": "2073930",
#             "Объем": 0.7,
#             "quantity": 2,
#             "section": "Коньяк",
#             "spider": "Winestyle"
#           },
#           {
#             "price": 1215,
#             "name": "Водка Русский Стандарт Платинум 1 л",
#             "image": "https://static.decanter.ru/image/305139-vodka-russian-standard-platinum-1-l-f.jpg",
#             "link": "https://decanter.ru/product/russian-standard-platinum-id1493",
#             "product_id": "2080445",
#             "Объем": 1,
#             "quantity": 1,
#             "section": "Водка",
#             "spider": "Decanter"
#           }]
# }


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
