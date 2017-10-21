# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup

text = '<font color="ff8400"><b>Куда ехать:</b></font> <b>52.58247, 39.47536 (ул. Детская 2)</b>\r\n' \
       '<font color="ff8400"><b>Античит:</b></font>  <b>52.575144, 39.481383</b>' \
       ' на желтом щите у дороги - последняя строка, второе слово\r\n' \
       '<font color="ff8400"><b>Код доезда:</b></font> у агента <hr size=2>Формат ответа:   ленина 123'

def send_object_text(text):
    text_pieces = list()
    # raw_text = text

    if 'table' in text or 'script' in text:
        text = 'В тексте найдены и вырезаны скрипты и/или таблицы\r\n' \
               '\xE2\x9D\x97<b>Информация в чате может отличаться от движка</b>\xE2\x9D\x97\r\n' + text
    text = cut_script(text)
    text = cut_formatting(text)
    text, images = cut_images(text)
    text, embeds, audios = cut_rare_tags(text)
    text, links = cut_links(text, cut=False)
    text, coords = handle_coords(text)

    if len(text) > 7000:
        text_pieces = cut_long_text_on_pieces(text, text_pieces)

    if text_pieces:
        for text in text_pieces:
            send_text(text)
    else:
        send_text(text)

    # if images:
    #     for i, image in enumerate(images):
    #         message = '(img%s)' % i
    #         bot.send_photo(chat_id, image, caption=message)
    # if links:
    #     for i, link in enumerate(links):
    #         message = '(link%s)' % i
    #         bot.send_message(chat_id, message + '\r\n' + link)
    # if coords:
    #     for i, coord in enumerate(coords):
    #         latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
    #         longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
    #         bot.send_message(chat_id, coord + ' - <b>' + str(i+1) + '</b>', parse_mode='HTML')
    #         bot.send_location(chat_id, latitude, longitude)


def cut_formatting(text):
    text = text.replace('<br/>', '\r\n')
    text = text.replace('<br />', '\r\n')
    text = text.replace('<br>', '\r\n')
    text = text.replace('<i>', '')
    text = text.replace('</i>', '')
    text = text.replace('<u>', '')
    text = text.replace('</u>', '')
    text = text.replace('<strong>', '')
    text = text.replace('</strong>', '')
    text = text.replace('<b>', '')
    text = text.replace('</b>', '')

    text = cut_style(text)
    tags_list = ['font', 'p', 'div', 'span', 'td', 'tr', 'table', 'hr']
    text = cut_tags(text, tags_list)

    h_tags = re.findall(r'<h\d>', text)
    soup = BeautifulSoup(text)
    for h_tag in h_tags:
        for h in soup.find_all('h%s' % h_tag[-2]):
            text = text.replace(str(h), h.text.encode('utf-8'))

    return text


def cut_images(text):
    images = list()

    soup = BeautifulSoup(text)
    links = re.findall(r'<a[^>]+>', text)
    for i, img in enumerate(soup.find_all('img')):
        for k, v in img.attrs.items():
            attr = ' %s=%s' % (k, v)
            attr = attr.encode('utf-8')
            attr2 = ' %s="%s"' % (k, v)
            attr2 = attr2.encode('utf-8')
            attr3 = " %s='%s'" % (k, v)
            attr3 = attr3.encode('utf-8')
            if links:
                for j, link in enumerate(links):
                    if v in link:
                        replacement = '(link%s)' % j
                        text = text.replace(link, replacement)
                        text = text.replace(attr, '')
                        text = text.replace(attr2, '')
                        text = text.replace(attr3, '')
                        text = text.replace(replacement, link)
                    else:
                        text = text.replace(attr2, '')
                        text = text.replace(attr, '')
                        text = text.replace(attr3, '')
            else:
                text = text.replace(attr2, '')
                text = text.replace(attr, '')
                text = text.replace(attr3, '')
        image = '(img%s)' % i
        images.append(img.get('src').encode('utf-8'))
        img_rests = ['<img>', '<img >', '<img/>', '<img />', '<img"">', '<img  />', '<img"" />']
        for img_rest in img_rests:
            for im in re.findall(img_rest, text):
                text = text.replace(im, image)

    return text, images


def handle_coords(text):

    soup = BeautifulSoup(text)
    for ahref in soup.find_all('a'):
        coord_links = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                                 r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                                 r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                                 r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', ahref.text.encode('utf-8'))
        if coord_links:
            str_ahref = str(ahref)
            str_ahref = str_ahref.replace('&amp;', '&')
            text = text.replace(str_ahref, ahref.text.encode('utf-8'))

    links = re.findall(r'<a[^>]+>', text)
    for i, link in enumerate(links):
        coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', link)
        if coords:
            replacement = '(link%s)' % i
            text = text.replace(link, replacement)

    coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', text)
    for i, coord in enumerate(coords):
        coord_Y_G = make_Y_G_links(coord) + ' - <b>' + str(i+1) + '</b>'
        text = text.replace(coord, coord_Y_G)

    for rep in re.findall(r'\(link\d+\)', text):
        j = re.findall(r'\d+', rep)
        text = text.replace(rep, links[int(j[0])])

    return text, coords


def make_Y_G_links(coord):
    lat = re.findall(r'\d\d\.\d{4,7}', coord)[0]
    long = re.findall(r'\d\d\.\d{4,7}', coord)[1]
    Y = '<a href="http://maps.yandex.ru/?text=%s,%s">[Y]</a>' % (lat, long)
    G = '<a href="https://maps.google.com/?daddr=%s,%s&t=m">[G]</a>' % (lat, long)
    # G = '<a href="https://www.google.com/maps/place/%s,%s">[G]</a>' % (lat, long)
    coord_Y_G = '<b>' + coord + '</b> ' + Y + ' ' + G
    return coord_Y_G


def cut_long_text_on_pieces(text, text_pieces):

    while len(text) > 7000:
        text_pieces.append(text[:6999] + ' \xE2\x9C\x82')
        text = text.replace(text[:6999], '\xE2\x9C\x82 ')
    text_pieces.append(text)

    return text_pieces


def send_text(text):
    text = text.replace('<b><b>', '<b>')
    text = text.replace('</b></b>', '</b>')
    links = re.findall(r'<a[^>]+>', text)
    tags = re.findall(r'<..|..>|..>$|<$', text)
    # soup = BeautifulSoup(text)
    # for ahref in soup.find_all('a'):
    #     links.append(str(ahref))
    for tag in tags:
        if tag not in ['<b>', '</b', '<i>', '</i', '/b>', '/i>', '<a ', '</a', '/a>']\
                + [re.search(r'..>', link).group(0) for link in links]:
            # parse = False
            break

    print text
    # parse_mode = 'HTML' if parse else None
    # try:
    #     bot.send_message(chat_id, header + '\r\n' + text, parse_mode=parse_mode, disable_web_page_preview=True)
    #     if not parse:
    #         bot.send_message(45839899, 'Unparsed text in chat_id: %s\r\n\r\n' % str(chat_id) + text,
    #                          disable_web_page_preview=True)
    #         with open("Exceptions_%s.txt" % str(chat_id), "a+") as raw_text_file:
    #             raw_text_file.write('Unparsed text:\r\n' + text + '\r\n\r\n')
    # except Exception:
    #     bot.send_message(chat_id, '<b>Exception</b>\r\nТекст не отправлен', parse_mode='HTML')
    #     try:
    #         with open("Exceptions_%s.txt" % str(chat_id), "a+") as raw_text_file:
    #             raw_text_file.write('Exception on send_object_text:\r\n' + raw_text + '\r\n\r\n')
    #     except Exception:
    #         return


def cut_links(text, cut=True):
    links = list()

    if cut:
        soup = BeautifulSoup(text)
        for i, ahref in enumerate(soup.find_all('a')):
            link = '(link%s)' % i
            links.append(ahref.get('href').encode('utf-8'))
            str_ahref = str(ahref)
            str_ahref = str_ahref.replace('&amp;', '&')
            text = text.replace(str_ahref, ahref.text.encode('utf-8') + link)
    return text, links


def cut_rare_tags(text):
    embeds = list()
    audios = list()

    soup = BeautifulSoup(text)
    for i, embed in enumerate(soup.find_all('embed')):
        for k,v in embed.attrs.items():
            attr = ' %s=%s' % (k, v)
            attr = attr.encode('utf-8')
            attr2 = ' %s="%s"' % (k, v)
            attr2 = attr2.encode('utf-8')
            text = text.replace(attr, '')
            text = text.replace(attr2, '')
            emb = '(emb%s)' % i
            embeds.append(embed.get('src').encode('utf-8'))
        text = text.replace('<embed>', emb)
        text = text.replace('<embed/>', emb)
        text = text.replace('<embed />', emb)
    text = text.replace('</embed>', '')

    soup = BeautifulSoup(text)
    for i, audio in enumerate(soup.find_all('audio')):
        aud = '(audio%s)' % i
        audios.append(audio.get('src').encode('utf-8'))
        text = text.replace(str(audio), aud)

    return text, embeds, audios


def cut_tags(text, tags_list):
    for tag in tags_list:
        soup = BeautifulSoup(text)
        for rep in soup.find_all(tag):
            for k, v in rep.attrs.items():
                if isinstance(v, list):
                    attr = ' %s=%s' % (k, v[0])
                    attr2 = ' %s="%s"' % (k, v[0])
                    attr3 = " %s='%s'" % (k, v[0])
                else:
                    attr = ' %s=%s' % (k, v)
                    attr2 = ' %s="%s"' % (k, v)
                    attr3 = " %s='%s'" % (k, v)
                text = text.replace(str(attr), '')
                text = text.replace(str(attr2), '')
                text = text.replace(str(attr3), '')

            tag_rests = ['<%s>' % tag, '<%s >' % tag, '<%s/>' % tag, '<%s />' % tag, '<%s"">' % tag, '</%s>' % tag, '<%s  />' % tag, '<%s"" />' % tag]
            for tag_rest in tag_rests:
                for value in re.findall(tag_rest, text):
                    text = text.replace(value, '')

    return text


def cut_style(text):
    soup = BeautifulSoup(text)
    for rep in soup.find_all('style'):
        string = str(rep.string)
        text = text.replace(string, '')

    style_rests = ['<style>', '<style >', '<style/>', '<style />', '<style"">', '</style>', '<style  />']
    for style_rest in style_rests:
        for st in re.findall(style_rest, text):
            text = text.replace(st, '')

    return text


def cut_script(text):
    soup = BeautifulSoup(text)
    for script in soup.find_all('script'):
        text = text.replace(str(script), '')

    return text

send_object_text(text)