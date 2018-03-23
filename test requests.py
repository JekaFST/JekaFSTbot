# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup
from DBMethods import DB

text = ''
tags_list = ['font', 'p', 'div', 'span', 'td', 'tr', 'table', 'hr', 'object', 'param', 'audio', 'source', 'embed', 'list']


def send_object_text(text):
    text_pieces = list()

    if 'table' in text or 'script' in text or 'object' in text or 'audio' in text:
        text = 'В тексте найдены и вырезаны скрипты таблицы, аудию и/или иные объекты\r\n' \
               '\xE2\x9D\x97<b>Информация в чате может отличаться от движка</b>\xE2\x9D\x97\r\n' + text
    text = cut_script(text)
    text = cut_formatting(text, tags_list)
    text, images = cut_images(text)
    text, links = cut_links(text)
    text, coords = handle_coords(text)

    if len(text) > 7000:
        text_pieces = cut_long_text_on_pieces(text, text_pieces)

    if text_pieces:
        for text in text_pieces:
            send_text(text)
    else:
        send_text(text)


def cut_formatting(text, tags_list):
    text = text.replace('&amp;', '&')

    br_tags_to_cut = ['<br/>', '<br />', '<br>']
    for br_tag in br_tags_to_cut:
        text = text.replace(br_tag, '\r\n')

    layout_tags_to_cut = ['<i>', '</i>', '<u>', '</u>', '<strong>', '</strong>', '<b>', '</b>']
    for layout_tag in layout_tags_to_cut:
        text = text.replace(layout_tag, '')

    text = cut_style(text)
    text = cut_tags(text, tags_list)

    h_tags = re.findall(r'<h\d>', text)
    soup = BeautifulSoup(text)
    for h_tag in h_tags:
        for h in soup.find_all('h%s' % h_tag[-2]):
            text = text.replace(str(h), h.text.encode('utf-8'))

    return text


def cut_images(text):
    images = list()
    for i, img in enumerate(re.findall(r'<img[^>]*>', text)):
        soup = BeautifulSoup(img)
        img_soup = soup.find_all('img')
        images.append(img_soup[0].get('src').encode('utf-8'))
        image = '(img%s)' % i
        text = text.replace(img, image)

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
    print text


def cut_links(text, cut=False):
    links = list()

    links_to_check = re.findall(r'<a[^>]+>', text)
    for link in links_to_check:
        href = re.search(r'href\s*=\s*[^>\s]+', link).group(0)
        if '"' not in href:
            soup = BeautifulSoup(link)
            for a in soup.find_all('a'):
                text = text.replace(href, 'href="' + a.get('href').encode('utf-8') + '"')

    if cut:
        soup = BeautifulSoup(text)
        for i, ahref in enumerate(soup.find_all('a')):
            link = '(link%s)' % i
            links.append(ahref.get('href').encode('utf-8'))
            str_ahref = str(ahref)
            str_ahref = str_ahref.replace('&amp;', '&')
            text = text.replace(str_ahref, ahref.text.encode('utf-8') + link)
    return text, links


def cut_tags(text, tags_list):
    for tag in tags_list:
        tag_reps = re.findall(r'<%s[^>]*>' % tag, text)
        for tag_rep in tag_reps:
            text = text.replace(tag_rep, '')

        text = text.replace('</%s>' % tag, '')
        text = text.replace('</ %s>' % tag, '')
        text = text.replace('<%s/>' % tag, '')
        text = text.replace('<%s />' % tag, '')

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
