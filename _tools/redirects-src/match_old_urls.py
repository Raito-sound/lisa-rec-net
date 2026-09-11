import json,glob,re,difflib,unicodedata,urllib.parse,collections,os
S=str(__import__('pathlib').Path(__file__).resolve().parent)
ROOT=S+'/../..'
# URLs seen in search results but missing from Wayback (add from Search Console 404 report)
EXTRA={'/2015/11/san-a-kariyushi/':'/post/%E3%80%90cm%E7%B4%B9%E4%BB%8B%E3%80%91%E3%82%B5%E3%83%B3%E3%82%A8%E3%83%BC%E3%81%8B%E3%82%8A%E3%82%86%E3%81%97/'}
old=json.load(open(S+'/lisarec_old_urls.json'))
titles=json.load(open(S+'/lisarec_month_titles.json'))
for u,v in (json.load(open(S+'/old_titles.json')) if os.path.exists(S+'/old_titles.json') else {}).items():
    if v.get('title') and v['title'] not in ('ERR','(no title)'):
        titles.setdefault(u.rstrip('/').replace('https://','http://').replace('www.',''),v['title'])
posts=[json.load(open(f)) for f in glob.glob(ROOT+'/content/blog/*.json')]
bym=collections.defaultdict(list)
for p in posts: bym[p['published'][:7]].append(p)
for v in bym.values(): v.sort(key=lambda p:p['published'])
def norm(s):
    s=unicodedata.normalize('NFKC',s); s=re.sub(r'\s*[–|｜-]\s*リサレコ.*$','',s)
    return re.sub(r'[\s　「」『』【】（）()・:：,、。!！?？\-–—~〜/／&＆]','',s).lower()
idx=collections.defaultdict(list)
for p in posts: idx[norm(p['title'])].append(p)
def url(p): return '/post/'+urllib.parse.quote(p['slug'],safe='-._~')+'/'
M={ # ym: {slug: title fragment}
'2014-09':{'meltyangel_cd':'Melty Angel','shinkiitten':'心機一転','uniel_ost':'Exe:Late OST'},
'2014-10':{'furapanust14':'フラパンUST','tedokonlive':'ソロライブありがとう','varimon_kabocha':'カボチャ王','yaten-no-ori':'夜天の檻'},
'2014-11':{'coffee':'コーヒー','creators_night_photo':'写真のワークショップ','dengeki_fc':'FIGHTING CLIMAX','genkai':'限界は他人','homete_nobinai':'子どもなのにスゴイね','lisarec_ha_ongakuyadesu':'何屋かわからない','mini4':'ミニ四駆','pm5004':'PM5004','senkyo':'県知事候補','shingeki_dassyutu':'進撃の巨人','tsu':'「Tsu」','unrealengine4':'UnrealEngine4','wi2':'wi2','youtuber':'ユーチューバー'},
'2014-12':{'02':'衆院選CM','balloon':'バルーンアート','book':'本を読んでも','kinen':'他人の煙','letsnote':'レッツノート','sonbidakudaku2':'ゾンビだくだく','syounenin':'少年院','tdkn-xmas':'クリスマス会やります','tedocri':'クリスマス会ありがとう','yatatehajime':'矢立肇'},
'2015-01':{'akeome2015':'あけまして','rbc-occ':'【来兎】RBCiラジオ','varimon_taiwan':'ヴァリモン台湾版'},
'2015-02':{'majin-theme2':'新作テーマ','uniel':'海外版リリース'},
'2015-03':{'amazon':'Amazonで販売'},
'2015-04':{'key-15th-fescd':'Key 15th','koropan-2':'ころぱん リリース'},
'2015-05':{'junsyoku':'殉職刑事','majin-vita':'PSVITA版','unielst':'エスト』発表'},
'2015-06':{'lets-and-go-2':'レッツ'},
'2015-07':{'arc-revo':'あーくれぼ','dengeki-fc-ignition':'IGNITION'},
'2015-10':{'animaxmajin2':'ANIMAX'},
'2015-12':{'dengekifc-ignition':'IGNITION'},
'2016-04':{'black-factory':'ブラック工場','mbaacc_steam':'STEAM版メルティ','oshimatsu-quiz':'推し松クイズ','sanreko5':'サンレコ','totoko':'トト子'},
'2016-05':{'osomatsuvoice':'ボイス実装'},
'2016-06':{'rudymical':'ルディミカル','tamanekowars':'たまねこ','uni_steam':'STEAM版 UNDER'},
'2016-07':{'bosyuu-2':'募集'},
'2016-11':{'bakushu':'麦酒夜宴','hesowo20':'Ver.2.0'},
'2016-12':{'brave':'ブレイブダンジョン サウンドトラック'},
'2017-03':{'4gamer-tgms2017':'東京ゲーム音楽ショーレポート','audition':'オーディション'},
'2017-05':{'gensoumaroku-w':'東方幻想魔録W','majin-gaiden':'ルディミカル','unist-ps4':'OPムービー'},
'2017-06':{'okigin-cash':'キャッシュカード','voez-majin01':'碧い陽炎'},
'2017-07':{'anic':'aniC','hot_okinawa':'HOT沖縄'},
'2017-08':{'creators-night-vol-22':'Creators Night','horuradi1':'ホルラジ出演1回目'},
'2017-09':{'bravedungeon':'COMBAT','horuradi2':'ホルラジ2回目'},
'2017-10':{'bd-sena':'主題歌を聖奈','san-a-happy':'ハッピーシニア','shimakutuba':'しまくとぅばであそぼ'},
'2017-11':{'ikoku':'異世界の約束'},
'2017-12':{'annouimo':'安納芋','dragonfang-z':'ドラゴンファングZ','homepage':'サイトリニューアル','ovm2017':'第8回オキナワベンチャー','rxn':'RXN -雷神-'},
'2018-01':{'kigyouhukusi_kyousaikai':'企業福祉共済会'},
'2018-02':{'indivisible':'効果音担当','osusume_game_cd':'タワレコ','voez-kikan':'Ver1.4'},
'2018-03':{'san-a-daikansyasai':'大感謝祭','san-a-kariyushi2018':'2018レディース','san-a-kariyushi2018-2':'放送開始です','san-a-nikoniko':'にこにこデー'},
'2018-04':{'bbtag':'BLAZBLUE','esports':'eスポーツ','kikan':'科学者の帰還','koshon':'コション','million':'ミリオン','roukins':'ろうきん新テレビ'},
'2018-05':{'saikikusuo':'斉木楠雄'},
'2018-06':{'happiness':'HAPPINESS','jikaseimai':'自家製米','rxn-ost':'オリジナルサウンドトラック'},
'2018-07':{'okinawatimes':'沖縄タイムスに掲載','tousenkyo':'唐船峡'},
'2018-08':{'okinawanokowaihanashi':'プライムビデオ'},
'2018-09':{'tgs2018':'東京ゲームショウに出展'},
'2018-10':{'au-kantan':'かんたん予約','job-calorie':'ジョブカロリ','tomato':'とまとハウジング'},
'2018-11':{'huistenbosch':'ハウステンボス','okimu':'おきみゅー','petbox2018':'PETBOX'},
'2018-12':{'southeast-botanical':'東南植物楽園'},
'2019-01':{'2-1':'ツーワン'},
'2019-02':{'asuka2019':'あすか120%','daichi-2':'大知建設','evo2019':'EVO2019','kaohsiung':'高雄','marokuw':'東方幻想魔録W','osomatsucd':'全イラスト集','rcworks':'RCワークス','taipeigameshow':'台北ゲームショウ','tgms2019':'2019に出展','tgms2019-2':'2019出展致しました'},
'2019-03':{'study':'Study','twc':'テラ・ウェブ'},
'2019-04':{'2d-swamp':'2次元SWAMP','cell':'CELL','pptp':'ポプテピピック','sana':'ファッションショー','shimpo-esports-fes2019':'eスポ'},
'2019-05':{'akaiyami':'赤い闇','aoikagerou':'【歌詞】碧い陽炎','car':'自動車税','fukuju':'麩久寿','linear48':'LINEAR','lisani37':'リスアニ','live_blooddrain':'【LIVE映像】Blood Drain','live_unist':'【LIVE映像】Unknown Actor','unknown-actor':'【歌詞】Unknown Actor'},
'2019-06':{'blooddrain':'【歌詞】Blood Drain','nyansore':'にゃんそーれ','okiko2019':'縄文と沖縄','sakae-tosou':'さかえ塗装','study-2':'ミニアルバム'},
'2019-07':{'mb':'【歌詞】MELTY BLOOD','meltyblood':'【歌詞】MELTY BLOOD'},
'2019-08':{'aoi-kagerou':'碧い陽炎','evo2019_1':'EVO観戦','unicl-r':'[cl-r]','y-kinjo':'金城'},
'2019-09':{'watering':'Watering Maze'},
'2019-10':{'2019gameshow':'東京ゲームショウ出展','majimun':'マジムン','study2ndsingle':'Can now'},
'2019-11':{'2019ovm':'第10回','amahaku':'天野ゲーム','cheerup':'Cheer up','indivisible-2':'IndivisibleのSE','majin1_switch':'Swith版','otonafashionshow':'オトナファッション','uniclr_11':'発売日が決定'},
'2019-12':{'gamemusic2019':'2019年この1枚','nikopuchitv':'ニコ☆プチ','pokemon-kids-tv':'We Wish','post-2253':'パラダイスジャム'},
'2020-01':{'bouhuri':'防御力'},
'2020-02':{'evo2020':'EVO2020','pokemon-yuki':'『ゆき』'},
'2020-03':{'2020tgms':'東京ゲーム音楽ショー'},
'2020-06':{'ryubo-store':'りうぼう','sakura-mediness':'さくらメディネス'},
'2020-11':{'parcocity202011':'PARCO CITY'},
'2020-12':{'fgo_202012':'Fate/Grand Order','iias202012':'イーアス','sk8_202012':'劇中歌'},
'2021-02':{'pangry':'パングリー','sk8_ost':'サウンドトラック','yapparihonda':'やっぱりHONDA'},
'2021-04':{'lumina_01':'TYPE LUMINA'},
'2021-05':{'jaokinawa2105':'JAおきなわ','kingdomdash':'キングダムDASH'},
'2021-07':{'mbtl_0930_pre':'発売日が決定','skull_umbrella_pre':'アンブレラ'},
'2021-09':{'hobohobo':'ほぼほぼ'},
'2021-11':{'hadomu202111':'ハドム'},
'2022-09':{'post-2562':'りゅうせき'},
'2022-11':{'resortech-expo-2022-in-okinawa':'ResorTech'},
'2023-03':{'post-2562':'東京ゲーム音楽ショー2023','post-2638':'ブロマイド'},
'2024-03':{'parco-city-spring':'SPRING'},
'2024-08':{'parco-city-new-shop-open-cm':'NEW SHOP OPEN'},
}
years={os.path.basename(d) for d in glob.glob(ROOT+'/blog/archive/*') if os.path.isdir(d)}
mapping={}; how=collections.Counter(); unresolved=[]
groups=collections.defaultdict(list)
for u in old:
    m=re.match(r'https?://(?:www\.)?lisa-rec\.net/(\d{4})/(\d{2})/([^/]+)/?$',u)
    groups[m.group(1)+'-'+m.group(2)].append((m.group(3),u))
for ym,items in groups.items():
    used=set(); pending=[]
    for slug,u in items:
        path=f'/{ym[:4]}/{ym[5:]}/{slug}/'
        key=u.rstrip('/').replace('https://','http://').replace('www.','')
        t=titles.get(key); pick=None
        if t:
            n=norm(t); c=idx.get(n) or [p for b in difflib.get_close_matches(n,list(idx.keys()),n=3,cutoff=0.8) for p in idx[b]]
            same=[p for p in c if p['published'][:7]==ym] or c
            if same and all(p['slug']==same[0]['slug'] for p in same): pick=same[0]; how['title']+=1
        if not pick and slug in M.get(ym,{}):
            frag=M[ym][slug]; c=[p for p in bym[ym] if frag.lower() in unicodedata.normalize('NFKC',p['title']).lower()]
            if c: pick=c[0]; how['manual']+=1
            else: print('MANUAL MISS',ym,slug,frag)
        if pick: mapping[path]=url(pick); used.add(pick['slug'])
        else: pending.append((slug,path))
    # numeric slugs ↔ remaining posts in date order
    rem=[p for p in bym[ym] if p['slug'] not in used]
    nums=sorted([(int(re.sub(r'\D','',s)),s,path) for s,path in pending if re.fullmatch(r'post-\d+|\d+',s)])
    if nums and len(nums)==len(rem):
        for (_,s,path),p in zip(nums,rem): mapping[path]=url(p); how['numeric-order']+=1
        pending=[(s,path) for s,path in pending if not re.fullmatch(r'post-\d+|\d+',s)]
    elif len(rem)==1 and pending:
        for s,path in pending: mapping[path]=url(rem[0]); how['only-post']+=1
        pending=[]
    for s,path in pending:
        y=ym[:4]; mapping[path]=f'/blog/archive/{y}/' if y in years else '/blog/'; how['fallback']+=1; unresolved.append(path)
print(dict(how),'total',len(mapping))
print('fallback:',unresolved)
mapping.update(EXTRA)
json.dump(dict(sorted(mapping.items())),open(ROOT+'/content/redirects.json','w'),ensure_ascii=False,indent=1)
