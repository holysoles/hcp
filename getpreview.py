import requests
# parse link and get thumbnail image from prefix url


def req(link):
    linkarray = link.split('/')
    endlink = linkarray[(len(linkarray) - 1)]
    sku = endlink.split('.')[0]
    previewurl = "https://images.footlocker.com/is/image/EBFL2/" + sku + "?wid=90&hei=90"
    response = requests.get(previewurl)
    img = response.content
    return img
