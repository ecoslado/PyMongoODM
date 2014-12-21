PyMongoODM
==========

Mongo ODM wroten in Python and based in pymongo client.
* Installation 
TODO

* Configuration 
TODO

* Define your model
<pre>
from pymongodm import Model, fields
</pre>
<pre>
class Post(Model):
         author = fields.StringField()
         body = fields.StringField()
         comments = fields.ListField(cls=Comment)
         tags = fields.ListField(cls=str)
</pre>
<pre>
class Comment(Model):
        author = fields.StringField()
        body = fields.StringField()
</pre>

* Create some objects
<pre>
post = Post(author = "Enrique Coslado")
post.setattr("body", "Lorem Ipsum ...")
post.getbody
> "Lorem Ipsum ..."
</pre>
<pre>
post.save()
</pre>
