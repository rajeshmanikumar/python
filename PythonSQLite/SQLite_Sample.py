import sqlite3
from items import Items

print('Connection Init..')
conn = sqlite3.connect('myitems.db') # ':memory:'
print('Connection Established')
c = conn.cursor()

print('Creating new Table..')
c.execute("""CREATE TABLE ITEMS (
            item_id integer,
            item_name text,
            item_cost float
            )""")

print('Table Created.')

# Sample Insert Query
def insert_item(item):
    with conn:
        c.execute("INSERT INTO ITEMS VALUES (:item_id, :item_name, :item_cost)", {'item_id': item.item_id, 'item_name': item.item_name, 'item_cost': item.item_cost})

# Sample Select Query
def get_item_by_name(item_name):
    c.execute("SELECT * FROM ITEMS WHERE item_name=:item_name", {'item_name': item_name})
    return c.fetchall()

# Sample Update Query
def update_item_cost(item, item_cost):
    with conn:
        c.execute("""UPDATE ITEMS SET item_cost = :item_cost
                    WHERE item_id = :item_id AND item_name = :item_name""",
                  {'item_id': item.item_id, 'item_name': item.item_name, 'item_cost': item_cost})

# Sample Delete Query
def remove_item(item):
    with conn:
        c.execute("DELETE from ITEMS WHERE item_id = :item_id AND item_name = :item_name",
                  {'item_id': item.item_id, 'item_name': item.item_name})

# Insert Block
print('Insert Operation Begin..')
item_1 = Items('1', 'Python 3 Book',300)
item_2 = Items('2', 'Java Book', 450)

insert_item(item_1)
insert_item(item_2)

print('Inserted')

# Select / Fetch Block
item_info = get_item_by_name('Java Book')
print('Query Result:')
print(item_info)

# Update Block
update_item_cost(item_2, 250)
print('Item - 2 Cost Updated.')

# Delete Block
remove_item(item_1)
print('Item -1 Removed.')

item_info = get_item_by_name('Java Book')
print('Updated Query Result:')
print(item_info)

conn.close()
print('Connection Closed. Exit!')