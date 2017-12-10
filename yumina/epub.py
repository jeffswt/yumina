
import mako
import mako.template
import os
import re
import shutil
import subprocess
import time

from . import renderer
from . import syosetu

def render_page(html_data, **additional_arguments):
    """ mako renderer """
    if type(html_data) == bytes:
        html_data = html_data.decode('utf-8', 'ignore')
    html_data = mako.template.Template(
        text=html_data,
        input_encoding='utf-8',
        output_encoding='utf-8').render(
            **additional_arguments if additional_arguments else dict()
        ).decode('utf-8', 'ignore')
    return html_data

def export_epub(database, display_progress_bar=False):
    prefix = './epub_output/'
    shutil.rmtree(prefix, ignore_errors=True)
    # copying critical files
    def copy(a, b):
        os.makedirs(os.path.dirname(prefix + b), exist_ok=True)
        f = [open('templates/' + a, 'rb'), open(prefix + b, 'wb')]
        f[1].write(f[0].read())
        f = [i.close() for i in f]
    copy('mimetype', 'mimetype')
    copy('container.xml', 'META-INF/container.xml')
    copy('cover.jpg', 'OEBPS/Images/cover.jpg')
    copy('main.css', 'OEBPS/Styles/main.css')
    copy('cover-img.xhtml', 'OEBPS/Text/cover-img.xhtml')
    copy('cover-name.xhtml', 'OEBPS/Text/cover-name.xhtml')
    # renderer start
    def modify(a, b, remove_returns=False, **kwargs):
        os.makedirs(os.path.dirname(prefix + b), exist_ok=True)
        f = open(prefix + b, 'w', encoding='utf-8')
        s = render_page(a, **kwargs)
        if remove_returns:
            s = re.sub(r'\n *', r'\n', s)
            s = re.sub(r'\n+', r'\n', s)
            s = s.split('<p>')
            s = '<p>'.join([s[0]] + list(i.replace('\n', '') for i in s[1:]))
        f.write(s)
        f.close()
    f = [open('templates/content.opf', 'r', encoding='utf-8'),
        open('templates/toc.ncx', 'r', encoding='utf-8'),
        open('templates/chapter.xhtml', 'r', encoding='utf-8'),
        open('templates/section.xhtml', 'r', encoding='utf-8')]
    s = [i.read() for i in f]
    _ = [i.close() for i in f]
    # really rendering pages
    toc = database.get_contents()
    toc_cnt = max(database.get_contents_chapters_id())
    modify(s[0], 'OEBPS/content.opf', toc=toc)
    modify(s[1], 'OEBPS/toc.ncx', toc=toc)
    for item in toc:
        if item[0] == 'chapter_title':
            modify(s[2], 'OEBPS/Text/chapter%s.xhtml' % str(item[1]).rjust(4, '0'), title=item)
        elif item[0] == 'subtitle':
            cont = database.get_chapter(item[1])
            modify(s[3], 'OEBPS/Text/sec%s.xhtml' % str(item[1]).rjust(4, '0'), remove_returns=True, title=item, cont=cont[1])
            if display_progress_bar:
                print('%s|%s\r' % (str(item[1]).rjust(4), ('=' * int(item[1] / toc_cnt * 70)).ljust(70, '.')), end='')
    # done this, compressing to epub
    if display_progress_bar:
        print('    |==== PACKAGING ' + '=' * (70-15))
    tname = '%s.epub' % database.sid
    if os.path.exists('output.zip'):
        os.remove('output.zip')
    if os.path.exists(tname):
        os.remove(tname)
    proc = subprocess.Popen(
        ['7z', 'a', 'output.zip', './epub_output/*'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    proc.wait()
    os.rename('output.zip', '%s.epub' % database.sid)
    shutil.rmtree(prefix, ignore_errors=True)
    return

for i in {'7z'}:
    if not os.path.exists(i) and not os.path.exists(i + '.exe'):
        raise RuntimeError('requires "%s" to execute' % i)
