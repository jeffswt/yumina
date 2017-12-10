
import bs4
import json
import os
import re
import requests
import sqlite3

from . import renderer

def get_webpage(*args, **kwargs):
    """ get_webpage(...) -- request webpage content / text """
    return requests.get(*args, **kwargs).text.encode('ISO-8859-1').decode('utf-8')

def map_num(s):
    """ map_num(str) -- change all full-width characters to half-width. """
    s = s.replace('０', '0')\
         .replace('１', '1')\
         .replace('２', '2')\
         .replace('３', '3')\
         .replace('４', '4')\
         .replace('５', '5')\
         .replace('６', '6')\
         .replace('７', '7')\
         .replace('８', '8')\
         .replace('９', '9')\
         .replace('\u3000', ' ')
    return s

def get_chapter_list(web_id):
    sel_1 = r'<div class="chapter_title">.*?</div>'
    sel_2 = r'<dd class="subtitle">\n<a href="/%s/\d+/">.*?</a>\n</dd>' % web_id
    q1 = map_num(get_webpage('http://ncode.syosetu.com/%s/' % web_id))
    q2 = re.findall('(%s|%s)' % (sel_1, sel_2), q1)
    q3 = []
    for i in q2:
        if re.findall(sel_1, i) != []:
            sel_3 = r'^<div class="chapter_title">第(\d+)章 (.*?)</div>$'
            j = int(re.sub(sel_3, r'\1', i))
            k = re.sub(sel_3, r'\2', i)
            q3.append(('chapter_title', j, k))
        else:
            sel_3 = r'^<dd class="subtitle">\n<a href="/%s/(\d+)/">(.*?)</a>\n</dd>$' % web_id
            k = int(re.sub(sel_3, r'\1', i))
            l = re.sub(r'^[＃#].*? (.*?)$', r'\1', re.sub(sel_3, r'\2', i))
            q3.append(('subtitle', k, l))
    return q3

def get_chapter(web_id, chap_id):
    q1 = map_num(get_webpage('http://ncode.syosetu.com/%s/%d/' % (web_id, chap_id)))
    q2 = bs4.BeautifulSoup(q1, 'html5lib')
    q3 = q2.find_all(id='novel_honbun')[0].text
    # stylize paragraphs
    q3 = re.sub(r'\n +', r'\n', q3)
    q3 = re.sub(r'\n\n+', r'\n\n', q3)
    q3 = re.sub(r'(^\n+|\n+$)', r'', q3)
    # split into lines
    q4 = q3.split('\n')
    q5 = []
    for i in q4:
        if re.findall(r'^ *$', i) != []:
            q5.append(('break',))
        else:
            q5.append(('line', [('regular', i.replace(' ', ''))]))
    return q5

class SyosetuDatabase:
    def __init__(self, filename, syosetu_id, force_clear=False):
        found = os.path.exists(filename)
        self.base = sqlite3.connect(filename)
        self.cur = self.base.cursor()
        self.sid = syosetu_id
        if not found or force_clear:
            self.cur.execute("DROP TABLE IF EXISTS toc;")
            self.cur.execute("DROP TABLE IF EXISTS cont;")
            self.cur.execute("""
                CREATE TABLE toc (
                    e_type  TEXT,
                    e_id    INTEGER,
                    e_title TEXT
                );""");
            self.cur.execute("""
                CREATE TABLE cont (
                    t_idx       INTEGER,
                    t_jpn       JSONB,
                    t_jpn_lit   JSONB
                );""");
        return
    def get_contents(self):
        q1 = []
        for i in self.cur.execute("SELECT * FROM toc;"):
            q1.append((i[0], i[1], i[2]))
        return q1
    def get_chapter_title(self, typ, num):
        for i in self.get_contents():
            if i[0] == typ and i[1] == num:
                return i
        return (typ, num, '無題')
    def get_contents_chapters_id(self):
        q1 = []
        for i in self.get_contents():
            if i[0] == 'subtitle':
                q1.append(i[1])
        return sorted(list(set(q1)))
    def update_contents(self):
        toc = get_chapter_list(self.sid)
        self.cur.execute("DELETE FROM toc;")
        for i in toc:
            self.cur.execute("INSERT INTO toc (e_type, e_id, e_title) VALUES (?, ?, ?)",
                (i[0], i[1], i[2]))
        return
    def get_chapter(self, chap_id):
        q1 = []
        for i in self.cur.execute("SELECT * FROM cont WHERE t_idx = ?", (chap_id,)):
            q1.append(i)
        if q1 == []:
            return []
        q = [[], []]
        for num in range(0, 2):
            for i in json.loads(q1[0][num + 1]):
                if i[0] == 'line':
                    q[num].append(('line', list(tuple(i) for i in i[1])))
                else:
                    q[num].append(('break',))
        return q[0], q[1]
    def has_chapter(self, chap_id):
        q1 = []
        for i in self.cur.execute("SELECT * FROM cont WHERE t_idx = ?", (chap_id,)):
            q1.append(i)
        return q1 != []
    def update_chapter(self, chap_id, phonogram_renderer=None):
        chap1 = get_chapter(self.sid, chap_id)
        cj1 = json.dumps(chap1)
        chap2 = renderer.phoneticize(chap1, phonogram_renderer=phonogram_renderer)
        cj2 = json.dumps(chap2)
        self.cur.execute("DELETE FROM cont WHERE t_idx = ?;", (chap_id,))
        self.cur.execute("INSERT INTO cont (t_idx, t_jpn, t_jpn_lit) VALUES (?, ?, ?)",
            (chap_id, cj1, cj2))
        return
    def update_all(self, phonogram_renderer=None, display_progress_bar=False):
        self.update_contents()
        self.commit()
        ch = self.get_contents_chapters_id()
        for i in ch:
            if not self.has_chapter(i):
                self.update_chapter(i, phonogram_renderer=phonogram_renderer)
                self.commit()
                if display_progress_bar:
                    print('%s|%s\r' % (str(i).rjust(4), ('=' * int(i / len(ch) * 70)).ljust(70, '.')), end='')
        return
    def commit(self):
        self.base.commit()
        return
    def close(self):
        self.commit()
        self.base.close()
        return
    pass
