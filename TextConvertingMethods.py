# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup
from DBMethods import DB, DBSession
from ExceptionHandler import ExceptionHandler


def send_object_text(text, header, bot, chat_id, session_id, from_updater, storm):
    tags_list = DB.get_tags_list()
    raw_text = text
    links = list()

    if 'table' in text or 'script' in text or 'object' in text or 'audio' in text:
        text = 'В тексте найдены и вырезаны скрипты таблицы, аудию и/или иные объекты\r\n' \
               '\xE2\x9D\x97<b>Информация в чате может отличаться от движка</b>\xE2\x9D\x97\r\n' + text
    text = cut_script(text, **{'bot': bot, 'chat_id': chat_id, 'message': header + '\r\nСкрипт не вырезан',
                               'raw_text': raw_text})
    text = cut_formatting(text, **{'tags_list': tags_list, 'bot': bot, 'chat_id': chat_id,
                                   'message': header + '\r\nФорматирование не вырезано', 'raw_text': raw_text})
    text, images = cut_images(text, **{'bot': bot, 'chat_id': chat_id, 'message': header + '\r\nКартинки не вырезаны',
                                       'raw_text': raw_text})
    text = reformat_links(text, **{'bot': bot, 'chat_id': chat_id, 'message': header + '\r\nСсылки не вырезаны',
                                   'raw_text': raw_text})
    text, indexes, incommon_coords = handle_coords(text, session_id, from_updater, storm,
                                                   **{'bot': bot, 'chat_id': chat_id,
                                                      'message': header + '\r\nКоординаты не обработаны', 'raw_text': raw_text})
    while '\r\n\r\n\r\n' in text:
        text = text.replace('\r\n\r\n\r\n', '\r\n\r\n')

    if not send_text(text, **{'header': header, 'bot': bot, 'chat_id': chat_id, 'parse_mode': 'HTML',
                              'raw_text': raw_text, 'text_pieces': list(),
                              'message': header + '\r\nТекст с не вырезанными ссылками и разметкой не отправлен'}):
        text, links = cut_links(text, **{'bot': bot, 'chat_id': chat_id, 'message': header + '\r\nСсылки не вырезаны',
                                         'raw_text': raw_text})
        if not send_text(text, **{'header': header, 'bot': bot, 'chat_id': chat_id, 'parse_mode': 'HTML',
                                  'raw_text': raw_text, 'text_pieces': list(),
                                  'message': header + '\r\nТекст с вырезанными ссылками и разметкой не отправлен'}):
            send_text(text, **{'header': header, 'bot': bot, 'chat_id': chat_id, 'parse_mode': None,
                               'raw_text': raw_text, 'text_pieces': list(),
                               'message': header + '\r\nТекст с вырезанными ссылками и без разметки не отправлен'})

    if images:
        try:
            if len(images) <= 10:
                for i, image in enumerate(images):
                    message = '(img%s)' % i
                    bot.send_photo(chat_id, image, caption=message)
            else:
                text = 'Найдено %s изображений. Их отправка заблокирована\r\n' \
                       'Для отправки всех изображений из задания введите /task_images' % str(len(images))
                bot.send_message(chat_id, text)
        except Exception:
            bot.send_message(chat_id, 'Exception - бот не смог отправить картинки')

    if links:
        try:
            for i, link in enumerate(links):
                message = '(link%s)' % i
                bot.send_message(chat_id, message + '\r\n' + link)
        except Exception:
            bot.send_message(chat_id, 'Exception - бот не смог отправить ссылки')

    locations = DBSession.get_locations(session_id)
    if locations and indexes:
        try:
            for i in indexes:
                latitude = re.findall(r'\d\d\.\d{4,7}', locations[str(i)])[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', locations[str(i)])[1]
                bot.send_venue(chat_id, latitude, longitude, locations[str(i)] + ' - ' + str(i), '')
        except Exception:
            bot.send_message(chat_id, 'Exceprion - бот не смог отправить координаты')

    if incommon_coords:
        if not storm:
            try:
                for coord in incommon_coords:
                    latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                    longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                    bot.send_venue(chat_id, latitude, longitude, coord, '')
            except Exception:
                bot.send_message(chat_id, 'Exceprion - бот не смог отправить не пронумерованные координаты')
        else:
            try:
                for i, coord in enumerate(incommon_coords):
                    latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                    longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                    bot.send_venue(chat_id, latitude, longitude, coord + ' - ' + str(i + 1), '')
            except Exception:
                bot.send_message(chat_id, 'Exceprion - бот не смог отправить координаты')


@ExceptionHandler.text_exception_1_result
def cut_formatting(text, **kwargs):
    text = text.replace('&amp;', '&')

    br_tags_to_cut = ['<br/>', '<br />', '<br>']
    for br_tag in br_tags_to_cut:
        text = text.replace(br_tag, '\r\n')

    layout_tags_to_cut = ['<i>', '</i>', '<u>', '</u>', '<strong>', '</strong>', '<b>', '</b>']
    for layout_tag in layout_tags_to_cut:
        text = text.replace(layout_tag, '')

    text = cut_style(text, **{'bot': kwargs['bot'], 'chat_id': kwargs['chat_id'], 'message': 'Стили не вырезаны'})
    for tag in kwargs['tags_list']:
        text = cut_tag(text, **{'tag': tag, 'bot': kwargs['bot'], 'chat_id': kwargs['chat_id'],
                                'message': 'Unparsed tag "%s" in chat_id: %s' % (tag, str(kwargs['chat_id'])),
                                'raw_text': kwargs['raw_text']})

    h_tags = re.findall(r'<h\d>', text)
    soup = BeautifulSoup(text)
    for h_tag in h_tags:
        for h in soup.find_all('h%s' % h_tag[-2]):
            text = text.replace(str(h), h.text.encode('utf-8'))

    return text


@ExceptionHandler.text_exception_2_results
def cut_images(text, **kwargs):
    images = list()
    for i, img in enumerate(re.findall(r'<img[^>]*>', text)):
        soup = BeautifulSoup(img)
        img_soup = soup.find_all('img')
        images.append(img_soup[0].get('src').encode('utf-8'))
        image = '(img%s)' % i
        text = text.replace(img, image)

    return text, images


@ExceptionHandler.text_exception_3_results
def handle_coords(text, session_id, from_udater, storm, **kwargs):
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
        if from_udater and not storm:
            for coord in coords:
                locations = DBSession.get_locations(session_id)
                i = 1 if not locations else len(locations.keys()) + 1
                coord_Y_G = make_Y_G_links(coord) + ' - <b>' + str(i) + '</b>'
                text = text.replace(coord, coord_Y_G)
                if unicode(i) not in locations.keys():
                    indexes.append(i)
                locations[str(i)] = coord
                DBSession.update_json_field(session_id, 'locations', locations)

        elif not from_udater and not storm:
            for coord in coords:
                locations = DBSession.get_locations(session_id)
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


@ExceptionHandler.text_exception_1_result
def reformat_links(text, **kwargs):
    links_to_lower = re.findall(r'<A[^>]+>', text)
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
    return text


@ExceptionHandler.text_exception_2_results
def cut_links(text, **kwargs):
    links = list()
    soup = BeautifulSoup(text)
    for i, ahref in enumerate(soup.find_all('a')):
        link = '(link%s)' % i
        links.append(ahref.get('href').encode('utf-8'))
        str_ahref = str(ahref)
        str_ahref = str_ahref.replace('&amp;', '&')
        text = text.replace(str_ahref, ahref.text.encode('utf-8') + link)
    return text, links


@ExceptionHandler.text_exception_1_result
def cut_tag(text, **kwargs):
    tag_reps = re.findall(r'<%s[^>]*>|<%s[^>]*>' % (kwargs['tag'], kwargs['tag'].upper()), text)
    for tag_rep in tag_reps:
        text = text.replace(tag_rep, '')
    text = text.replace('</%s>' % kwargs['tag'], '')
    text = text.replace('</%s>' % kwargs['tag'].upper(), '')

    return text


@ExceptionHandler.text_exception_1_result
def cut_style(text, **kwargs):
    soup = BeautifulSoup(text)
    for rep in soup.find_all('style'):
        string = str(rep.string)
        text = text.replace(string, '')

    style_rests = ['<style>', '<style >', '<style/>', '<style />', '<style"">', '</style>', '<style  />']
    for style_rest in style_rests:
        for st in re.findall(style_rest, text):
            text = text.replace(st, '')

    return text


@ExceptionHandler.text_exception_1_result
def cut_script(text, **kwargs):
    soup = BeautifulSoup(text)
    for script in soup.find_all('script'):
        text = text.replace(str(script), '')

    return text


def find_coords(text):
    coords = re.findall(r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', text)
    return coords
