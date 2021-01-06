from flask import Flask, render_template, request
from pymongo import MongoClient
from pprint import pprint
from hashlib import sha1
from create_groups import read_file
from create_groups import take_other_groups
import os


os.popen('mongod --dbpath /Users/artak/data/db')

client = MongoClient('localhost', 27017)
Orders_DB = client.Orders_DB

app = Flask(__name__)
app.config['SECRET_KEY'] = '12091988BernardoProvencanoToto'


@app.route('/', methods=['GET', 'POST'])
def main_page():

    # Orders_DB['orders'].delete_many({})

    if 'change_shop' in request.form:
        Orders_DB['orders'].update_one({'_id': request.form['order']}, {'$set': {'active': request.form['change_shop']}}, upsert=True)

    orders = read_file('orders.json')
    for i in orders:
        order = take_other_groups([i])
        if not list(Orders_DB['orders'].find({'_id': order['order_num']})):
            Orders_DB['orders'].update_one({'_id': order['order_num']}, {'$set': order}, upsert=True)

    shops = ['Alcomarket', 'Amwine', 'Decanter', 'Lwine', 'Winestreet', 'Winestyle']
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
        new_order['link'] = 'http://127.0.0.1:5000/order/' + order_num
        new_order['sum_'] = sum_
        new_order['order_shop'] = shop
        new_order['sums'] = sums
        if item[item['active']]['confirmed'] and not [n for n in item[item['active']]['order'] if 'not_in_stock' in n.keys()]:
            new_order['status'] = 'Подтвержден'
        elif item[item['active']]['confirmed'] and [n for n in item[item['active']]['order'] if 'not_in_stock' in n.keys()]:
            new_order['status'] = 'Не Подтвержден'
        elif not item[item['active']]['confirmed']:
            new_order['status'] = 'Ожидает'

        order_list.append(new_order)

    return render_template('main_page.html', orders=order_list)


@app.route('/order/<order_num>', methods=['GET', 'POST'])
def orders(order_num):
    # order = read_file('order.json')
    # pprint(list(Orders_DB['orders'].find()))
    order = list(Orders_DB['orders'].find({'_id': order_num}))
    order_num = order[0]['order_num']
    order = order[0][order[0]['active']]
    orders = [order]

    ip_address = request.remote_addr.replace('.', '')
    # Orders_DB['orders'].delete_many({})
    # Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'order': order}}, upsert=True)
    # Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'confirmed': False}}, upsert=True)

    if 'comment' in request.form:
        active_shop = list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']
        if request.form['comment']:
            item = list(Orders_DB['orders'].find({'_id': order_num}, {active_shop+'.comments': 1}))
            if 'comments' in item[0][active_shop].keys():
                comments = item[0][active_shop]['comments']
                print('UP', comments)
                # comments.append(request.form['comment'])
                comments.append({ip_address: request.form['comment']})
            else:
                comments = []
                # comments.append(request.form['comment'])
                comments.append({ip_address: request.form['comment']})

            Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {active_shop+'.comments': comments}})

    if 'not_in_stock' in request.form:
        found = list(Orders_DB['orders'].find({'_id': order_num}))
        if found:
            for i in found[0][found[0]['active']]['order']:
                if i['link'] == request.form['not_in_stock']:
                    if not ('not_in_stock' in i.keys()):
                        i['not_in_stock'] = True
                    else:
                        i.pop('not_in_stock')
            Orders_DB['orders'].delete_one({'_id': order_num})
            Orders_DB['orders'].update_one({'_id': order_num}, {'$set': found[0]}, upsert=True)

    if 'saving' in request.form:
        orders = list(Orders_DB['orders'].find({'_id': order_num}))
        pprint(orders)
        for i in orders[0][orders[0]['active']]['order']:
            i['price'] = request.form[i['link']+'price']
            i['price'] = float(i['price']) if '.' in i['price'] else int(i['price'])

        if orders[0][orders[0]['active']]['confirmed']:
                orders[0][orders[0]['active']]['confirmed'] = False
        else:
            orders[0][orders[0]['active']]['confirmed'] = True

        Orders_DB['orders'].delete_one({'_id': order_num})
        Orders_DB['orders'].update_one({'_id': order_num}, {'$set': orders[0]}, upsert=True)

    # pprint(list(Orders_DB['orders'].find({'_id': order_num})))

    orders = list(Orders_DB['orders'].find({'_id': order_num}))
    orders = [orders[0][orders[0]['active']]['order']]
    sum_ = sum([i['price'] * i['quantity'] for i in orders[0] if not ('not_in_stock' in i.keys())])
    # pprint(list(Orders_DB['orders'].find({'_id': order_num})))

    confirmed = list(Orders_DB['orders'].find({'_id': order_num}))[0]
    confirmed = confirmed[confirmed['active']]['confirmed']
    shop = list(Orders_DB['orders'].find({'_id': order_num}))[0]['active']

    items = list(Orders_DB['orders'].find({'_id': order_num}))
    comments = []
    if 'comments' in items[0][shop].keys():
        comments = items[0][shop]['comments']

    # pprint(list(Orders_DB['orders'].find({'_id': order_num})))

    return render_template('orders.html', groups=orders, order_num=order_num, sum_=sum_, comments=comments[::-1], my_ip=ip_address, confirmed=confirmed, shop=shop)


if __name__ == '__main__':
    app.run(debug=True)
