from core.util import path_format, db_space
import os


def artworks(datas, filter=lambda id: True):
    if isinstance(datas, dict):
        for id, _detail in datas.items():
            if filter(id) is False:
                yield id


def author_space(item):
    author_path = "%s_%s" % (item['author']['name'], item['author']['id'])
    return path_format(author_path)


def file_space(item):
    illust_path = "%s_%s" % (item['title'], item['id'])
    return os.path.join(
        author_space(item),
        path_format(illust_path),
    )


def novel_html(title, novel):
    _html = '''
        <html>
            <head>
                <title>%s</title>
                <style type="text/css">
                    body{
                        width: 650px;
                        margin: auto;
                    }
                    .img{
                       text-align: center;
                    }
                    img{
                        width:80%%;
                    }
                </style>
            </head>
            <body>
                %s
            </body>
        </html>
    ''' % (title, novel)
    return _html


def novel_format(novel):
    _html = novel
    _html = ''.join("<p>%s</p>" % line for line in _html.split("\n") if len(line.strip()) > 0)
    _html = _html.replace("[newpage]", "")

    return _html


def novel_bind_image(novel, images: dict):
    _html = novel_format(novel)
    for id, image in images.items():
        _tag_image = '[pixivimage:%s]' % id
        _img_html = '<div class="img" ><img src="%s" /></div>' % image
        _html = _html.replace(_tag_image, _img_html)
    return _html
