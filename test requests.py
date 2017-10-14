# -*- coding: utf-8 -*-
import re

t = re.search(r'b', 'yityutiubiuyitawtbaiuwytoiyaiwbaoiwytiab')
print t


# text = 'Уровень мечты Виталика. <a href="http://maps.yandex.ru/?text=54.125774,28.073387">[Y]</a> <a href="https://maps.google.com/?daddr=54.125774,28.073387&t=m">[G]</a> Он очень любит играть в покер! Кстати, если вспомнить правильную комбинацию, то колоду можно разложить на 13 наборов. И пусть число не счастливое, достаточно постучать по дереву и все наладится! <a href="http://d1.endata.cx/data/games/59668/kartavit750.png" target=_blank>карта</a> Подвал не играет. Сектора на карте отмечены. Рядом живут люди, не беспокойте их пожалуйста.'
# links = re.findall(r'<a[^>]+>', text)
# # pattern = r'<a[^>]+>'
# # links = re.findall(pattern, text)
# tags = re.findall(r'<..|..>|..>$|<$', text)
# for tag in tags:
#     if tag not in ['<b>', '</b', '<i>', '</i', '/b>', '/i>', '<a ', '</a', '/a>']\
#             + [re.search(r'..>', link).group() for link in links]:
#         parse = False
#     else:
#         parse = True
#
# print parse
