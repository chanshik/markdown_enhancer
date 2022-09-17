"""
# Markdown Parser for Technical Writer

- Code block naming
- Numbering in code block lines
- Replace reference name to number ({chapter number}-{reference number})

# BNF syntax definition

doc : para
    | doc para
    | doc code
    | doc named_code

para    : TITLE
        | sentence_list

code    : CODE_BEGIN code_block CODE_END
        | CODE_BEGIN_WITH_LANGUAGE code_block CODE_END

named_code  : CODE_BEGIN CODE_LABEL code_block CODE_END
            | CODE_BEGIN_WITH_LANGUAGE CODE_LABEL code_block CODE_END

code_block  : code_block CODE_LINE
            | CODE_LINE

sentence_list   : sentence_list sentence
                | sentence

sentence    : REF_CODE
            | REF_LINE
            | REF_FIGURE
            | REF_TABLE
            | REF_CHAPTER
            | WORD
            | NEW_LINE

# Requirements

- sly: tokenizer and parser
- typer: command line interface

"""
import sys
from dataclasses import dataclass
from typing import Dict, List, Tuple

import typer

from sly import Lexer, Parser


@dataclass
class ChapterContent:
    title: str
    number: int
    label_code_map: Dict[str, str]  # label -> code
    label_enhanced_code_map: Dict[str, str]  # label -> enhanced_code
    code_number_map: Dict[str, int]  # code_label -> code number
    line_number_map: Dict[str, int]  # line_label -> line number in codeblock
    code_lines_map: Dict[str, List[Tuple]]  # code_label -> list of line number and label tuples
    figure_number_map: Dict[str, int]  # figure_label -> figure number
    table_number_map: Dict[str, int]  # table_label -> table number
    code_number: int
    figure_number: int
    table_number: int

    def __init__(self, title: str, number: int):
        self.title = title
        self.number = number
        self.label_code_map = {}
        self.label_enhanced_code_map = {}
        self.code_number_map = {}
        self.code_lines_map = {}
        self.line_number_map = {}
        self.figure_number_map = {}
        self.table_number_map = {}
        self.code_number = 0
        self.figure_number = 0
        self.table_number = 0


class MarkdownEnhancer:
    chapter_number: int
    chapter_name_map: Dict[str, ChapterContent]
    chapter_number_map: Dict[int, ChapterContent]
    line_label_indicator: str

    def __init__(self, line_label_indicator="<<--"):
        self.chapter_number = 0
        self.chapter_name_map = {}  # chapter_name -> ChapterContent
        self.chapter_number_map = {}  # chapter_number -> ChapterContent
        self.line_label_indicator = line_label_indicator

    def add_chapter(self, title: str):
        self.chapter_number += 1
        title = title.split("#")[1].strip()

        new_chapter = ChapterContent(title=title, number=self.chapter_number)
        self.chapter_name_map[title] = new_chapter
        self.chapter_number_map[self.chapter_number] = new_chapter

    def find_chapter(self, number: int = None, title: str = None) -> ChapterContent:
        if self.chapter_number == 0:
            raise KeyError("no registered chapters")

        if number is not None:
            if number not in self.chapter_number_map:
                raise KeyError(f"invalid chapter number: {number}")
            return self.chapter_number_map[number]

        if title is not None and title != "":
            if title not in self.chapter_name_map:
                raise KeyError(f"invalid chapter title: {title}")
            return self.chapter_name_map[title]

        return self.chapter_number_map[self.chapter_number]

    def add_codeblock(self, code_label: str, code: str, chapter_number: int = None, chapter_title: str = None) -> str:
        chapter = self.find_chapter(chapter_number, chapter_title)

        if code_label in chapter.label_code_map:
            return self.ref_codeblock(chapter, code_label, code)

        chapter.label_code_map[code_label] = code
        chapter.code_number += 1
        chapter.code_number_map[code_label] = chapter.code_number
        chapter.code_lines_map[code_label] = []

        numbered_codes = self.make_numbered_codes(chapter, code_label, code, is_new=True)
        chapter.label_enhanced_code_map[code_label] = numbered_codes

        return chapter.label_enhanced_code_map[code_label]

    def make_numbered_codes(self, chapter: ChapterContent,
                            label: str, code: str, start: int = 1, is_new: bool = False) -> str:

        lines = code.splitlines()
        line_number = start - 1
        numbered_lines = []

        for line in lines:
            line_number += 1
            idx, line_label = self.extract_line_label(line)
            if idx == -1:
                numbered_lines.append(f"{line_number:02}| {line}")
                continue

            if is_new:
                chapter.line_number_map[line_label] = line_number
                chapter.code_lines_map[label].append((line_label, line_number))

            line = line[:idx]
            numbered_lines.append(f"{line_number:02}| {line}")

        return "\n".join(numbered_lines)

    def extract_line_label(self, line: str) -> (int, str):
        idx = line.rfind(self.line_label_indicator)
        if idx == -1:
            return -1, None

        line_label = line[idx+5:].strip()
        return idx, line_label

    def ref_codeblock(self, chapter: ChapterContent, code_label: str, code: str) -> str:
        lines = code.splitlines()
        first_line_label_number = -1
        read_line_count = 0

        for line in lines:
            idx, line_label = self.extract_line_label(line)
            if idx == -1:
                read_line_count += 1
                continue

            first_line_label_number = chapter.line_number_map[line_label]
            break

        if first_line_label_number == -1:
            return self.make_numbered_codes(chapter, code_label, code)

        start_line_number = first_line_label_number - read_line_count
        return self.make_numbered_codes(chapter, code_label, code, start=start_line_number)

    def find_ref_name(self, ref_text: str, ref_prefix: str, start='{', end='}') -> (ChapterContent, str, str, str):
        ref_name_start = ref_text.find(start)
        ref_name_end = ref_text.rfind(end)
        prefix = ref_text[:ref_name_start - len(ref_prefix)+1]
        postfix = ref_text[ref_name_end+1:]
        ref_value = ref_text[ref_name_start+1:ref_name_end].strip()

        chapter = self.find_chapter()
        reference = ref_value
        if "/" in ref_value:
            chapter_title, reference = ref_value.split("/")
            chapter = self.find_chapter(title=chapter_title)

        return chapter, reference, prefix, postfix

    def find_code_label(self, chapter: ChapterContent, code_label: str) -> str:
        if code_label not in chapter.code_number_map:
            raise KeyError(f"invalid code_label: {code_label}")

        code_number = chapter.code_number_map[code_label]
        return f"{chapter.number:02}-{code_number:02}"

    def find_line_label(self, chapter: ChapterContent, line_label: str) -> str:
        if line_label not in chapter.line_number_map:
            raise KeyError(f"invalid line_label: {line_label} ")

        line_number = chapter.line_number_map[line_label]
        return f"{line_number:02}"

    def find_figure_label(self, chapter: ChapterContent, figure_label: str) -> str:
        if figure_label not in chapter.figure_number_map:
            chapter.figure_number += 1
            chapter.figure_number_map[figure_label] = chapter.figure_number

        figure_number = chapter.figure_number_map[figure_label]
        return f"{chapter.number:02}-{figure_number:02}"

    def find_table_label(self, chapter: ChapterContent, table_label: str) -> str:
        if table_label not in chapter.table_number_map:
            chapter.table_number +=1
            chapter.table_number_map[table_label] = chapter.table_number

        table_number = chapter.table_number_map[table_label]
        return f"{chapter.number:02}-{table_number:02}"

    def find_chapter_title(self, title: str) -> str:
        if title not in self.chapter_name_map:
            raise KeyError(f"invalid chapter: {title}")

        chapter = self.chapter_name_map[title]
        return f"{chapter.number:02}"

    def generate_indexes(self) -> str:
        results = []
        len_of_chapters = len(self.chapter_number_map)
        for i in range(len_of_chapters):
            chapter_number = i + 1
            chapter = self.chapter_number_map[chapter_number]
            results.append(f"# {chapter.title} [{chapter_number:02}]")

            if len(chapter.code_number_map) > 0:
                results.append("## Codes")
                for code_label, number in chapter.code_number_map.items():
                    results.append(f"* {code_label} [{chapter.number:02}-{number:02}]")

                    if len(chapter.code_lines_map[code_label]) > 0:
                        for line_label, line_number in chapter.code_lines_map[code_label]:
                            results.append(f"  * {line_label} [{line_number:02}]")

            if len(chapter.figure_number_map) > 0:
                results.append("## Figures")
                for figure_label, number in chapter.figure_number_map.items():
                    results.append(f"* {figure_label} [{chapter.number:02}-{number:02}]")

            if len(chapter.table_number_map) > 0:
                results.append("## Tables")
                for table_label, number in chapter.table_number_map.items():
                    results.append(f"* {table_label} [{chapter.number:02}-{number:02}]")

        return "\n".join(results)


class CodeblockLexer(Lexer):
    tokens = [
        "CODE_END", "CODE_LABEL", "CODE_LINE",
    ]

    CODE_END = r'```\n'
    CODE_LABEL = r'[\w\-\_]+\n'
    CODE_LINE = r'.*\n'

    def CODE_END(self, t):
        self.begin(MarkdownLexer)
        return t

    def CODE_LABEL(self, t):
        return t

    def CODE_LINE(self, t):
        return t


class MarkdownLexer(Lexer):
    tokens = [
        "TITLE", "WORD", "NEW_LINE",
        "CODE_BEGIN", "CODE_BEGIN_WITH_LANGUAGE",
        "REF_CODE", "REF_LINE", "REF_FIGURE", "REF_TABLE", "REF_CHAPTER",
    ]

    TITLE = r'(?m)^\# .+\n'
    CODE_BEGIN = r'(?m)^```\s+'
    CODE_BEGIN_WITH_LANGUAGE = r'```\w+\s'
    REF_CODE = r'[`"\']?code\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_LINE = r'[`"\']?line\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_FIGURE = r'[`"\']?figure\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_TABLE = r'[`"\']?table\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_CHAPTER = r'[`"\']?chapter\{[\w\-_\+=\/ ]+\}[`"\']?'
    WORD = r'[\w\d\.,"\'`\?\!\+\-\–%:;=/\*\#\&<>\[\]\(\)\{\}\|\\\^\$]+'
    NEW_LINE = r'\n'
    ignore = ' '

    def TITLE(self, t):
        return t

    def CODE_BEGIN(self, t):
        self.begin(CodeblockLexer)
        return t

    def CODE_BEGIN_WITH_LANGUAGE(self, t):
        self.begin(CodeblockLexer)
        return t

    def NEW_LINE(self, t):
        self.lineno += t.value.count('\n')
        return t


class MarkdownParser(Parser):
    tokens = MarkdownLexer.tokens + CodeblockLexer.tokens

    def __init__(self, markdown_enhancer: MarkdownEnhancer):
        self.enhancer = markdown_enhancer

    @_('para')
    def doc(self, p):
        return p.para

    @_('doc para')
    def doc(self, p):
        return p.doc + p.para

    @_('doc code')
    def doc(self, p):
        return p.doc + p.code

    @_('doc named_code')
    def doc(self, p):
        return p.doc + p.named_code

    @_('TITLE')
    def para(self, p):
        self.enhancer.add_chapter(p.TITLE)
        return p.TITLE

    @_('sentence_list')
    def para(self, p):
        return p.sentence_list

    @_('sentence_list sentence')
    def sentence_list(self, p):
        if p.sentence_list[-1] == '\n':
            return p.sentence_list + p.sentence
        else:
            return p.sentence_list + " " + p.sentence

    @_('sentence')
    def sentence_list(self, p):
        return p.sentence

    @_('WORD',
       'NEW_LINE')
    def sentence(self, p):
        return p[0]

    @_('REF_CODE')
    def sentence(self, p):
        chapter, reference, prefix, postfix = self.enhancer.find_ref_name(p.REF_CODE, "code{")
        code_index = self.enhancer.find_code_label(chapter, reference)

        return prefix + code_index + postfix

    @_('REF_LINE')
    def sentence(self, p):
        chapter, reference, prefix, postfix = self.enhancer.find_ref_name(p.REF_LINE, "line{")
        line_index = self.enhancer.find_line_label(chapter, reference)

        return prefix + line_index + postfix

    @_('REF_FIGURE')
    def sentence(self, p):
        chapter, reference, prefix, postfix = self.enhancer.find_ref_name(p.REF_FIGURE, "figure{")
        figure_index = self.enhancer.find_figure_label(chapter, reference)

        return prefix + figure_index + postfix

    @_('REF_TABLE')
    def sentence(self, p):
        chapter, reference, prefix, postfix = self.enhancer.find_ref_name(p.REF_TABLE, "table{")
        table_index = self.enhancer.find_table_label(chapter, reference)

        return prefix + table_index + postfix

    @_('REF_CHAPTER')
    def sentence(self, p):
        _, reference, prefix, postfix = self.enhancer.find_ref_name(p.REF_CHAPTER, "chapter{")
        chapter_index = self.enhancer.find_chapter_title(reference)

        return prefix + chapter_index + postfix

    @_('CODE_BEGIN code_block CODE_END',
       'CODE_BEGIN_WITH_LANGUAGE code_block CODE_END')
    def code(self, p):
        return f"{p[0]}{p.code_block}{p.CODE_END}"

    @_('CODE_BEGIN CODE_LABEL code_block CODE_END',
       'CODE_BEGIN_WITH_LANGUAGE CODE_LABEL code_block CODE_END')
    def named_code(self, p):
        code_label = p.CODE_LABEL.strip()
        code = p.code_block
        enhanced_code = self.enhancer.add_codeblock(code_label, code)

        return f"{p[0]}\n{enhanced_code}\n{p.CODE_END}"

    @_('code_block CODE_LINE')
    def code_block(self, p):
        return p.code_block + p.CODE_LINE

    @_('CODE_LINE')
    def code_block(self, p):
        return p.CODE_LINE

    def error(self, p):
        if p:
            print(f"Syntax error at token {p.type} {p.value}")
            return self.errok()
        else:
            print("Syntax error at EOF")


def main(input_md: str, output_md: str, indicator: str = "<<--"):
    try:
        with open(input_md) as input_f:
            content = input_f.read()

    except IOError as e:
        print(f"failed to read {input_md}: {str(e)}")
        sys.exit(10)

    lexer = MarkdownLexer()
    enhancer = MarkdownEnhancer(line_label_indicator=indicator)
    parser = MarkdownParser(enhancer)

    try:
        enhanced_content = parser.parse(lexer.tokenize(content))

    except KeyError as e:
        print(str(e))
        sys.exit(20)

    except ValueError as e:
        print(str(e))
        sys.exit(21)

    indexes = enhancer.generate_indexes()

    try:
        with open(output_md, "w") as output_f:
            output_f.write(enhanced_content + "\n")
            output_f.write(indexes)

    except IOError as e:
        print(f"failed to write {output_md}: {str(e)}")
        sys.exit(11)


if __name__ == '__main__':
    typer.run(main)
