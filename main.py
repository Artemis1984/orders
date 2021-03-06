from flask import Flask, render_template, request, redirect, flash
from pymongo import MongoClient
from pprint import pprint
from hashlib import sha1
from create_groups import read_file
from create_groups import take_other_groups, get_orders, prepare_orders
import os
import requests
from bs4 import BeautifulSoup as Bs


os.popen('mongod --dbpath /Users/artak/data/db')

client = MongoClient('localhost', 27017)
Orders_DB = client.Orders_DB

app = Flask(__name__)
app.config['SECRET_KEY'] = '12091988BernardoProvencanoToto'


@app.route('/order_for_client/<string:order_num>/<path>', methods=['GET', 'POST'])
def client_page(order_num, path):
    order = Orders_DB['orders'].find({'_id': order_num})
    if order[0][path]['confirmed']:
        order_num = order[0]['order_num']
        order = order[0][path]['order']
        sum_ = sum([i['price'] * i['quantity'] for i in order])
        return render_template('client_page.html', order=order, sum_=sum_, shop=path, order_num=order_num)
    else:
        return render_template('no_orders.html')


@app.route('/', methods=['GET', 'POST'])
def main_page():

    # Orders_DB['orders'].delete_many({})

    # Orders_DB['Виски'].delete_many({})
    # for i in read_file('whiskey.json'):
    #     Orders_DB['Виски'].update_one({'_id': i['_id']}, {'$set': i}, upsert=True)
    #
    # Orders_DB['Водка'].delete_many({})
    # for i in read_file('vodka.json'):
    #     Orders_DB['Водка'].update_one({'_id': i['_id']}, {'$set': i}, upsert=True)
    #
    # Orders_DB['Шампанское и игристое вино'].delete_many({})
    # for i in read_file('champagne.json'):
    #     Orders_DB['Шампанское и игристое вино'].update_one({'_id': i['_id']}, {'$set': i}, upsert=True)
    #
    # Orders_DB['Коньяк'].delete_many({})
    # for i in read_file('cognac.json'):
    #     Orders_DB['Коньяк'].update_one({'_id': i['_id']}, {'$set': i}, upsert=True)

    if 'change_shop' in request.form:
        Orders_DB['orders'].update_one({'_id': request.form['order']}, {'$set': {'active': request.form['change_shop']}}, upsert=True)

    orders = get_orders()
    # orders = read_file('orders.json')
    # orders = []
    for i in orders:
        if not list(Orders_DB['orders'].find({'_id': i['order_id']})):
            i = prepare_orders(i)
            order = take_other_groups([i])
            order['contacts'] = dict()
            order['contacts']['address'] = i['delivery_address']
            order['contacts']['phone'] = i['phone']
            order['contacts']['customer'] = i['customer']
            order['contacts']['order_date'] = i['order_date']
            Orders_DB['orders'].update_one({'_id': order['order_num']}, {'$set': order}, upsert=True)

    shops = ['Alcomarket', 'Amwine', 'Decanter', 'Lwine', 'Winestreet', 'Winestyle', 'Mixed']
    orders = list(Orders_DB['orders'].find())

    order_list = []
    for item in orders:
        order_num = item['order_num']
        shop = item['active']
        order = item[shop]['order']
        sum_ = sum([i['price'] * i['quantity'] for i in order])
        sums = {}
        for i in list(Orders_DB['orders'].find({'_id': order_num}))[0]:
            if i in shops:
                if i != list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']:
                    group = list(Orders_DB['orders'].find({'_id': order_num}, {i: 1}))[0]
                    sums[i] = sum([k['price'] * k['quantity'] for k in group[i]['order']])

        Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'sums': sums}}, upsert=True)

        new_order = dict()
        new_order['_id'] = order_num
        new_order['sum_'] = sum_
        new_order['order_shop'] = shop
        new_order['link'] = 'http://127.0.0.1:5000/order/' + order_num + '/' + shop
        new_order['sums'] = sums
        if item[item['active']]['confirmed'] and not [n for n in item[item['active']]['order'] if 'not_in_stock' in n.keys()]:
            new_order['status'] = 'Подтвержден'
            new_order['client_link'] = 'http://127.0.0.1:5000/order_for_client/' + order_num + '/' + shop
        elif item[item['active']]['confirmed'] and [n for n in item[item['active']]['order'] if 'not_in_stock' in n.keys()]:
            new_order['status'] = 'Нет в наличии'
        elif not item[item['active']]['confirmed']:
            new_order['status'] = 'Ожидает'

        order_list.append(new_order)

    return render_template('main_page.html', orders=order_list)


@app.route('/order/<string:order_num>/<path>', methods=['GET', 'POST'])
def orders(order_num, path):

    order = list(Orders_DB['orders'].find({'_id': order_num}))

    if not order:
        return render_template('no_orders.html')
    shops = ['Alcomarket', 'Amwine', 'Decanter', 'Lwine', 'Winestreet', 'Winestyle', 'Mixed']
    order_count = [i for i in order[0].keys() if i in shops]
    actual_shops = []
    for i in order_count:
        for j in order[0][i]['order']:
            if 'not_in_stock' in j:
                break
        else:
            actual_shops.append(i)

    order_num = order[0]['order_num']
    order = order[0][path]

    ip_address = request.remote_addr.replace('.', '')
    # Orders_DB['orders'].delete_many({})
    # Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'order': order}}, upsert=True)
    # Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'confirmed': False}}, upsert=True)

    if request.method == 'GET':
        Orders_DB['replace'].delete_one({'_id': order_num})
        Orders_DB['delete'].delete_one({'_id': order_num})

    if 'check_in_stock' in request.form:
        # print('check_in_stock')
        orders = list(Orders_DB['orders'].find({'_id': order_num}))
        # orders[0][path]['confirmed'] = True
        orders = [orders[0][path]['order']]
        for i in orders[0]:
            price = check_functions[i['spider']](i['link'])
            if price:
                if price != i['price']:
                    i['price'] = price
            else:
                i['not_in_stock'] = True

        Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {f'{path}.order': orders[0]}})
        Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {f'{path}.confirmed': True}})

    if 'delete_this' in request.form:
        delete_list = list(Orders_DB['delete'].find({'_id': order_num}))
        if not delete_list:
            Orders_DB['delete'].update_one({'_id': order_num}, {'$set': {'delete_list': [request.form['delete_this']]}},
                                            upsert=True)
        else:
            delete_list = delete_list[0]['delete_list']
            if not (request.form['delete_this'] in delete_list):
                delete_list.append(request.form['delete_this'])
            else:
                delete_list.remove(request.form['delete_this'])

            Orders_DB['delete'].update_one({'_id': order_num}, {'$set': {'delete_list': delete_list}})
        # print(request.form['delete_this'])

    if 'index' in request.form:
        # Orders_DB['replace'].delete_many({})
        replace_list = list(Orders_DB['replace'].find({'_id': order_num}))
        if not replace_list:
            Orders_DB['replace'].update_one({'_id': order_num}, {'$set': {'replace_list': [request.form['index']]}}, upsert=True)
        else:
            replace_list = replace_list[0]['replace_list']
            if not (request.form['index'] in replace_list):
                replace_list.append(request.form['index'])
            else:
                replace_list.remove(request.form['index'])

            Orders_DB['replace'].update_one({'_id': order_num}, {'$set': {'replace_list': replace_list}})

        # print('replace_list')
        # pprint(list(Orders_DB['replace'].find({'_id': order_num})))

    if 'comment' in request.form:
        # active_shop = list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']
        # active_shop = list(Orders_DB['orders'].find({'_id': order_num}))[0][path]
        if request.form['comment']:
            item = list(Orders_DB['orders'].find({'_id': order_num}, {path+'.comments': 1}))
            if 'comments' in item[0][path].keys():
                comments = item[0][path]['comments']
                comments.append({ip_address: request.form['comment']})
            else:
                comments = []
                comments.append({ip_address: request.form['comment']})

            Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {path+'.comments': comments}}, upsert=True)

    if 'not_in_stock' in request.form:
        found = list(Orders_DB['orders'].find({'_id': order_num}))
        if found:
            for i in found[0][path]['order']:
                if i['link'] == request.form['not_in_stock']:
                    if not ('not_in_stock' in i.keys()):
                        i['not_in_stock'] = True
                        Orders_DB[i['section']].update_one({'link': i['link']}, {'$set': {'not_in_stock': True}})
                    else:
                        i.pop('not_in_stock')
                        Orders_DB[i['section']].update_one({'link': i['link']}, {'$unset': {'not_in_stock': 1}}, upsert=True)

            Orders_DB['orders'].delete_one({'_id': order_num})
            Orders_DB['orders'].update_one({'_id': order_num}, {'$set': found[0]}, upsert=True)

    if 'saving' in request.form:
        orders = list(Orders_DB['orders'].find({'_id': order_num}))
        delete_list = list(Orders_DB['delete'].find({'_id': order_num}))
        if delete_list:
            delete_list = delete_list[0]['delete_list']
            for i in delete_list:
                for j in orders[0][path]['order']:
                    if j['link'] == i:
                        orders[0][path]['order'].remove(j)
                        break

        for i in orders[0][path]['order']:
            i['price'] = request.form[i['link']+'price']
            i['price'] = float(i['price']) if '.' in i['price'] else int(i['price'])

        if orders[0][path]['confirmed']:
            orders[0][path]['confirmed'] = False
        else:
            orders[0][path]['confirmed'] = True

        Orders_DB['orders'].delete_one({'_id': order_num})
        Orders_DB['orders'].update_one({'_id': order_num}, {'$set': orders[0]}, upsert=True)

    orders = list(Orders_DB['orders'].find({'_id': order_num}))
    orders = [orders[0][path]['order']]

    sum_ = sum([i['price'] * i['quantity'] for i in orders[0] if not ('not_in_stock' in i.keys())])

    confirmed = list(Orders_DB['orders'].find({'_id': order_num}))[0]
    confirmed = confirmed[path]['confirmed']
    shop = list(Orders_DB['orders'].find({'_id': order_num}))[0][path]
    comments = shop['comments'] if 'comments' in shop.keys() else []

    not_in_stock = [i for i in orders[0] if 'not_in_stock' in i.keys()]
    other_drinks = []

    if confirmed and not_in_stock and not actual_shops:
        # champagne = read_file('champagne.json')
        # whiskey = read_file('whiskey.json')
        # vodka = read_file('vodka.json')
        # cognac = read_file('cognac.json')
        # drinks = {'Виски': whiskey, 'Водка': vodka, 'Шампанское и игристое вино': champagne, 'Коньяк': cognac}

        for i in not_in_stock:
            other_drink = {}

            # other_drink[i['name']] = [k for k in drinks[i['section']] if 'product_id' in k.keys() and (k['product_id'] == i['product_id']) and (k['link'] != i['link']) and ('features' in k.keys() and 'Объем' in k['features'].keys() and k['features']['Объем'] == i['Объем'])]
            other_drink[i['name']] = [k for k in list(Orders_DB[i['section']].find()) if 'product_id' in k.keys() and (k['product_id'] == i['product_id']) and (k['link'] != i['link']) and ('features' in k.keys() and 'Объем' in k['features'].keys() and k['features']['Объем'] == i['Объем']) and not ('not_in_stock' in k.keys())]
            other_drinks.append(other_drink)

        if 'saving_replace' in request.form:

            replace_list = list(Orders_DB['replace'].find({'_id': order_num}))
            if replace_list:
                replace_list = replace_list[0]['replace_list']

            extended_other_drinks = []
            for i in other_drinks:
                extended_other_drinks.extend(list(i.values())[0])

            product_id_list = []
            for i in replace_list:
                product_id_list.append([k['product_id'] for k in extended_other_drinks if k['link'] == i][0])

            if len(product_id_list) != len(set(product_id_list)):
                flash('Вы можете выбрать один напиток из каждой группы')
                active = list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']
                return redirect(f'/order/{order_num}/{active}')
            else:
                orders_new = list(Orders_DB['orders'].find({'_id': order_num}))[0][path]['order']
                orders_new_test = list(Orders_DB['orders'].find({'_id': order_num}))
                not_in_stock_items = [i for i in orders_new if 'not_in_stock' in i.keys()]

                for i in replace_list:
                    new_product_dict = {}
                    found = [k for k in extended_other_drinks if k['link'] == i][0]
                    new_product_dict['image'] = found['image']
                    new_product_dict['link'] = found['link']
                    new_product_dict['name'] = found['name']
                    new_product_dict['section'] = found['section']
                    new_product_dict['price'] = found['price']
                    new_product_dict['product_id'] = found['product_id']
                    new_product_dict['Объем'] = found['features']['Объем']
                    new_product_dict['quantity'] = [k['quantity'] for k in not_in_stock_items if k['product_id'] == found['product_id']][0]
                    new_product_dict['price'] = found['price']
                    new_product_dict['spider'] = found['spider']
                    orders_new.append(new_product_dict)

                    for k in other_drinks:
                        if found in list(k.values())[0]:
                            orders_new.remove([n for n in not_in_stock_items if n['name'] == list(k.keys())[0]][0])

                for i in not_in_stock_items:

                    try:
                        new_card = {}
                        # new_card['image'] = request.form[i['name'] + 'image']
                        new_card['image'] = i['image']
                        new_card['name'] = request.form[i['name'] + 'name']
                        new_card['Объем'] = i['Объем']
                        new_card['price'] = request.form[i['name'] + 'price']
                        new_card['price'] = float(new_card['price']) if '.' in new_card['price'] else int(new_card['price'])
                        new_card['spider'] = request.form[i['name'] + 'spider']
                        new_card['link'] = request.form[i['name'] + 'link']
                        new_card['quantity'] = i['quantity']
                        new_card['section'] = i['section']
                        new_card['product_id'] = i['product_id']

                        orders_new.append(new_card)
                        orders_new.remove(i)
                    except:
                        pass

                if len(set([i['spider'] for i in orders_new])) > 1:
                    orders_new_test[0].pop(orders_new_test[0]['active'])
                    orders_new_test[0]['Mixed'] = dict()
                    orders_new_test[0]['Mixed']['order'] = orders_new
                    orders_new_test[0]['active'] = 'Mixed'
                    if not [k for k in orders_new if 'not_in_stock' in k.keys()]:
                        orders_new_test[0]['Mixed']['confirmed'] = False
                    else:
                        orders_new_test[0]['Mixed']['confirmed'] = True
                    Orders_DB['orders'].delete_one({'_id': order_num})
                    Orders_DB['orders'].update_one({'_id': order_num}, {'$set': orders_new_test[0]}, upsert=True)

                else:
                    orders_new_test[0].pop(orders_new_test[0]['active'])
                    active = list(set([i['spider'] for i in orders_new]))[0]
                    orders_new_test[0][active] = dict()
                    orders_new_test[0][active]['order'] = orders_new
                    orders_new_test[0]['active'] = active
                    if not [k for k in orders_new if 'not_in_stock' in k.keys()]:
                        orders_new_test[0][active]['confirmed'] = False
                    else:
                        orders_new_test[0][active]['confirmed'] = True
                    Orders_DB['orders'].delete_one({'_id': order_num})
                    Orders_DB['orders'].update_one({'_id': order_num}, {'$set': orders_new_test[0]}, upsert=True)

            Orders_DB['replace'].delete_one({'_id': order_num})

            active = list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']
            orders = list(Orders_DB['orders'].find({'_id': order_num}))
            orders = [orders[0][active]['order']]
            sum_ = sum([i['price'] * i['quantity'] for i in orders[0] if not ('not_in_stock' in i.keys())])
            confirmed = list(Orders_DB['orders'].find({'_id': order_num}))[0]
            confirmed = confirmed[active]['confirmed']
            shop = list(Orders_DB['orders'].find({'_id': order_num}))[0][active]
            comments = shop['comments'] if 'comments' in shop.keys() else []
            return redirect(f'/order/{order_num}/{active}')

    contacts = list(Orders_DB['orders'].find({'_id': order_num}))[0]['contacts']
    active = list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']
    confirmed = list(Orders_DB['orders'].find({'_id': order_num}))[0][active]['confirmed']
    not_in_stock_in_shop = None
    if confirmed and [i for i in orders[0] if 'not_in_stock' in i.keys()]:
        not_in_stock_in_shop = 'Нет в наличии'

    return render_template('orders.html', groups=orders, order_num=order_num, sum_=sum_, comments=comments[::-1], my_ip=ip_address, confirmed=confirmed, shop=path, other_drinks=other_drinks, contacts=contacts, not_in_stock_in_shop=not_in_stock_in_shop)


def check_lwine(link):
    response = requests.get(link)
    if response.status_code == 200:
        in_stock = Bs(response.text, 'html.parser').findChild("button", {"class": "main-button btn-buy"})
        if in_stock:
            price = Bs(response.text, 'html.parser').findChild("section", {"itemprop": "offers"}).findChild('span').text
            price = price[:price.index(' Р')].replace(' ', '')
            price = float(price) if '.' in price else int(price)
            return price
        else:
            return None
    else:
        return None


def check_alcomarket(link):
    response = requests.get(link)
    if response.status_code == 200:
        in_stock = Bs(response.text, 'html.parser').findChild("div", {"class": "right relative"}).findChild("div", {"class": "catalog_item_buy"})
        if in_stock:
            price = Bs(response.text, 'html.parser').findChild("div", {"class": "price"}).text.replace('  ', '')
            price = price.replace(' ', '').replace('\n', '').replace('р', '')
            price = float(price) if '.' in price else int(price)
            return price
        else:
            return None
    else:
        return None


def check_amwine(link):
    response = requests.get(link)
    if response.status_code == 200:
        in_stock = Bs(response.text, 'html.parser').findChild("div", {"class": "bth-add-to-cart-block bth-add-to-cart-block_detail js-add-to-cart-wrapper"})
        if in_stock:
            price = Bs(response.text, 'html.parser').findChild("div", {"class": "col-md-10 col-lg-6"}).findChild("span", {"itemprop": "price"}).get_attribute_list('content')
            price = price[0].replace(' ', '').replace('\n', '').replace('р', '')
            price = float(price) if '.' in price else int(price)
            return price
        else:
            return None
    else:
        return None


def check_decanter(link):
    response = requests.get(link)
    if response.status_code == 200:
        in_stock = Bs(response.text, 'html.parser').findChild("a", {"class": "prod-card__button"})
        if in_stock:
            price = Bs(response.text, 'html.parser').findChild("div", {"class": "prod-card__price"}).findChildren("div")
            for i in price:
                if 'руб.' in i.text:
                    price = i.text.replace('\n', '').replace('\xa0', '').replace('руб.', '')
                    price = float(price) if '.' in price else int(price)
            return price
        else:
            return None
    else:
        return None


def check_winestreet(link):
    response = requests.get(link)
    if response.status_code == 200:
        in_stock = Bs(response.text, 'html.parser').findChild("div", {"class": "cart_wrap"}).findChild("a", {"class": "submit catalog-put-to-cart"})
        # print(in_stock)
        if in_stock:
            price = Bs(response.text, 'html.parser').findChild("div", {"class": "cart_wrap"}).findChild("div", {"class": "cl_price"}).text
            price = price[:price.index('Р')].replace('\n', '').replace(' ', '')
            price = float(price) if '.' in price else int(price)
            return price
        else:
            return None
    else:
        return None


def check_winestyle(link):
    headers = {'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'}
    response = requests.get(link, headers=headers)
    if response.status_code == 200:
        in_stock = Bs(response.text, 'html.parser').findChild("form", {"class": "form-add-cart"})
        if in_stock:
            price = Bs(response.text, 'html.parser').findChild("div", {"class": "right-info"}).findChild("div", {"class": "price"}).text
            price = price[:price.index(' руб.')].replace(' ', '')
            price = float(price) if '.' in price else int(price)
            return price
        else:
            return None
    else:
        return None


check_functions = {'Lwine': check_lwine, 'Alcomarket': check_alcomarket, 'Amwine': check_amwine, 'Decanter': check_decanter, 'Winestreet': check_winestreet, 'Winestyle': check_winestyle}

if __name__ == '__main__':
    app.run(debug=True)
