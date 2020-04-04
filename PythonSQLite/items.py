class Items:
    """A sample Item (Store) class"""

    def __init__(self, item_id, item_name, item_cost):
        self.item_id = item_id
        self.item_name = item_name
        self.item_cost = item_cost

    @property
    def itemcost(self):
        return '{} {}'.format(self.item_id, self.item_cost)

    def __repr__(self):
        return "Items('{}', '{}', {})".format(self.item_id, self.item_name, self.item_cost)