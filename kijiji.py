# -*- coding: utf-8 -*-

import re
import requests
from structominer import Document, StructuredListField, TextField, URLField, IntField


class ConditionalURLField(URLField): _masquerades_ = URLField
class ConstructedURLField(TextField): _masquerades_ = TextField

class Listings(Document):
    listings = StructuredListField('//table[contains(@class, "regular-ad")]', structure=dict(
        id = TextField('.//td[contains(@class, "watchlist")]/div/@data-adid'),
        name = TextField('.//td[contains(@class, "description")]/a'),
        link = URLField('.//td[contains(@class, "description")]/a'),
        price = IntField('.//td[contains(@class, "price")]'),
        has_image = ConditionalURLField('.//td[contains(@class, "image")]//img'),
        posted_delay = IntField('.//td[contains(@class, "posted")]'),
        map_url = ConstructedURLField('.//td[contains(@class, "watchlist")]/div/@data-adid')
    ))

    @listings.name.preprocessor()
    def _clean_name_fractions(value, **kwargs):
        return map(lambda s: s.replace(u"½", u'1/2'), value)

    @listings.name.postprocessor()
    def _normalize_titles(value, **kwargs):
        value = value.lower()
        value = re.sub('(?<=\d)1/2', '-1/2', value) # 31/2 -> 3-1/2
        value = re.sub('(?<=\d) 1/2', '-1/2', value) # 3 1/2 -> 3-1/2
        value = re.sub('(?<=\d)\.5', '-1/2', value) # 3.5 -> 3-1/2
        return value

    @listings.price.preprocessor()
    def _extract_price(value, **kwargs):
        return value.split(',')[0]

    @listings.has_image.postprocessor()
    def _has_image(value, **kwargs):
        return 'placeholder' not in value

    @listings.posted_delay.preprocessor()
    def _extract_posted_delay_in_minutes(value, **kwargs):
        _, i, unit = value.rsplit(' ', 2)
        return int(i) * (60 if unit.startswith('h') else 1)

    @listings.map_url.postprocessor()
    def _construct_map_url_from_id(value, **kwargs):
        return "http://www.kijiji.ca/v-map-view.html?adId={0}&enableSearchNavigationFlag=true".format(value)

area = "ville-de-montreal"
price_from = 600
price_to = 900
url = "http://www.kijiji.ca/b-appartement-condo/{area}/c37l1700281?price={from_}.00__{to}.00".format(
    from_=price_from,
    to=price_to,
    area=area)
page = requests.get(url)

listings = Listings(page.content)

import json
print json.dumps(listings['listings'], indent=2)
