db.define_table(
    'the_help'
    , Field('lang')
    , Field('url_controller', default='')
    , Field('url_function', default='')
    , Field('title')
    , Field('description')
    , Field('tags', 'list:string')
    , Field('contents', 'text')

)
db.the_help.title.requires = IS_NOT_EMPTY(error_message='Please add a title')
db.the_help.description.requires = IS_NOT_EMPTY(error_message='Please add a description')
db.the_help.contents.requires = IS_NOT_EMPTY(error_message='Please add content')
