
# yumina / ユミナ

This tool provides an API to phoneticize Japanese paragraphs and novels, via the Japanese morphological analyzer [kuromoji](http://www.atilika.org/).

The project is named after *Yumina Ernier Belfast* in light novel *In Another World With My Smartphone*.

![ユミナさん](./images/yumina.png)

You may also download novels from [小説家になろう](https://syosetu.com/) and save them to a local database, where you could update them on a timely basis.

In addition, downloaded novels can also be phoneticized and exported to EPUB documents. However, the EPUB templates ought to be modified before utilization.

## Dependencies

*   `kuromoji.jar`

    Download at [https://github.com/atilika/kuromoji/downloads](https://github.com/atilika/kuromoji/downloads).

*   `TokenizerCaller.class`

    Compile with command `javac -encoding utf-8 -classpath kuromoji.jar TokenizerCaller.java`. Must have `kuromoji.jar` in advance.

*   `7z / 7z.exe`

    You must have a valid 7-zip distribution in order to create EPUB documents. You can download them here: http://7-zip.org/download.html

*   `/templates`

    The default templates are provided in the project.

These files must be present under the working directory.

## API

**The entire library is guranteed to be thread-safe.**

*   Phoneticized Article Interchange Format (PAIF)

    ```python
    [
        ('line', [
            ('regular', '「というわけで、お'),
            ('phonogram', '前', 'マエ'),
            ('regular', 'さんは'),
            ('phonogram', '死', ' シ'),
            ('regular', 'んでしまった。'),
            ('phonogram', '本当', 'ホントウ'),
            ('regular', 'に'),
            ('phonogram', '申', 'モウ'),
            ('regular', 'し'),
            ('phonogram', '訳', 'ワケ'),
            ('regular', 'ない」')
        ]),
        ('break',),
        ('line', [
            ('regular', '「はあ」')
        ])
    ]
    ```

*   `renderer.PhonogramRenderer`

    Class initializes a *kuromoji* library and communicates with it in order to add phonograms to the sentence. This class is thread-safe.

    *   `.convert(content, hiragana=False)`

        content: A string to phoneticize, must not contain line breaks.

        hiragana: Set to True to represent phonograms with hiragana, otherwise would use katakana.

    *   `.close()`

        Terminate the *kuromoji* library and discard this renderer instance.

*   `renderer.get_phonogram_renderer()`

  Returns a shared `renderer.PhonogramRenderer` instance.

  *Alias:* `get_phonogram_renderer(...)`

*   `renderer.phoneticize(article, phonogram_renderer=None, hiragana=False)`

  Phoneticize an article and returns a PAIF object.

  *   `article`

      A PAIF object, must not be processed in advance.

  *   `phonogram_renderer`

      If not given, would assign one of its own.

  *   `hiragana`

      Use hiragana instead of katakana while phoneticizing.

  *Alias:* `phoneticize(...)`

*   `syosetu.get_chapter_list(web_id)`

  Returns a list of chapters, taking the following forms:

  *   `'chapter_title', chapter_id, title`
  *   `'subtitle', subtitle_id, subtitle`

  For example:

  `[('chapter_title', 1, '異世界来訪。'), ('subtitle', 1, '死亡、そして復活。'), ('subtitle', 2, '目覚め、そして異世界。'), ...]`

*   `syosetu.get_chapter(web_id, chap_id)`

  Returns a PAIF object, unprocessed.

  *   `web_id`

      Web novel ID, e.g. `n1443bp`.

  *   `chap_id`

      Chapter ID, an integer.

*   `syosetu.SyosetuDatabase`

    Class manages novel chapters stored in a SQLite database.

    *   `.__init__(filename, syosetu_id, force_clear=False)`

        *   `filename`

            Database filename.

        *   `syosetu_id`

            Web novel ID, e.g. `n1443bp`.

        *   `force_clear`

            If set to True, would reset the database.

    *   `.get_contents()`

        Functions like `syosetu.get_chapter_list()`, but offline.

    *   `.get_chapter_title(typ, num)`

        Finds the title of the entry in TOC matching `typ` and `num`.

    *   `.get_contents_chapters_id()`

        Get all subtitle IDs in a list.

    *   `.update_contents()`

        Update offline database TOC.

    *   `.get_chapter(chap_id)`

        Returns two PAIF objects, one is the original data and the other is processed.

    *   `.has_chapter(chap_id)`

        Returns if this chapter exists in database.

    *   `.update_chapter(chap_id, phonogram_renderer=None)`

        Downloads chapter, processes and stores into database.

    *   `.update_all(phonogram_renderer=None, display_progress_bar=False)`

        Downloads entire novel to local database.

    *   `.commit()`

        Flush changes to file.

    *   `.close()`

        Close database.

*   `epub.export_epub(database, display_progress_bar=False)`

    Export EPUB file with given templates and database.


## Issues

-   [ ] can't convert raw string to PAIF object
-   [ ] easier customizations of EPUB templates
-   [ ] <del>don't have a morphological analyzer of my own</del>
-   [x] <del>this light novel doesn't make any sense...</del>
