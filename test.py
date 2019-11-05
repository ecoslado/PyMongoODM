import models, fields

class Shoe(models.Model):
    color = fields.StringField()
    size = fields.StringField()
    material = fields.StringField()
    cordon = fields.ObjectField()

class Cordon(models.Model):
    material = fields.StringField()
    color = fields.StringField()

if __name__ == '__main__':
    shoe = Shoe(color='green', size='23', material='nylon', cordon=Cordon(material='nylon', color='blue'))
    shoe.save()
    Shoe.objects.find()
    myshoe = shoe.deserialize({
        '__type__': {'class': 'Shoe', 'module': '__main__'},
        'color': 'green',
        'size': '23',
        'material': 'nylon',
        'cordon': {'__type__': {'class': 'Cordon', 'module': '__main__'},
                   'material': 'nylon', 'color': 'blue'}
    })

    print(myshoe.get_color)
    print(myshoe.get_size)
    print(myshoe.get_cordon.get_color)
    print(myshoe.get_material)



