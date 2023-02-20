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
        text = f'В тексте найдены и вырезаны скрипты, таблицы, аудио и/или иные объекты\r\n' \
               f'\xE2\x9D\x97<b>Информация в чате может отличаться от движка</b>\xE2\x9D\x97\r\n{text}'

    text, _, _ = cut_script(text, bot=bot, chat_id=chat_id, message=f'{header}\r\nСкрипт не вырезан', raw_text=raw_text,
                            r2=None, r3=None)
    text, images, _ = cut_images(text, bot=bot, chat_id=chat_id, message=f'{header}\r\nКартинки не вырезаны', r2=list(),
                                 r3=None, raw_text=raw_text)
    text, _, _ = cut_formatting(text, tags_list=tags_list, bot=bot, chat_id=chat_id, raw_text=raw_text, r2=None, r3=None,
                                message=f'{header}\r\nФорматирование не вырезано')
    text, _, _ = reformat_links(text, bot=bot, chat_id=chat_id, message=f'{header}\r\nСсылки не вырезаны', r2=None, r3=None,
                                raw_text=raw_text)
    text, indexes, incommon_coords = handle_coords(text, session_id=session_id, from_updater=from_updater, storm=storm,
                                                   bot=bot, chat_id=chat_id, raw_text=raw_text, r2=list(), r3=list(),
                                                   message=f'{header}\r\nКоординаты не обработаны')
    while '\r\n\r\n\r\n' in text:
        text = text.replace('\r\n\r\n\r\n', '\r\n\r\n')
    text, _, _ = cut_extra_links_endings(text, bot=bot, chat_id=chat_id, r2=None, r3=None, raw_text=raw_text,
                                         message=f'{header}\r\nЛишние окончания ссылок не вырезаны')

    if not send_text(text, header=header, bot=bot, chat_id=chat_id, parse_mode='HTML', raw_text=raw_text, text_pieces=list(),
                     message=f'{header}\r\nТекст с не вырезанными ссылками и разметкой не отправлен', send_to_chat=False):
        text, links, text_cut_links = cut_links_change_small_symbol(text, bot=bot, chat_id=chat_id, raw_text=raw_text,
                                                                    message=f'{header}\r\nСсылки не вырезаны', r2=list(), r3=text)
        if not send_text(text, header=header, bot=bot, chat_id=chat_id, parse_mode='HTML', raw_text=raw_text, send_to_chat=False,
                         text_pieces=list(), message=f'{header}\r\nТекст с вырезанным знаком меньше и разметкой не отправлен'):
            if not send_text(text_cut_links, header=header, bot=bot, chat_id=chat_id, parse_mode='HTML',
                             raw_text=raw_text, text_pieces=list(), send_to_chat=False,
                             message=f'{header}\r\nТекст с вырезанными ссылками, знаком меньше и разметкой не отправлен'):
                header_not_bold = header.replace('<b>', '')
                header_not_bold = header_not_bold.replace('</b>', '')
                if not send_text(text_cut_links, header=header_not_bold, bot=bot, chat_id=chat_id, parse_mode=None,
                                 raw_text=raw_text, text_pieces=list(), send_to_chat=True,
                                 message=f'{header}\r\nТекст с вырезанными ссылками и без разметки не отправлен'):
                    try:
                        soup = BeautifulSoup(text_cut_links)
                        send_text(soup.get_text(), header=header_not_bold, bot=bot, chat_id=chat_id, parse_mode=None,
                                  raw_text=raw_text, text_pieces=list(), send_to_chat=True,
                                  message=f'{header}\r\nТекст с вырезанными ссылками и без разметки, вытащенный методом парсером, не отправлен')
                    except:
                        pass
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

    br_tags_to_cut = ['</br>', '</br >', '</ br>', '<br/>', '<br />', '<br>', '&nbsp;']
    for br_tag in br_tags_to_cut:
        text = text.replace(br_tag, '\r\n')

    text, _, _ = cut_style(text, bot=kwargs['bot'], chat_id=kwargs['chat_id'], message='Стили не вырезаны', r2=None, r3=None)
    for tag in kwargs['tags_list']:
        text, _, _ = cut_tag(text, tag=tag, bot=kwargs['bot'], chat_id=kwargs['chat_id'], raw_text=kwargs['raw_text'],
                       message=f'Unparsed tag "{tag}" in chat_id: {kwargs["chat_id"]}', r2=None, r3=None)

    h_tags = re.findall(r'<h\d>', text)
    soup = BeautifulSoup(text)
    for h_tag in h_tags:
        for h in soup.find_all(f'h{h_tag[-2]}'):
            text = text.replace(str(h), h.text.encode('utf-8'))

    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_images(text, **kwargs):
    images = list()
    for i, img in enumerate(re.findall(r'<img[^>]*>|<image[^>]*>', text)):
        soup = BeautifulSoup(img)
        img_soup = soup.find_all('img') if 'img' in img else soup.find_all('image')
        images.append(str.strip(img_soup[0].get('src').encode('utf-8')))
        image = f'(img{i+1})'
        text = text.replace(img, image)
    text = text.replace('<img>', '')
    text = text.replace('</img>', '')

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
            replacement = f'(link{i})'
            text = text.replace(link, replacement)

    coords = list()
    init_coords = find_coords(text)
    for coord in init_coords:
        if coord in coords:
            continue
        coords.append(coord)
    if coords:
        if kwargs['from_updater'] and not kwargs['storm']:
            for coord in coords:
                locations = DBSession.get_locations(kwargs['session_id'])
                i = 1 if not locations else len(locations.keys()) + 1
                coord_Y_G = f'make_Y_G_links(coord) - <b>{i}</b>'
                text = text.replace(coord, coord_Y_G)
                if str(i) not in locations.keys():
                    indexes.append(i)
                locations[str(i)] = coord
                DBSession.update_json_field(kwargs['session_id'], 'locations', locations)

        elif not kwargs['from_updater'] and not kwargs['storm']:
            for coord in coords:
                locations = DBSession.get_locations(kwargs['session_id'])
                if coord in locations.values():
                    for k, v in locations.items():
                        if coord == str(v):
                            coord_Y_G = f'{make_Y_G_links(coord)} - <b>{k}</b>'
                            text = text.replace(coord, coord_Y_G)
                            indexes.append(int(k))
                            break
                else:
                    coord_Y_G = make_Y_G_links(coord)
                    text = text.replace(coord, coord_Y_G)
                    incommon_coords.append(coord)
        else:
            for i, coord in enumerate(coords):
                coord_Y_G = f'{make_Y_G_links(coord)} - <b>{i+1}</b>'
                text = text.replace(coord, coord_Y_G)
                incommon_coords.append(coord)

    for rep in re.findall(r'\(link\d+\)', text):
        j = re.findall(r'\d+', rep)
        text = text.replace(rep, links[int(j[0])])

    return text, indexes, incommon_coords


def make_Y_G_links(coord):
    lat = re.findall(r'\d\d\.\d{4,7}', coord)[0]
    long = re.findall(r'\d\d\.\d{4,7}', coord)[1]
    Y = f'<a href="http://maps.yandex.ru/?text={lat},{long}">[Y]</a>'
    G = f'<a href="https://maps.google.com/?daddr={lat},{long}&t=m">[G]</a>'
    # G = '<a href="https://www.google.com/maps/place/%s,%s">[G]</a>' % (lat, long)
    coord_Y_G = f'<b>{coord}</b> {Y} {G}'
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
            kwargs['bot'].send_message(kwargs['chat_id'], f'{kwargs["header"]}\r\n{text}',
                                       parse_mode=kwargs['parse_mode'], disable_web_page_preview=True)
    else:
        kwargs['bot'].send_message(kwargs['chat_id'], f'{kwargs["header"]}\r\n{text}',
                                   parse_mode=kwargs['parse_mode'], disable_web_page_preview=True)
    return True


@ExceptionHandler.convert_text_exception
def reformat_links(text, **kwargs):
    links = re.findall(r'<A[^>]+>|<a[^>]+>', text)
    for link in links:
        soup = BeautifulSoup(link)
        text = text.replace(link, f'<a href="{str.strip(soup.find_all("a")[0].get("href").encode("utf-8"))}">')
        text = text.replace('</A>', '</a>')
        text = text.replace('<A/>', '</a>')
        text = text.replace('<a/>', '</a>')
    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_extra_links_endings(text, **kwargs):
    a_openings = re.findall(r'<a[^>]+>', text)
    a_closings = re.findall(r'</a>', text)
    if len(a_closings) > len(a_openings):
        links = re.findall(r'<a\sh.+>.*</a>', text)
        for i, link in enumerate(links):
            cut_link = f'(link{i})'
            text = text.replace(link, cut_link)
        text = text.replace('</a>', '')
        for i, link in enumerate(links):
            cut_link = f'(link{i})'
            text = text.replace(cut_link, link)
    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_links_change_small_symbol(text, **kwargs):
    links = list()
    links_indexes = list()
    links_text = list()

    str_ahrefs = re.findall(r'<a\sh.+>.*</a>', text)
    for i, str_ahref in enumerate(str_ahrefs):
        link = f'(link{i})'
        soup = BeautifulSoup(str_ahref)
        ahref = soup.find_all('a')[0]
        links.append(ahref.get('href').encode('utf-8'))
        str_ahref = str_ahref.replace('&amp;', '&')
        text = text.replace(str_ahref, ahref.text.encode('utf-8') + link)
        links_text.append(str_ahref)
        links_indexes.append(ahref.text.encode('utf-8') + link)
    text_cut_links = text
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    for i, link_index in enumerate(links_indexes):
        text = text.replace(link_index, links_text[i])
    return text, links, text_cut_links


@ExceptionHandler.convert_text_exception
def cut_tag(text, **kwargs):
    tag_reps = re.findall(r'<%s[^>]*>|<%s[^>]*>' % (kwargs['tag'], kwargs['tag'].upper()), text)
    for tag_rep in tag_reps:
        text = text.replace(tag_rep, '')
    text = text.replace(f'</{kwargs["tag"]}>', '')
    text = text.replace(f'</{kwargs["tag"]} >', '')
    text = text.replace(f'</{kwargs["tag"].upper()}>', '')
    text = text.replace(f'</{kwargs["tag"].upper()} >', '')

    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_style(text, **kwargs):
    try:
        soup = BeautifulSoup(text)
        for rep in soup.find_all('style'):
            string = str(rep.string.encode('utf-8'))
            text = text.replace(string, '')

        style_rests = ['<style>', '<style >', '<style/>', '<style />', '<style"">', '</style>', '<style  />']
        for style_rest in style_rests:
            for st in re.findall(style_rest, text):
                text = text.replace(st, '')
    except Exception:
        reps = re.findall(r'<style>[\s\S]*</style>', text)
        for rep in reps:
            text = text.replace(rep, '')

    return text, None, None


@ExceptionHandler.convert_text_exception
def cut_script(text, **kwargs):
    soup = BeautifulSoup(text)
    for script in soup.find_all('script'):
        coords = str()
        coords_in_script = find_coords(str(script))
        for coord in coords_in_script:
            coords += f'\r\nКорды из скрипта: {coord}'
        text = text.replace(str(script), coords)

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
        message = f'(link{i})'
        bot.send_message(chat_id, f'{message}\r\n{link}', disable_web_page_preview=True)


@ExceptionHandler.send_text_objects_exception
def send_images(bot, chat_id, **kwargs):
    if len(kwargs['images']) <= 5:
        for i, image in enumerate(kwargs['images']):
            message = f'(img{i+1})'
            bot.send_photo(chat_id, image, caption=message)
    else:
        text = f'Найдено {len(kwargs["images"])} изображений. Их отправка заблокирована\r\n' \
               f'Для отправки всех изображений из задания введите /task_images'
        bot.send_message(chat_id, text)


@ExceptionHandler.send_text_objects_exception
def send_index_venue(bot, chat_id, **kwargs):
    for i in kwargs['indexes']:
        latitude = re.findall(r'\d\d\.\d{4,7}', kwargs['locations'][str(i)])[0]
        longitude = re.findall(r'\d\d\.\d{4,7}', kwargs['locations'][str(i)])[1]
        bot.send_venue(chat_id, latitude, longitude, f'{kwargs["locations"][str(i)]} - {i}', '')


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
            bot.send_venue(chat_id, latitude, longitude, f'{coord} - {i+1}', '')
