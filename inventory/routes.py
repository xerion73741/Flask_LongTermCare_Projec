from flask import render_template
from . import inventory_bp

@inventory_bp.route('/list')
def invenvtory_list():
    items = [
        {'name': '口罩', 'quantity': 120},
        {'name': '酒精', 'quantity': 30},
        {'name': '手套', 'quantity': 55},
    ]
    return render_template('inventory/list.html', items=items)

