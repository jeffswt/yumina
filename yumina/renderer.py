
import os
import subprocess
import threading

__global_phonogram_renderer = None

class PhonogramRenderer:
    def __init__(self):
        # javac -encoding utf-8 -classpath kuromoji.jar TokenizerCaller.java
        # java -classpath ./kuromoji.jar;./TokenizerCaller.class; TokenizerCaller
        self.proc = subprocess.Popen(
            ['java', '-classpath', './kuromoji.jar;./TokenizerCaller.class;', 'TokenizerCaller'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        self.th_lock = threading.Lock()
        return
    def __communicate__(self, cont, noread=False):
        lines = []
        gl_lock = threading.Lock()
        gl_lock.acquire()
        def out_thr(proc):
            if noread:
                gl_lock.release()
                return
            while True:
                s = proc.stdout.readline().decode('utf-8', 'ignore').replace('\r', '').replace('\n', '')
                if s == '__ANALYSIS_COMPLETE__':
                    break
                lines.append(s)
            gl_lock.release()
            return
        threading.Thread(target=out_thr, args=[self.proc]).start()
        self.proc.stdin.write(cont.encode('utf-8', 'ignore'))
        self.proc.stdin.flush()
        gl_lock.acquire()
        gl_lock.release()
        return lines
    def __match_romaji(self, a, b):
        # align katakana to kanji, marking pronunciation
        def kana_eq(p, q): # p is char, q is katakana
            if p == q:
                return True
            if '\u3040' <= p <= '\u309f':
                return chr(ord(p) - ord('\u3040') + ord('\u30a0')) == q
            return False
        # convert strings
        M = a
        N = b
        m = len(M)
        n = len(N)
        R = []
        # dynamic programming
        dist = list(list((0, '') for j in range(0, n + 2)) for i in range(0, m + 2))
        dist[0][0] = (0, '')
        for i in range(0, m + 1):
            dist[i][0] = (i, M[:i], ' ' * i)
        for j in range(0, n + 1):
            dist[0][j] = (j, ' ' * j, N[:j])
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if kana_eq(M[i-1], N[j-1]):
                    dist[i][j] = (dist[i-1][j-1][0], dist[i-1][j-1][1] + M[i-1], dist[i-1][j-1][2] + N[j-1])
                else:
                    mat_1 = dist[i][j-1][0] + 1
                    mat_2 = dist[i-1][j][0] + 1
                    mat_3 = dist[i-1][j-1][0] + 1
                    mat = min(mat_1, mat_2, mat_3)
                    if mat_2 == mat: # skip one
                        dist[i][j] = (dist[i-1][j][0] + 1, dist[i-1][j][1] + M[i-1], dist[i-1][j][2] + ' ')
                    elif mat_1 == mat: # add one
                        dist[i][j] = (dist[i][j-1][0] + 1, dist[i][j-1][1] + ' ', dist[i][j-1][2] + N[j-1])
                    else:
                        dist[i][j] = (dist[i-1][j-1][0] + 1, dist[i-1][j-1][1] + M[i-1], dist[i-1][j-1][2] + N[j-1])
        _, s_src, s_prn = dist[m][n]
        mode = 'kana' if kana_eq(s_src[0], s_prn[0]) else 'kanji'
        s_src += '?'
        s_prn += '?'
        buff_l = s_src[0]
        buff_r = s_prn[0]
        for i in range(1, len(s_src)):
            if mode == 'kanji' and (kana_eq(s_src[i], s_prn[i]) or s_src[i] == '?'):
                R.append(('phonogram', buff_l.replace(' ', ''), buff_r.replace(' ', '')))
                buff_l = buff_r = ''
                mode = 'kana'
            elif mode == 'kana' and (not kana_eq(s_src[i], s_prn[i]) or s_src[i] == '?'):
                R.append(('regular', buff_l))
                buff_l = buff_r = ''
                mode = 'kanji'
            buff_l += s_src[i]
            buff_r += s_prn[i]
        return R
    def __direct_convert(self, cont, hiragana):
        if '\n' in cont:
            raise ValueError('should not contain line breaks')
        q1 = []
        for s in self.__communicate__(cont + '\n'):
            a, b = tuple(s.split('__SPLIT__'))
            if a == b:
                q1.append(('regular', a))
            elif b == '':
                q1.append(('regular', a))
            else:
                q2 = self.__match_romaji(a, b)
                for i in q2:
                    q1.append(i)
        # convert katakana to hiragana
        for i in range(0, len(q1)):
            if q1[i][0] == 'phonogram':
                if len(q1[i]) < 2:
                    q1[i] = ('regular', q1[i][1])
                if hiragana:
                    q2 = list(q1[i][2])
                    for j in range(0, len(q2)):
                        if q2[j] not in {'ー'}:
                            q2[j] = chr(ord(q2[j]) - ord('\u30a0') + ord('\u3040'))
                    q1[i] = (q1[i][0], q1[i][1], ''.join(q2))
        # joining similar items
        q2 = []
        for i in q1:
            if len(q2) > 0 and i[0] == q2[-1][0] == 'regular':
                q2[-1] = ('regular', q2[-1][1] + i[1])
            else:
                q2.append(i)
        return q2
    def convert(self, content, hiragana=False):
        self.th_lock.acquire()
        res = self.__direct_convert(content, hiragana)
        self.th_lock.release()
        return res
    def close(self):
        global __global_phonogram_renderer
        self.proc.terminate()
        self.proc.wait()
        __global_phonogram_renderer = None
        return
    pass

def get_phonogram_renderer():
    global __global_phonogram_renderer
    if __global_phonogram_renderer == None:
        __global_phonogram_renderer = PhonogramRenderer()
    return __global_phonogram_renderer

def phoneticize(articles, phonogram_renderer=None, hiragana=False):
    if phonogram_renderer == None:
        phonogram_renderer = get_phonogram_renderer()
    q1 = []
    for line in articles:
        if line[0] == 'break':
            q1.append(line)
        else:
            q1.append(('line', phonogram_r.convert(line[1][0][1], hiragana=hiragana)))
    return q1

for i in {'kuromoji.jar', 'TokenizerCaller.class'}:
    if not os.path.exists(i):
        raise RuntimeError('requires "%s" to execute' % i)
