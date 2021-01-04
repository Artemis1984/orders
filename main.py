from flask import Flask, render_template, request
from pymongo import MongoClient
from pprint import pprint
from hashlib import sha1
from create_groups import read_file
from create_groups import take_other_groups


client = MongoClient('localhost', 27017)
Orders_DB = client.Orders_DB

app = Flask(__name__)
app.config['SECRET_KEY'] = '12091988BernardoProvencanoToto'

# order = [{'name': 'Шампанское Moet & Chandon, Brut "Imperial", gift box',
#          'Артикул': 'в2752',
#          'image': 'https://s.wine.style/images_gen/275/2752/0_0_prod_desktop.jpg',
#          'link': 'https://winestyle.ru/products/Moet-Chandon-Brut-Imperial-in-gift-box.html',
#          'Объем': 0.75,
#          'quantity': 2,
#          'type': 'Шампанское',
#          'price': 3986},
#          {'name': 'Виски "Macallan" Double Cask 12 Years Old, gift box, 0.7 л',
#          'Артикул': 'в71280',
#          'image': 'https://s.wine.style/images_gen/712/71280/0_0_prod_desktop.jpg',
#          'link': 'https://winestyle.ru/products/Macallan-Double-Cask-12-Years-Old-gift-box.html',
#          'Объем': 0.7,
#          'quantity': 3,
#          'type': 'Виски',
#          'price': 4576}
# ]


# print(order)

# order_num = '1872658'

@app.route('/', methods=['GET', 'POST'])
def main_page():
    order = read_file('order.json')
    order_num = order[0]['order_num']
    shop = order[0]['active']
    order = order[0][order[0]['active']]
    sum_ = sum([i['price'] * i['quantity'] for i in order])

    order = {'_id': order_num, 'link': 'http://127.0.0.1:5000/order/' + order_num, 'sum_': sum_,
             'status': 'Ожидает', 'order_shop': shop}

    Orders_DB['orders'].update_one({'_id': take_other_groups()['order_num']}, {'$set': take_other_groups()}, upsert=True)
    # pprint(list(Orders_DB['orders'].find({'_id': take_other_groups()['order_num']})))
    # print('from DB')
    return render_template('main_page.html', orders=[order])


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
            for j in found:
                for i in j['order']:
                    if i['link'] == request.form['not_in_stock']:
                        if not ('not_in_stock' in i.keys()):
                            i['not_in_stock'] = True
                        else:
                            i.pop('not_in_stock')
                Orders_DB['orders'].delete_one({'_id': order_num})
                Orders_DB['orders'].update_one({'_id': order_num}, {'$set': found[0]}, upsert=True)
        # pprint(found)

    if 'saving' in request.form:
        orders = list(Orders_DB['orders'].find({'_id': order_num}))
        for i in orders[0]['order']:
            i['price'] = request.form[i['link']+'price']
            i['price'] = float(i['price']) if '.' in i['price'] else int(i['price'])

        if orders[0]['confirmed']:
                orders[0]['confirmed'] = False
                confirmed = False
        else:
            orders[0]['confirmed'] = True
            confirmed = True

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

    pprint(list(Orders_DB['orders'].find({'_id': order_num})))

    return render_template('orders.html', groups=orders, order_num=order_num, sum_=sum_, comments=comments[::-1], my_ip=ip_address, confirmed=confirmed, shop=shop)


if __name__ == '__main__':
    app.run(debug=True)
