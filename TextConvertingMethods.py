# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup
from DBMethods import DB, DBSession
from ExceptionHandler import ExceptionHandler


def send_object_text(text, header, bot, chat_id, session_id, from_updater, storm):
    tags_list = DB.get_tags_list()
    raw_text = text
    links = list()
    send_links = False

    if 'table' in text or 'script' in text or 'object' in text or 'audio' in text:
        text = 'В тексте найдены и вырезаны скрипты таблицы, аудию и/или иные объекты\r\n' \
               '\xE2\x9D\x97<b>Информация в чате может отличаться от движка</b>\xE2\x9D\x97\r\n' + text

    text, _, _ = cut_script(text, bot=bot, chat_id=chat_id, message=header + '\r\nСкрипт не вырезан', raw_text=raw_text,
                            r2=None, r3=None)
    text, _, _ = cut_formatting(text, tags_list=tags_list, bot=bot, chat_id=chat_id, raw_text=raw_text, r2=None, r3=None,
                                message=header + '\r\nФорматирование не вырезано')
    text, images, _ = cut_images(text, bot=bot, chat_id=chat_id, message=header + '\r\nКартинки не вырезаны', r2=list(),
                                 r3=None, raw_text=raw_text)
    text, _, _ = reformat_links(text, bot=bot, chat_id=chat_id, message=header + '\r\nСсылки не вырезаны', r2=None, r3=None,
                                raw_text=raw_text)
    text, indexes, incommon_coords = handle_coords(text, session_id=session_id, from_updater=from_updater, storm=storm,
                                                   bot=bot, chat_id=chat_id, raw_text=raw_text, r2=list(), r3=list(),
                                                   message=header + '\r\nКоординаты не обработаны')
    while '\r\n\r\n\r\n' in text:
        text = text.replace('\r\n\r\n\r\n', '\r\n\r\n')

    if not send_text(text, header=header, bot=bot, chat_id=chat_id, parse_mode='HTML', raw_text=raw_text, text_pieces=list(),
                     message=header + '\r\nТекст с не вырезанными ссылками и разметкой не отправлен', send_to_chat=False):
        text, links, text_cut_links = cut_links_change_small_symbol(text, bot=bot, chat_id=chat_id, raw_text=raw_text,
                                                                    message=header + '\r\nСсылки не вырезаны', r2=list(), r3=text)
        if not send_text(text, header=header, bot=bot, chat_id=chat_id, parse_mode='HTML', raw_text=raw_text, send_to_chat=False,
                         text_pieces=list(), message=header + '\r\nТекст с вырезанным знаком меньше и разметкой не отправлен'):
            if not send_text(text_cut_links, header=header, bot=bot, chat_id=chat_id, parse_mode='HTML',
                             raw_text=raw_text, text_pieces=list(), send_to_chat=False,
                             message=header + '\r\nТекст с вырезанными ссылками, знаком меньше и разметкой не отправлен'):
                header_not_bold = header.replace('<b>', '')
                header_not_bold = header_not_bold.replace('</b>', '')
                send_text(text_cut_links, header=header_not_bold, bot=bot, chat_id=chat_id, parse_mode=None,
                          raw_text=raw_text, text_pieces=list(), send_to_chat=True,
                          message=header + '\r\nТекст с вырезанными ссылками и без разметки не отправлен')
            send_links = True

    if images:
        send_images(bot, chat_id, images=images, message='Exception - бот не смог отправить картинки')

    if links and send_links:
        send_links_to_chat(bot, chat_id, links=links, message='Exception - бот не смог отправить ссылки')

    locations = DBSession.get_locations(session_id)
    if locations and indexes:
        send_index_venue(bot, chat_id, indexes=indexes, locations=locations, message='Бот не смог отправить координаты')

    if incommon_coords:
        send_incommon_coords(bot, chat_id, incommon_coords=incommon_coords, storm=storm,
                             message='Бот не смог отправить координаты')


@ExceptionHandler.convert_text_exception
def cut_formatting(text, **kwargs):
    text = text.replace('&amp;', '&')

    br_tags_to_cut = ['<br/>', '<br />', '<br>', '&nbsp;']
    for br_tag in br_tags_to_cut:
        text = text.replace(br_tag, '\r\n')

    layout_tags_to_cut = ['<i>', '</i>', '<u>', '</u>', '<strong>', '</strong>', '<b>', '</b>']
    for layout_tag in layout_tags_to_cut:
        text = text.replace(layout_tag, '')

    text, _, _ = cut_style(text, bot=kwargs['bot'], chat_id=kwargs['chat_id'], message='Стили не вырезаны', r2=None, r3=None)
    for tag in kwargs['tags_list']:
        text, _, _ = cut_tag(text, tag=tag, bot=kwargs['bot'], chat_id=kwargs['chat_id'], raw_text=kwargs['raw_text'],
                       message='Unparsed tag "%s" in chat_id: %s' % (tag, str(kwargs['chat_id'])), r2=None, r3=None)

    h_tags = re.findall(r'<h\d>', text)
    soup = BeautifulSoup(text)
    for h_tag in h_tags:
        for h in soup.find_all('h%s' % h_tag[-2]):
            text = text.replace(str(h), h.text.encode('utf-8'))

    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_images(text, **kwargs):
    images = list()
    for i, img in enumerate(re.findall(r'<img[^>]*>|<image[^>]*>', text)):
        soup = BeautifulSoup(img)
        img_soup = soup.find_all('img') if 'img' in img else soup.find_all('image')
        images.append(img_soup[0].get('src').encode('utf-8'))
        image = '(img%s)' % i
        text = text.replace(img, image)
    text = text.replace('<img>', '')

    return text, images, None


@ExceptionHandler.convert_text_exception
def handle_coords(text, **kwargs):
    incommon_coords = list()
    indexes = list()

    soup = BeautifulSoup(text)
    for ahref in soup.find_all('a'):
        coord_links = find_coords(ahref.text.encode('utf-8'))
        if coord_links:
            str_ahref = str(ahref)
            str_ahref = str_ahref.replace('&amp;', '&')
            text = text.replace(str_ahref, ahref.text.encode('utf-8'))

    links = re.findall(r'<a[^>]+>', text)
    for i, link in enumerate(links):
        coords = find_coords(link)
        if coords:
            replacement = '(link%s)' % i
            text = text.replace(link, replacement)

    coords = find_coords(text)
    if coords:
        if kwargs['from_updater'] and not kwargs['storm']:
            for coord in coords:
                locations = DBSession.get_locations(kwargs['session_id'])
                i = 1 if not locations else len(locations.keys()) + 1
                coord_Y_G = make_Y_G_links(coord) + ' - <b>' + str(i) + '</b>'
                text = text.replace(coord, coord_Y_G)
                if unicode(i) not in locations.keys():
                    indexes.append(i)
                locations[str(i)] = coord
                DBSession.update_json_field(kwargs['session_id'], 'locations', locations)

        elif not kwargs['from_updater'] and not kwargs['storm']:
            for coord in coords:
                locations = DBSession.get_locations(kwargs['session_id'])
                if coord in locations.values():
                    for k, v in locations.items():
                        if coord == str(v):
                            coord_Y_G = make_Y_G_links(coord) + ' - <b>' + str(k) + '</b>'
                            text = text.replace(coord, coord_Y_G)
                            indexes.append(int(k))
                            break
                else:
                    coord_Y_G = make_Y_G_links(coord)
                    text = text.replace(coord, coord_Y_G)
                    incommon_coords.append(coord)
        else:
            for i, coord in enumerate(coords):
                coord_Y_G = make_Y_G_links(coord) + ' - <b>' + str(i + 1) + '</b>'
                text = text.replace(coord, coord_Y_G)
                incommon_coords.append(coord)

    for rep in re.findall(r'\(link\d+\)', text):
        j = re.findall(r'\d+', rep)
        text = text.replace(rep, links[int(j[0])])

    return text, indexes, incommon_coords


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


@ExceptionHandler.send_text_exception
def send_text(text, **kwargs):
    text_pieces = kwargs['text_pieces']
    if len(text) > 7000:
        text_pieces = cut_long_text_on_pieces(text, text_pieces)
    if text_pieces:
        for text in text_pieces:
            kwargs['bot'].send_message(kwargs['chat_id'], kwargs['header'] + '\r\n' + text,
                                       parse_mode=kwargs['parse_mode'], disable_web_page_preview=True)
    else:
        kwargs['bot'].send_message(kwargs['chat_id'], kwargs['header'] + '\r\n' + text,
                                   parse_mode=kwargs['parse_mode'], disable_web_page_preview=True)
    return True


@ExceptionHandler.convert_text_exception
def reformat_links(text, **kwargs):
    links_to_lower = re.findall(r'<A\sH[^>]+>|'
                                r'<A\sh[^>]+>', text)
    for link in links_to_lower:
        soup = BeautifulSoup(link)
        for a in soup.find_all('a'):
            link_lower = link.replace(a.get('href').encode('utf-8'), 'link')
            link_lower = link_lower.lower()
            link_lower = link_lower.replace('link', a.get('href').encode('utf-8'))
            text = text.replace(link, link_lower)
    text = text.replace('</A>', '</a>')

    links_to_check = re.findall(r'<a[^>]+>', text)
    for link in links_to_check:
        href = re.search(r'href\s*=\s*[^>\s]+', link).group(0)
        if '"' not in href:
            soup = BeautifulSoup(link)
            for a in soup.find_all('a'):
                text = text.replace(href, 'href="' + a.get('href').encode('utf-8') + '"')
    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_links_change_small_symbol(text, **kwargs):
    links = list()
    links_indexes = list()
    links_text = list()

    str_ahrefs = re.findall(r'<a\sh.+>.*</a>', text)
    for i, str_ahref in enumerate(str_ahrefs):
        link = '(link%s)' % i
        soup = BeautifulSoup(str_ahref)
        ahref = soup.find_all('a')[0]
        links.append(ahref.get('href').encode('utf-8'))
        str_ahref = str_ahref.replace('&amp;', '&')
        text = text.replace(str_ahref, ahref.text.encode('utf-8') + link)
        links_text.append(str_ahref)
        links_indexes.append(ahref.text.encode('utf-8') + link)
    text_cut_links = text
    text = text.replace('<', '&lt;')
    for i, link_index in enumerate(links_indexes):
        text = text.replace(link_index, links_text[i])
    return text, links, text_cut_links


@ExceptionHandler.convert_text_exception
def cut_tag(text, **kwargs):
    tag_reps = re.findall(r'<%s[^>]*>|<%s[^>]*>' % (kwargs['tag'], kwargs['tag'].upper()), text)
    for tag_rep in tag_reps:
        text = text.replace(tag_rep, '')
    text = text.replace('</%s>' % kwargs['tag'], '')
    text = text.replace('</%s>' % kwargs['tag'].upper(), '')

    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_style(text, **kwargs):
    soup = BeautifulSoup(text)
    for rep in soup.find_all('style'):
        string = str(rep.string)
        text = text.replace(string, '')

    style_rests = ['<style>', '<style >', '<style/>', '<style />', '<style"">', '</style>', '<style  />']
    for style_rest in style_rests:
        for st in re.findall(style_rest, text):
            text = text.replace(st, '')

    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_script(text, **kwargs):
    soup = BeautifulSoup(text)
    for script in soup.find_all('script'):
        text = text.replace(str(script), '')

    return text, None, None


def find_coords(text):
    coords = re.findall(r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', text)
    return coords


@ExceptionHandler.send_text_objects_exception
def send_links_to_chat(bot, chat_id, **kwargs):
    for i, link in enumerate(kwargs['links']):
        message = '(link%s)' % i
        bot.send_message(chat_id, message + '\r\n' + link, disable_web_page_preview=True)


@ExceptionHandler.send_text_objects_exception
def send_images(bot, chat_id, **kwargs):
    if len(kwargs['images']) <= 5:
        for i, image in enumerate(kwargs['images']):
            message = '(img%s)' % i
            bot.send_photo(chat_id, image, caption=message)
    else:
        text = 'Найдено %s изображений. Их отправка заблокирована\r\n' \
               'Для отправки всех изображений из задания введите /task_images' % str(len(kwargs['images']))
        bot.send_message(chat_id, text)


@ExceptionHandler.send_text_objects_exception
def send_index_venue(bot, chat_id, **kwargs):
    for i in kwargs['indexes']:
        latitude = re.findall(r'\d\d\.\d{4,7}', kwargs['locations'][str(i)])[0]
        longitude = re.findall(r'\d\d\.\d{4,7}', kwargs['locations'][str(i)])[1]
        bot.send_venue(chat_id, latitude, longitude, kwargs['locations'][str(i)] + ' - ' + str(i), '')


@ExceptionHandler.send_text_objects_exception
def send_incommon_coords(bot, chat_id, **kwargs):
    if not kwargs['storm']:
        for coord in kwargs['incommon_coords']:
            latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
            bot.send_venue(chat_id, latitude, longitude, coord, '')
    else:
        for i, coord in enumerate(kwargs['incommon_coords']):
            latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
            bot.send_venue(chat_id, latitude, longitude, coord + ' - ' + str(i + 1), '')
