# -*- coding: utf-8 -*-
import re
import telebot
from bs4 import BeautifulSoup


text = """
<svg style="background: url(http://d1.endata.cx/data/games/60649/final_moryartysherlock_yusgfbhzisguish.png)" width="640" height="404">
  <rect width="148" height="8" x="53" y="32" fill="yellow" id="HealthSher"></rect>
  <rect width="148" height="8" x="440" y="32" fill="yellow" id="HealthMory"></rect>
</svg>
<hr>
<audio src="http://d1.endata.cx/data/games/60649/%5bChiptune%5d+-+Sherlock.mp3" controls></audio>
<hr>
<script>
function HealthSher(n) {
 const HealthSher = document.getElementById("HealthSher")
 const width = parseInt(HealthSher.getAttribute("width")) + n
  if(width < 148 && width>0)
   HealthSher.setAttribute("width", width)
}

function HealthMory(n) {
 const HealthMory = document.getElementById("HealthMory")
 const width = parseInt(HealthMory.getAttribute("width")) + n
  const x = parseInt(HealthMory.getAttribute("x")) - n
  if(width < 148 && width>0) {
   HealthMory.setAttribute("width", width)
   HealthMory.setAttribute("x", x)
  }
}
</script>

<div>
Нанес урона:<br>
<b>Шерлок:</b> <span id="TimeMory"></span><br>
<b>Мориарти:</b> <span id="TimeSher"></span></div>


<script>
    var minTimerMory = 0;
    var i1 = 0;
    function changeTimerMory ( i1 ) {
        minTimerMory += i1;
        document.getElementById("TimeMory").innerHTML=minTimerMory;
        if (minTimerMory >= 200) {
/КОД, ВВОД КОТОРОГО САМОСТОЯТЕЛЬНО РАССМАТРИВАЕТСЯ КАК ЧИТЕРСТВО!/
            $("#lnkAnswerBoxMarker+form input#Answer").val("ВРЕШЬНЕУЙДЕШЬ5429").closest("form").submit();
/КОД, ВВОД КОТОРОГО САМОСТОЯТЕЛЬНО РАССМАТРИВАЕТСЯ КАК ЧИТЕРСТВО!/
        }
    }
</script>

<script>
    var minTimerSher = 0;
    var i2 = 0;
    function changeTimerSher ( i2 ) {
        minTimerSher += i2;
        document.getElementById("TimeSher").innerHTML=minTimerSher;
        if (minTimerSher >= 200) {
/КОД, ВВОД КОТОРОГО САМОСТОЯТЕЛЬНО РАССМАТРИВАЕТСЯ КАК ЧИТЕРСТВО!/
            $("#lnkAnswerBoxMarker+form input#Answer").val("АВОТИНЕУГАДАЛ2485").closest("form").submit();
/КОД, ВВОД КОТОРОГО САМОСТОЯТЕЛЬНО РАССМАТРИВАЕТСЯ КАК ЧИТЕРСТВО!/
        }
    }
</script>
"""


def send_object_text(text):
    tags_list = ['font', 'p', 'div', 'span', 'td', 'tr', 'th', 'table', 'hr', 'object', 'param', 'audio', 'source',
                 'embed', 'link', 'iframe', 'address', 'body', 'html', 'li', 'ol', 'details', 'ul', 'script', 'video',
                 'b', 'center', 'u', 'i', 'strong', 'em', 'style', 'script', 's', 'svg', 'rect', 'del']

    if 'table' in text or 'script' in text or 'object' in text or 'audio' in text:
        text = 'В тексте найдены и вырезаны скрипты таблицы, аудию и/или иные объекты\r\n' \
               '\xE2\x9D\x97<b>Информация в чате может отличаться от движка</b>\xE2\x9D\x97\r\n' + text

    text = cut_script(text)
    text, images = cut_images(text)
    text = cut_formatting(text, tags_list)
    text = reformat_links(text)
    text, indexes = handle_coords(text)
    while '\r\n\r\n\r\n' in text:
        text = text.replace('\r\n\r\n\r\n', '\r\n\r\n')
    text = cut_extra_links_endings(text)

    return text, images, indexes


def cut_formatting(text, tags_list):
    text = text.replace('&amp;', '&')

    br_tags_to_cut = ['</br>', '</br >', '</ br>', '<br/>', '<br />', '<br>', '&nbsp;']
    for br_tag in br_tags_to_cut:
        text = text.replace(br_tag, '\r\n')

    text = cut_style(text)
    for tag in tags_list:
        text = cut_tag(text, tag)

    h_tags = re.findall(r'<h\d>', text)
    soup = BeautifulSoup(text)
    for h_tag in h_tags:
        for h in soup.find_all('h%s' % h_tag[-2]):
            text = text.replace(str(h), h.text.encode('utf-8'))

    return text


def cut_images(text):
    images = list()
    for i, img in enumerate(re.findall(r'<img[^>]*>|<image[^>]*>', text)):
        soup = BeautifulSoup(img)
        img_soup = soup.find_all('img') if 'img' in img else soup.find_all('image')
        images.append(str.strip(img_soup[0].get('src').encode('utf-8')))
        image = '(img%s)' % str(i+1)
        text = text.replace(img, image)
    text = text.replace('<img>', '')
    text = text.replace('</img>', '')

    return text, images


def handle_coords(text):
    indexes = list()
    locations = dict()

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

    coords = list()
    init_coords = find_coords(text)
    for coord in init_coords:
        if coord in coords:
            continue
        coords.append(coord)
    if coords:
        for coord in coords:
            i = 1 if not locations else len(locations.keys()) + 1
            coord_Y_G = make_Y_G_links(coord) + ' - <b>' + str(i) + '</b>'
            text = text.replace(coord, coord_Y_G)
            if unicode(i) not in locations.keys():
                indexes.append(i)
            locations[str(i)] = coord

    for rep in re.findall(r'\(link\d+\)', text):
        j = re.findall(r'\d+', rep)
        text = text.replace(rep, links[int(j[0])])

    return text, indexes


def make_Y_G_links(coord):
    lat = re.findall(r'\d\d\.\d{4,7}', coord)[0]
    long = re.findall(r'\d\d\.\d{4,7}', coord)[1]
    Y = '<a href="http://maps.yandex.ru/?text=%s,%s">[Y]</a>' % (lat, long)
    G = '<a href="https://maps.google.com/?daddr=%s,%s&t=m">[G]</a>' % (lat, long)
    # G = '<a href="https://www.google.com/maps/place/%s,%s">[G]</a>' % (lat, long)
    coord_Y_G = '<b>' + coord + '</b> ' + Y + ' ' + G
    return coord_Y_G


def reformat_links(text):
    links = re.findall(r'<A[^>]+>|<a[^>]+>', text)
    for link in links:
        soup = BeautifulSoup(link)
        text = text.replace(link, '<a href="' + str.strip(soup.find_all('a')[0].get('href').encode('utf-8')) + '">')
        text = text.replace('</A>', '</a>')
        text = text.replace('<A/>', '<a/>')
        text = text.replace('<a/>', '</a>')
    return text


def cut_extra_links_endings(text):
    a_opens = re.findall(r'<a[^>]+>', text)
    a_closings = re.findall(r'</a>', text)
    if len(a_closings) > len(a_opens):
        links = re.findall(r'<a\sh.+>.*</a>', text)
        for i, link in enumerate(links):
            cut_link = '(link%s)' % i
            text = text.replace(link, cut_link)
        text = text.replace('</a>', '')
        for i, link in enumerate(links):
            cut_link = '(link%s)' % i
            text = text.replace(cut_link, link)
    return text


def cut_links_change_small_symbol(text):
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
    text = text.replace('>', '&gt;')
    for i, link_index in enumerate(links_indexes):
        text = text.replace(link_index, links_text[i])
    return text, links, text_cut_links


def cut_tag(text, tag):
    tag_reps = re.findall(r'<%s[^>]*>|<%s[^>]*>' % (tag, tag.upper()), text)
    for tag_rep in tag_reps:
        text = text.replace(tag_rep, '')
    text = text.replace('</%s>' % tag, '')
    text = text.replace('</%s >' % tag, '')
    text = text.replace('</%s>' % tag.upper(), '')
    text = text.replace('</%s >' % tag.upper(), '')

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
        coords = str()
        coords_in_script = find_coords(str(script))
        for coord in coords_in_script:
            coords += '\r\nКорды из скрипта: ' + coord
        text = text.replace(str(script), coords)

    return text


def find_coords(text):
    coords = re.findall(r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                        r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', text)
    return coords


text, images, indexes = send_object_text(text)
telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo").send_message(45839899, text, parse_mode='HTML')
print text
