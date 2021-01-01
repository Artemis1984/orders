from flask import Flask, render_template, request
from pymongo import MongoClient
from pprint import pprint
from hashlib import sha1


client = MongoClient('localhost', 27017)
Orders_DB = client.Orders_DB

app = Flask(__name__)
app.config['SECRET_KEY'] = '12091988BernardoProvencanoToto'

order = [{'name': 'Шампанское Moet & Chandon, Brut "Imperial", gift box',
         'Артикул': 'в2752',
         'image': 'https://s.wine.style/images_gen/275/2752/0_0_prod_desktop.jpg',
         'link': 'https://winestyle.ru/products/Moet-Chandon-Brut-Imperial-in-gift-box.html',
         'Объем': 0.7,
         'quantity': 2,
         'price': 3986},
         {'name': 'Виски "Macallan" Double Cask 12 Years Old, gift box, 0.7 л',
         'Артикул': 'в71280',
         'image': 'https://s.wine.style/images_gen/712/71280/0_0_prod_desktop.jpg',
         'link': 'https://winestyle.ru/products/Macallan-Double-Cask-12-Years-Old-gift-box.html',
         'Объем': 0.7,
         'quantity': 3,
         'price': 4576}
         ]



order_num = '1872658'
orders = [order]


@app.route('/', methods=['GET', 'POST'])
def main_page():
    print('Запрос', request.args)
    ip_address = request.remote_addr.replace('.', '')
    # Orders_DB['orders'].delete_many({})
    # Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'order': order}}, upsert=True)

    if 'comment' in request.form:
        if request.form['comment']:
            item = list(Orders_DB['orders'].find({'_id': order_num}, {'comments': 1}))
            # print('UP', comments)
            if 'comments' in item[0].keys():
                comments = item[0]['comments']
                # comments.append(request.form['comment'])
                comments.append({ip_address: request.form['comment']})
            else:
                comments = []
                # comments.append(request.form['comment'])
                comments.append({ip_address: request.form['comment']})
            Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'comments': comments}})
        # # if item:
        # if comments:
        #     comments = comments[0]
        #     comments.append(request.form['comment'])
        #     Orders_DB['orders'].update_one({'_id': order_num}, {'$set': {'comments': comments}})
        # else:
        #     # comments.append(request.form['comment'])

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

    if 'saving' in request.form:
        orders = list(Orders_DB['orders'].find({'_id': order_num}))
        for i in orders[0]['order']:
            i['price'] = request.form[i['link']+'price']
            i['price'] = float(i['price']) if '.' in i['price'] else int(i['price'])

        Orders_DB['orders'].delete_one({'_id': order_num})
        Orders_DB['orders'].update_one({'_id': order_num}, {'$set': orders[0]}, upsert=True)

    orders = list(Orders_DB['orders'].find({'_id': order_num}))
    orders = [orders[0]['order']]
    sum_ = sum([i['price'] * i['quantity'] for i in orders[0] if not ('not_in_stock' in i.keys())])
    # pprint(list(Orders_DB['orders'].find({'_id': order_num})))

    items = list(Orders_DB['orders'].find({'_id': order_num}, {'comments': 1}))
    # print('down', items)
    comments = []
    if 'comments' in items[0].keys():
        comments = items[0]['comments']
        # print('downer', comments)

    return render_template('orders.html', groups=orders, order_num=order_num, sum_=sum_, comments=comments[::-1], my_ip=ip_address)


if __name__ == '__main__':
    app.run(debug=True)