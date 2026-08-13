# -*- coding: utf-8 -*-
"""案件台帳で「確定」にならなかった4件をサイトから外し、件数表記を163件に直す。"""
import re, io, sys, datetime

P='index.html'; L='llms.txt'
s=open(P,encoding='utf-8').read()
before_li=len(re.findall(r'<li class="wrow', s))

DROP=['ビッグワン「こだわりの自家精米」CMソング ロングバージョン',
      '「琉Q大戦 はぶ×まん」OP「琉Qニコイチ」・ED「琉Q萌演歌」',
      '泡盛「あわもえ2」演歌（ミクガチ演歌ver.）',
      '琉球インタラクティブ 新サービス サウンドロゴ']
for name in DROP:
    pat = re.compile(r'[ \t]*<li class="wrow[^"]*"><span class="t">' + re.escape(name) + r'</span>.*?</li>\n')
    s, n = pat.subn('', s)
    assert n == 1, f'削除できなかった: {name} ({n}件ヒット)'

# --- CMリストの各グループ件数を数え直す ---
m = re.search(r'(<ul class="wlist clip" id="cm-list">)(.*?)(</ul>\s*</div>\s*<button class="wl-more")', s, re.S)
if not m:
    m = re.search(r'id="cm-list"(.*?)<button class="wl-more"', s, re.S)
block_start = s.index('id="cm-list"')
block_end = s.index('<button class="wl-more"')
block = s[block_start:block_end]

def fix_group(mo):
    head, cnt, tail, items = mo.group(1), mo.group(2), mo.group(3), mo.group(4)
    real = len(re.findall(r'<li class="wrow', items))
    return f'{head}{real}{tail}{items}'

new_block, ng = re.subn(
    r'(<span class="n">)(\d+)(件</span>\s*</div>\s*<ul>)(.*?)</ul>',
    lambda mo: fix_group(mo) + '</ul>', block, flags=re.S)
s = s[:block_start] + new_block + s[block_end:]

total = len(re.findall(r'<li class="wrow', new_block))
grp_sum = sum(int(x) for x in re.findall(r'<span class="n">(\d+)件</span>', new_block))
assert total == grp_sum, f'グループ合計 {grp_sum} と実数 {total} が合わない'

OLD, NEW = '167', str(total)
reps = [
 (f'<div class="num">{OLD}</div><div class="lbl">CM音楽・サウンドロゴ制作数</div>',
  f'<div class="num">{NEW}</div><div class="lbl">CM音楽・サウンドロゴ制作数</div>'),
 (f'CM音楽・サウンドロゴ<span class="wcount">{OLD}件</span>',
  f'CM音楽・サウンドロゴ<span class="wcount">{NEW}件</span>'),
 (f'手がけたCM音楽・サウンドロゴは{OLD}件です。',
  f'手がけたCM音楽・サウンドロゴは{NEW}件です。'),
 (f'CM実績 {OLD}件をすべて表示', f'CM実績 {NEW}件をすべて表示'),
 (f'CM音楽・サウンドロゴ{OLD}件', f'CM音楽・サウンドロゴ{NEW}件'),
]
for a,b in reps:
    if a in s: s = s.replace(a,b)
    else: print('  ※見つからず:', a[:40])

TODAY = datetime.date.today().isoformat()
s = re.sub(r'最終更新: <time datetime="[\d-]+">[^<]+</time>',
           f'最終更新: <time datetime="{TODAY}">{TODAY[:4]}年{int(TODAY[5:7])}月{int(TODAY[8:10])}日</time>', s)
s = re.sub(r'"dateModified": "[\d-]+"', f'"dateModified": "{TODAY}"', s)

open(P,'w',encoding='utf-8').write(s)

t=open(L,encoding='utf-8').read()
t=t.replace(f'2010年から2026年までに{OLD}件', f'2010年から2026年までに{NEW}件')
t=t.replace(f'CM音楽・サウンドロゴ {OLD}件', f'CM音楽・サウンドロゴ {NEW}件')
open(L,'w',encoding='utf-8').write(t)

print(f'li: {before_li} → {len(re.findall(chr(60)+"li class=..wrow", s))}')
print(f'CMリスト: {total}件')
print('グループ内訳:', re.findall(r'<div class="g">([^<]+)<span class="n">(\d+)件', new_block))
