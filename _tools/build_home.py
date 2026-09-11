#!/usr/bin/env python3
"""Render lisa-rec.net's home page in Japanese (index.html) and English (en/index.html)
from templates/home.html + templates/works-list.html + content/i18n/home.{ja,en}.json."""
from pathlib import Path
from html import escape
import json, re

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://lisa-rec.net'
PERSON = 'https://raito.studio/#person'
ORG = SITE + '/#org'
DATE = '2026-09-11'
SAME_AS_PERSON = ['https://raito.studio/', 'https://www.wikidata.org/wiki/Q11523677', 'https://ja.wikipedia.org/wiki/%E6%9D%A5%E5%85%8E',
                  'https://vgmdb.net/artist/1585', 'https://www.imdb.com/name/nm9311908/',
                  'https://open.spotify.com/artist/4gvNo6XIRTD2N0l75sY6II', 'https://www.youtube.com/channel/UCuUUK_sojL65BDL2AK7yWNw']
AWARDS_JA = ['沖縄広告賞 テレビ15秒CM部門 銅賞（2022年・第40回沖縄広告協会広告賞／ぐしけんパン「パングリー」TVCM 楽曲制作）',
             '沖縄広告賞 テレビ15秒CM部門 銅賞（2019年／沖縄県立博物館・美術館 特別展「縄文と沖縄」TVCM 音楽）',
             '沖縄広告賞 テレビCM15秒部門 銅賞（2017年／琉球新報 TVCM BGM）']
AWARDS_EN = ['Okinawa Advertising Awards, TV 15-second commercial category, Bronze (2022; Gushiken Pan “Pangry” TV commercial music)',
             'Okinawa Advertising Awards, TV 15-second commercial category, Bronze (2019; Okinawa Prefectural Museum & Art Museum “Jomon and Okinawa” TV commercial music)',
             'Okinawa Advertising Awards, TV 15-second commercial category, Bronze (2017; Ryukyu Shimpo TV commercial music)']


def jsonld(lang, url, s):
    ja = lang == 'ja'
    faq = [{'@type': 'Question', 'name': re.sub(r'<[^>]+>', '', f['q']), 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'<[^>]+>', '', f['a'])}} for f in s['faq']]
    data = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Organization', '@id': ORG, 'name': '株式会社リサレコ' if ja else 'Lisa-Rec Inc.',
         'alternateName': ['リサレコ', 'Lisa-Rec Co.,Ltd', 'Lisa-Rec Inc.', 'Lisa-Rec'] if ja else ['株式会社リサレコ', 'リサレコ', 'Lisa-Rec Co.,Ltd', 'Lisa-Rec'],
         'url': SITE + '/', 'email': 'contact@lisa-rec.com', 'foundingDate': '2010-03',
         'description': ('株式会社リサレコ（Lisa-Rec Co.,Ltd）は、2010年3月に設立された沖縄県那覇市の音楽制作会社です。代表取締役は作曲家の久場超（活動名義: 来兎 / Raito）です。CM音楽、サウンドロゴ、施設・空間の音楽、ゲーム・アニメ音楽を企画・制作しています。2010年から2026年までに150件以上のCM音楽・サウンドロゴを手がけ、沖縄広告賞のテレビCM部門で3度の銅賞受賞作に参加しています。これらのCM音楽・サウンドロゴはすべて代表の来兎（久場 超）が作曲しています。現在、国内案件は株式会社リサレコ、海外案件は Raito.studio で受け付けています。'
                         if ja else 'Lisa-Rec Inc. (株式会社リサレコ, Lisa-Rec Co.,Ltd) is a music production company founded in March 2010 in Naha, Okinawa, Japan. Its CEO is composer Masaru Kuba, credited as Raito (来兎). The company plans and produces commercial music, sound logos, music for facilities and spaces, and game and anime music. From 2010 to 2026 it has produced more than 150 commercials and sound logos, three of which won bronze awards in the TV commercial category of the Okinawa Advertising Awards. All of these commercials and sound logos were composed by Raito (Masaru Kuba). Work within Japan is handled by Lisa-Rec Inc.; international work through Raito.studio.'),
         'address': {'@type': 'PostalAddress', 'addressCountry': 'JP', 'addressRegion': '沖縄県' if ja else 'Okinawa', 'addressLocality': '那覇市' if ja else 'Naha', 'streetAddress': '久茂地1-1-1 9階' if ja else '9F, 1-1-1 Kumoji'},
         'founder': {'@id': PERSON}, 'employee': {'@id': PERSON},
         'knowsAbout': ['AIボーカル', 'CM音楽', 'MA（整音）', 'TVアニメ劇伴', 'アニメ音楽', 'ゲーム音楽', 'コマーシャルソング', 'サウンドロゴ', 'ナレーション収録', '主題歌制作', '劇伴', '効果音', '対戦格闘ゲーム音楽', '施設音楽', '空間音楽'] if ja else
                       ['Commercial music', 'Sound logos', 'Sonic branding', 'Music for facilities and spaces', 'Game music', 'Fighting game music', 'Anime music', 'Theme songs', 'Sound effects', 'Audio post-production', 'Narration recording', 'AI vocals'],
         'award': AWARDS_JA if ja else AWARDS_EN, 'areaServed': {'@type': 'Country', 'name': '日本' if ja else 'Japan'},
         'slogan': 'その場所に、まだない音を' if ja else 'Sound that stays in Okinawa’s memory'},
        {'@type': 'Person', '@id': PERSON, 'name': '来兎' if ja else 'Raito', 'alternateName': ['らいと', 'Raito', '久場 超', 'Masaru Kuba'] if ja else ['来兎', 'らいと', 'RAITO', 'Masaru Kuba', '久場 超'],
         'jobTitle': '作曲家 / 株式会社リサレコ 代表取締役' if ja else 'Composer / Founder and CEO of Lisa-Rec Inc.', 'url': 'https://raito.studio/',
         'image': SITE + '/assets/profile/raito-profile.jpg', 'sameAs': SAME_AS_PERSON, 'worksFor': {'@id': ORG}, 'knowsLanguage': ['ja', 'en'], 'award': AWARDS_JA if ja else AWARDS_EN},
        {'@type': 'WebSite', '@id': SITE + '/#website', 'url': SITE + '/', 'name': '株式会社リサレコ' if ja else 'Lisa-Rec Inc.', 'inLanguage': ['ja', 'en'], 'publisher': {'@id': ORG}},
        {'@type': 'WebPage', '@id': url + '#webpage', 'url': url, 'name': s['title'], 'description': s['meta_description'], 'isPartOf': {'@id': SITE + '/#website'},
         'about': {'@id': ORG}, 'inLanguage': lang, 'dateModified': DATE},
        {'@type': 'FAQPage', '@id': url + '#faq', 'isPartOf': {'@id': url + '#webpage'}, 'mainEntity': faq},
    ]}
    return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2).replace('</', '<\\/') + '\n</script>'


def render(lang):
    s = json.loads((ROOT / 'content' / 'i18n' / f'home.{lang}.json').read_text(encoding='utf-8'))
    ja = lang == 'ja'
    url = SITE + ('/' if ja else '/en/')
    root = '' if ja else '../'
    cur = ' aria-current="page"'
    values = dict(s)
    values.update({
        'lang': lang, 'url': url, 'root': root,
        'alternates': (f'<link rel="canonical" href="{url}">\n<link rel="alternate" hreflang="ja" href="{SITE}/">\n'
                       f'<link rel="alternate" hreflang="en" href="{SITE}/en/">\n<link rel="alternate" hreflang="x-default" href="{SITE}/">'),
        'og_locale': f'<meta property="og:locale" content="{"ja_JP" if ja else "en_US"}">\n<meta property="og:locale:alternate" content="{"en_US" if ja else "ja_JP"}">',
        'jsonld': jsonld(lang, url, s),
        'lang_switch': (f'<nav class="lang-switch" aria-label="{"言語" if ja else "Language"}">'
                        f'<a href="{root}en/" lang="en" hreflang="en" data-lang-switch="en"{"" if ja else cur}>EN</a><span aria-hidden="true">/</span>'
                        f'<a href="{root}index.html" lang="ja" hreflang="ja" data-lang-switch="ja"{cur if ja else ""}>日本語</a></nav>'),
        'faq_items': '\n'.join(f'    <div class="faq-item fade">\n      <h3>{f["q"]}</h3>\n      <p>{f["a"]}</p>\n    </div>' for f in s['faq']),
        'works_list': (ROOT / 'templates' / 'works-list.html').read_text(encoding='utf-8'),
    })
    html = (ROOT / 'templates' / 'home.html').read_text(encoding='utf-8')
    for _ in range(3):
        html = re.sub(r'\{\{([a-z_0-9]+)\}\}', lambda m: values[m.group(1)], html)
    assert '{{' not in html, re.findall(r'\{\{[^}]+\}\}', html)[:5]
    dest = ROOT / ('index.html' if ja else 'en/index.html')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    render('ja'); render('en')
    print('Rendered index.html and en/index.html')
