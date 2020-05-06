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
