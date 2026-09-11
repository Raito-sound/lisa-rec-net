"""One-off: turn index.html into templates/home.html + templates/works-list.html + content/i18n/home.ja.json."""
from pathlib import Path
import json, re
src = Path('index.html').read_text(encoding='utf-8')
ja = {}
def key(k, text, count=None):
    global src
    assert text in src, (k, text[:80])
    if count is not None: assert src.count(text) == count, (k, src.count(text))
    src = src.replace(text, '{{'+k+'}}'); ja[k] = text

# --- works list block → separate fragment (shared by both languages) ---
a0 = src.index('  <div class="wcat">\n    <h3 class="serif wcat-title">CM音楽')
a1 = src.index('</section>', a0)
fragment = src[a0:a1]
src = src[:a0] + '{{works_list}}\n' + src[a1:]
# keyed headings inside the fragment
frag_keys = [
 ('wl_cm_title','CM音楽・サウンドロゴ<span class="wcount">150件以上</span>'),
 ('wl_cm_intro','15秒で覚えてもらうための音を、企画意図から逆算して作ります。2010年から2026年までに手がけたCM音楽・サウンドロゴは150件以上。掲載作品はすべて、代表の作曲家・来兎（本名：久場 超）が作曲・制作しています。'),
 ('wl_more','CM実績をすべて表示'),
 ('wl_space_title','施設・空間の音楽<span class="wcount">7件</span>'),
 ('wl_game_title','ゲーム・アニメの音楽<span class="wcount">17件</span>'),
 ('g_retail','流通・小売'),('g_food','飲食・食品'),('g_media','メディア・放送'),('g_housing','住宅・不動産・建設'),('g_edu','教育・医療・サービス'),
 ('g_public','行政・自治体・公共'),('g_finance','金融・保険'),('g_infra','通信・エネルギー'),('g_auto','自動車'),('g_other','その他'),
]
for k,t in frag_keys:
    if k.startswith('g_'):
        needle = f'<div class="g">{t}<span'
        assert needle in fragment, k
        fragment = fragment.replace(needle, f'<div class="g">{{{{{k}}}}}<span', 1); ja[k] = t
    else:
        assert t in fragment, k
        fragment = fragment.replace(t, '{{'+k+'}}', 1); ja[k] = t
m = re.search(r'<p class="cat-intro">人がその場所で.*?</p>', fragment, re.S); assert m
fragment = fragment.replace(m.group(0), '<p class="cat-intro">{{wl_space_intro}}</p>'); ja['wl_space_intro'] = m.group(0)[len('<p class="cat-intro">'):-len('</p>')]
m = re.search(r'<p class="cat-intro">『<span class="nowrap">MELTY BLOOD.*?</p>', fragment, re.S); assert m
fragment = fragment.replace(m.group(0), '<p class="cat-intro">{{wl_game_intro}}</p>'); ja['wl_game_intro'] = m.group(0)[len('<p class="cat-intro">'):-len('</p>')]
fragment = fragment.replace('件</span>', '{{count_suffix}}</span>')
ja['count_suffix'] = '件'
Path('templates/works-list.html').write_text(fragment, encoding='utf-8')

# --- head ---
src = src.replace('<html lang="ja">','<html lang="{{lang}}">')
key('title','株式会社リサレコ｜CM音楽・サウンドロゴ・施設音楽の制作会社（沖縄・那覇）')
m = re.search(r'<meta name="description" content="([^"]+)">', src); key('meta_description', m.group(1))
src = src.replace('<link rel="canonical" href="https://lisa-rec.net/">','{{alternates}}')
src = src.replace('<meta property="og:site_name" content="株式会社リサレコ">','<meta property="og:site_name" content="{{site_name}}">'); ja['site_name']='株式会社リサレコ'
src = src.replace('<meta property="og:locale" content="ja_JP">','{{og_locale}}')
src = src.replace('<meta property="og:url" content="https://lisa-rec.net/">','<meta property="og:url" content="{{url}}">')
m = re.search(r'<meta property="og:description" content="([^"]+)">', src); key('og_description', m.group(1))
src = re.sub(r'<script type="application/ld\+json">.*?</script>\n', '{{jsonld}}\n', src, count=1, flags=re.S)
src = src.replace('<link rel="stylesheet" href="site-refresh.css?v=fb1e31f629">','<link rel="stylesheet" href="{{root}}site-refresh.css?v=lang-20260911">\n<script src="{{root}}lang.js" defer></script>')
# --- paths ---
for a,b in [('src="logo.png"','src="{{root}}logo.png"'),('src="assets/','src="{{root}}assets/'),('srcset="assets/','srcset="{{root}}assets/'),
            (', assets/',', {{root}}assets/'),('href="blog/index.html"','href="{{root}}blog/index.html"'),('href="post/','href="{{root}}post/')]:
    assert a in src, a; src = src.replace(a,b)
# --- header ---
key('skip','本文へスキップ')
key('wordmark_aria','株式会社リサレコ トップ')
src = src.replace('alt="株式会社リサレコ" width="1946"','alt="{{site_name}}" width="1946"')
key('menu','メニュー <span aria-hidden="true">＋</span>')
key('nav_aria','メインナビゲーション')
key('nav','<a href="#works">沖縄の実績</a>\n    <a href="#awards">受賞</a>\n    <a href="#global">世界実績</a>\n    <a href="#company">会社情報</a>\n    <a href="{{root}}blog/index.html">ブログ</a>\n    <a class="mobile-contact" href="#contact">制作のご相談 ↗</a>')
src = src.replace('  <a class="nav-contact" href="#contact">制作のご相談 <span aria-hidden="true">↗</span></a>','  {{lang_switch}}\n  <a class="nav-contact" href="#contact">{{contact_label}}</a>'); ja['contact_label']='制作のご相談 <span aria-hidden="true">↗</span>'
# --- hero ---
key('hero_h1','<span>沖縄の記憶に、</span><br><em>音を刻む。</em>')
key('hero_def','<span>作曲家・来兎が率いる、</span><span>沖縄・那覇の音楽制作会社。</span>')
key('hero_lead','ぐしけんパン「パングリー」、沖縄ホンダ「まるまるセット」。<br>暮らしの中で何度も聴かれてきた音を、沖縄・那覇から。')
key('hero_actions','<a class="primary" href="#works">制作実績を見る <span aria-hidden="true">↗</span></a><a href="#services">私たちにできること <span aria-hidden="true">↓</span></a>')
key('panel_aria','リサレコ。沖縄から広がる音づくり。')
key('panel_tag','音楽をつくる。記憶に残る。')
key('stats_aria','沖縄での主な実績数値')
key('stats_intro','暮らしに届く音を、ひとつずつ。')
key('stat1','CM音楽・サウンドロゴ</div>')
key('stat2','企業・団体・ブランド</div>')
# --- showcase ---
key('works_h2','沖縄で知られている、<br>あの音。')
key('works_p','CMの音は、背景ではありません。<br>企業の名前と一緒に思い出される、ブランドの顔です。')
key('c1_alt','ぐしけんパン「パングリー」TVCMの画面')
key('c1_body','<h3>パングリー</h3><div class="feature-copy"><strong>見ても、聴いても、忘れない。</strong><p>ぐしけんパン「みんなでパングリー」篇TVCMの楽曲を制作。2022年沖縄広告賞テレビ15秒CM部門銅賞。</p>')
key('c1_link','aria-label="パングリーの制作記事を読む">制作記事を読む <span aria-hidden="true">↗</span>')
key('c2_alt','サンエー「かりゆしウェア」TVCMの画面')
key('c2_body','<h3>かりゆしウェア</h3><div class="feature-copy"><strong>沖縄の夏の定番に、口ずさめる音を。</strong><p>サンエーのかりゆしウェアキャンペーンCM楽曲。2014年の制作後、新アレンジへ発展した代表作。</p>')
key('c2_link','aria-label="かりゆしウェアの制作記事を読む">制作記事を読む <span aria-hidden="true">↗</span>')
key('c3_alt','沖縄ホンダ「まるまるセット」TVCMの画面')
key('c3_body','<h3>まるまるセット</h3><div class="feature-copy"><strong>一度聴けば、踊りだしたくなる。</strong><p>TEMPURA KIDZを起用し、フル・60・30・15秒を制作。琉球新報の連載でも楽曲が紹介された。</p>')
key('c3_link','aria-label="まるまるセットの制作記事を読む">制作記事を読む <span aria-hidden="true">↗</span>')
# --- awards ---
key('awards_h2','沖縄広告賞、3度。')
key('awards_p','耳に残るだけではない。企画と映像の価値を引き上げ、広告そのものを強くする音を。')
key('aw1','<strong>パングリー</strong>'); key('aw2','<strong>縄文と沖縄</strong>'); key('aw3','<strong>琉球新報 TVCM BGM</strong>')
# --- services ---
key('services_label','<span>制作領域</span><small>SERVICES</small>')
key('services_intro','株式会社リサレコが対応している制作業務です。作曲だけでなく、収録・仕上げ・整音まで自社スタジオで一貫して行えます。')
for i,(h,p) in enumerate([
 ('CM音楽・サウンドロゴ','テレビCM・ラジオCM・WEB動画の楽曲、コマーシャルソング、企業や商品のサウンドロゴ。15秒・30秒・60秒の尺調整、インスト版やカラオケ版の書き分けまで対応します。'),
 ('施設・空間の音楽','商業施設・観光施設の常設BGM、館内映像やプロジェクション用の音楽。4.0chサラウンドなどマルチチャンネル仕様の制作実績もあります。'),
 ('ゲーム・アニメの音楽','対戦格闘ゲームのBGM・効果音、TVアニメの劇伴・主題歌。『MELTY BLOOD』『UNDER NIGHT IN-BIRTH』シリーズ、TVアニメ『SK∞ エスケーエイト』など、世界各国で配信されるタイトルを1997年から手がけています。'),
 ('歌唱・ナレーション収録','ボーカリストやナレーターの人選・手配から、自社スタジオでの収録、ミックスまで。タレント・アーティスト起用の収録ディレクションも行います。'),
 ('MA・整音・効果音','ドラマ・テレビ番組・企業PVの整音（MA）、効果音の制作と配置、ラウドネス調整。映像の仮編集をお預かりして仕上げます。'),
 ('AIボーカル・AI音声の活用','AIボーカルと人の歌声を重ねる、AI音声でナレーションのバリエーションを作るなど、実際にオンエアされたCMでの運用実績があります。用途に応じて人の歌との使い分けを提案します。'),
],1):
    key(f'svc{i}', f'<h3>{h}</h3>\n      <p>{p}</p>')
# --- brands ---
key('brands_label','<span>主な制作先</span><small>BRANDS</small>')
key('brands_note','敬称略／一部抜粋')
key('brands_intro','株式会社リサレコが音楽を手がけたCM・施設の広告主および事業主です。制作は広告代理店・制作会社を通じたご依頼を中心にお受けしています。')
# --- global ---
key('global_h2','沖縄で選ばれる音は、<br>世界でも届く。')
key('global_p','地元CMで培った「一度で伝わる」設計力と、長く愛される作品をつくる技術。その両方が、株式会社リサレコの音の強さです。')
key('global_aria','世界での主な実績')
key('global_proof','<div><strong>1億<small>回以上</small></strong><span>音楽配信 総再生数</span></div><div><strong>29<small>年</small></strong><span>作曲活動歴</span></div><div><strong class="proof-long">2,000万<small>回以上</small></strong><span>1曲の再生数</span></div>')
key('g2_note','2,000万回以上 / 1曲')
# --- artist ---
key('artist_label','<span>代表・作曲家</span><small>COMPOSER</small>')
key('artist_alt','作曲家・来兎（株式会社リサレコ代表）')
key('artist_name','<h3 class="serif fade">来兎</h3>')
key('artist_role','COMPOSER / 株式会社リサレコ代表')
m = re.search(r'<div class="artist-bio fade">\n(.*?)\n    </div>', src, re.S); key('artist_bio', m.group(1))
# --- archive headings ---
key('archive_label','<span>制作実績</span><small>WORKS</small>')
key('archive_note','順不同・敬称略。CM音楽・サウンドロゴ、施設・空間の音楽は、すべて来兎（久場 超）が作曲・制作')
# --- faq ---
key('faq_label','<span>よくある質問</span><small>FAQ</small>')
m = re.search(r'<div class="faq-list">\n(.*?)\n  </div>\n</section>', src, re.S); assert m
src = src.replace(m.group(1), '{{faq_items}}')
items = re.findall(r'<h3>(.*?)</h3>\n      <p>(.*?)</p>', m.group(1), re.S)
ja['faq'] = [{'q': q, 'a': a} for q, a in items]
# --- company / contact / footer ---
key('company_label','<span>会社情報</span><small>COMPANY</small>')
key('company_dl','<div><dt>社名</dt><dd>株式会社リサレコ（Lisa-Rec Co.,Ltd）</dd></div>\n    <div><dt>代表</dt><dd>代表取締役 久場 超（作曲家・来兎）</dd></div>\n    <div><dt>設立</dt><dd>2010年3月</dd></div>\n    <div><dt>所在地</dt><dd>沖縄県那覇市久茂地1-1-1 9階</dd></div>\n    <div><dt>事業内容</dt><dd>CM音楽・サウンドロゴ、施設・空間のための音楽、ゲーム・アニメ音楽の企画制作</dd></div>')
key('contact_head','<span>制作のご相談</span><small>CONTACT</small>')
src = src.replace('<a class="mail" href="mailto:contact@lisa-rec.com">contact@lisa-rec.com<span aria-hidden="true">↗</span></a>','{{contact_block}}')
ja['contact_block'] = '<a class="mail" href="mailto:contact@lisa-rec.com">contact@lisa-rec.com<span aria-hidden="true">↗</span></a>'
key('footer_info','<span>株式会社リサレコ｜代表: 久場 超（来兎）｜2010年3月設立</span>\n    <span>沖縄県那覇市久茂地1-1-1 9階</span>\n    <a href="{{root}}blog/index.html">ブログ</a>\n    <span class="updated">最終更新: <time datetime="2026-08-29">2026年8月29日</time></span>')
key('js_collapse',"'CM実績を折りたたむ'"); key('js_expand',"'CM実績をすべて表示'")
for must in ['{{jsonld}}','{{alternates}}','{{lang_switch}}','{{works_list}}','{{faq_items}}','{{root}}lang.js']: assert must in src, must
Path('templates/home.html').write_text(src, encoding='utf-8')
Path('content/i18n/home.ja.json').write_text(json.dumps(ja, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
print('keys', len(ja))
