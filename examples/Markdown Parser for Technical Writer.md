# 기술 문서 작성을 위한 마크다운 파서 개발
문서 중에 코드를 제시하고 그에 대한 설명을 작성하는 형식으로 기술 문서를 작성하는 경우, 참조할 코드를 지칭하기 위해서 코드 번호나 이름을 사용합니다. 예를 들어, `코드 01` 등과 같은 형태로 앞에서 나온 코드라는 것을 언급하고, 이어서 해당 코드에 대한 설명을 작성하는 형식입니다. 코드가 적어서 이후에 수작업으로 수정하는 것이 가능하다면 크게 문제가 되지는 않지만, 기술 문서의 특성상 코드나 표, 그림을 지칭하는 경우가 많아서 은근히 시간을 많이 잡아먹는 작업입니다. `latex` 등과 같은 문서 형식을 사용하면 상대적으로 쉽게 해결되는 문제이긴 하지만, 마크다운 형식으로 문서를 주로 작성하니까 원하는 기능을 찾기가 쉽지 않았습니다. 그래서 마크다운 문법으로 그을 작성할 때 참조하는 부분을 자동으로 치환해주는 파서를 개발해 이 불편함을 개선해보았습니다.

## 구현 기능
구현한 기능 중에 첫 번째는 코드 블럭에 이름을 붙여두고 나중에 참조할 때 이름을 사용하는 기능입니다. 기존 코드 블럭 태그 다음에 코드 이름을 지정하고 파서에서 해당 이름을 추출할 수 있도록 구현했습니다. 그리고 코드 블럭 각 라인에 번호를 붙여주는 기능입니다. 이 기능은 코드 블럭에 레이블을 붙여둔 경우에만 동작하고 일반적인 코드 블럭이라면 적용되지 않도록 했습니다. 코드 이름 뿐만 아니라 코드 안에 특정한 라인을 지칭할 수 있는 라인 레이블 기능도 구현했습니다. 라인에 붙여둔 레이블은 라인을 참조할 때 몇 번째 줄인지 나타낼 때 사용되며, 코드 블럭 일부를 다시 표시할 때 라인 앞에 붙는 번호의 기준점이 됩니다. 참조 기능은 코드 블럭, 그림, 표 등을 이름으로 언급하면 나타난 순서를 숫자로 치환해 변경해주는 기능입니다. 
코드 블럭은 코드 레이블을 지정하는 구문을 추가적으로 지정해 구현하였고, 나머지 참조 기능은 토큰을 추가해 파싱 단계에서 숫자로 변환합니다.

## 마크다운 문서 확장 구문 정의
기존 마크다운 문서 구문을 그대로 사용하면서 원하는 기능을 지원할 수 있도록 몇 가지 토큰과 규칙을 추가해 BNF(Backus-Naur Form) 표현식을 정의하였습니다. 
먼저 타이틀(`TITLE`)과 코드블럭 안에서 코드 레이블을 추출할 수 있도록 문법을 구성하였습니다. 그리고 코드 이름(`REF_CODE`), 코드 안에 특정 라인을 나타내는 라인 이름(`REF_LINE`), 그림(`REF_FIGURE`)과 표(`REF_TABLE`) 그리고 챕터(`REF_CHAPTER`) 이름을 참조할 수 있도록 태그를 추가하였습니다. 

코드 블럭 태그는 기존 문법을 확장해 코드 이름을 지정할 수 있도록 구성하였습니다. 이름표를 붙인 코드는 `code{}` 태그를 이용해 `01-01` 등으로 쉽게 치환할 수 있습니다. 코드 안에 라인에도 이름표를 지정하는 것이 가능하고 `line{}` 태그를 이용해 특정한 라인이 몇 번째 줄에 위치하고 있는지 간편하게 지정할 수 있습니다.

``` markdown-bnf
doc : para  <<-- markdown-bnf-doc
    | doc para
    | doc code
    | doc named_code

para    : TITLE  <<-- markdown-bnf-title
        | sentence_list

sentence_list   : sentence_list sentence
                | sentence

sentence    : REF_CODE  <<-- markdown-ref-tags
            | REF_LINE
            | REF_FIGURE
            | REF_TABLE
            | REF_CHAPTER
            | WORD
            | NEW_LINE

code    : CODE_BEGIN code_block CODE_END
        | CODE_BEGIN_WITH_LANGUAGE code_block CODE_END

named_code  : CODE_BEGIN CODE_LABEL code_block CODE_END  <<-- markdown-bnf-named-code
            | CODE_BEGIN_WITH_LANGUAGE CODE_LABEL code_block CODE_END

code_block  : code_block CODE_LINE
            | CODE_LINE
```
코드 `code{markdown-bnf}`

BNF 문법 정의 내용은 기존의 마크다운 문서를 파싱하기 위한 규칙과 코드 블럭 확장을 위한 규칙으로 구성됩니다.
코드 `code{markdown-bnf}`  에는 마크다운 문서의 일반적인 문장을 `doc`, `para`, `sentence-list`, `sentence` 심볼로 추출하는 문법을 정의하고 있습니다. 코드 블럭 태그를 만나면 그 안에 있는 내용들은 `code` 아니면 `named_code` 규칙에 따라 추출됩니다.

``` markdown-bnf
para    : TITLE  <<-- markdown-bnf-title
        | sentence_list
```

`para` 규칙은 `TITLE` 아니면 `sentence_list` 로 분리되는데, `TITLE` 은 마크다운에서 `#` 문자로 시작하는 `Header` 문자열을 의미합니다. `TITLE` 을 만날 때마다 `Chapter` 번호는 1씩 증가되고, 코드와 참조 정보를 저장하기 위한 데이터 클래스를 하나씩 생성합니다.

``` markdown-bnf
sentence_list   : sentence_list sentence
                | sentence
    
sentence    : REF_CODE  <<-- markdown-ref-tags
            | REF_LINE
            | REF_FIGURE
            | REF_TABLE
            | REF_CHAPTER
            | WORD
            | NEW_LINE
```

`sentence_list` 규칙은 `sentence` 문장이 반복되어 완성됩니다. `sentence` 에는 일반적인 문자와 줄 바꿈 문자 그리고 참조하는 대상을 지칭하기 위한 `REF_CODE`, `REF_LINE`, `REF_FIGURE`, `REF_TABLE`, `REF_CHAPTER` 태그로 구성됩니다.

``` markdown-bnf
code    : CODE_BEGIN code_block CODE_END
        | CODE_BEGIN_WITH_LANGUAGE code_block CODE_END

named_code  : CODE_BEGIN CODE_LABEL code_block CODE_END  <<-- markdown-bnf-named-code
            | CODE_BEGIN_WITH_LANGUAGE CODE_LABEL code_block CODE_END

code_block  : code_block CODE_LINE
            | CODE_LINE
```

코드 `code{markdown-bnf}` 에서 `line{markdown-bnf-named-code}` 번째 줄을 살펴보면 기존의 코드 블럭 문법에 `CODE_LABEL` 이라는 토큰이 추가되어 있는 것을 볼 수 있습니다. `CODE_LABEL` 로 분리한 토큰은 해당 코드 블럭의 이름표를 나타내며, 문서 내부에서 해당 코드를 지칭하면서 설명하고자 할 때 `code{}` 태그를 이용해 쉽게 몇 번째 코드 블럭인지 치환할 수 있습니다. 또한, `CODE_LABEL` 토큰을 가지고 있는 코드 블럭인 경우에는 각 코드의 앞에 줄 번호를 추가합니다. 코드 블럭이 `CODE_LABEL` 토큰을 가지고 있지 않다면 아무런 변경 없이 그대로 출력되어 결과물에 포함됩니다.

# ply & sly 프로젝트
문서를 특정한 문법에 맞도록 토큰을 분리하고 지정된 문법에 따라 구성하는 데 `lex` 와 `yacc` 혹은 그와 비슷한 도구를 많이 사용합니다.
파이썬에서 코드 내부에 토큰을 정의하고 문법을 구성할 수 있는 오픈소스 프로젝트로 `ply` 와 `sly` 를 사용할 수 있습니다.

## ply 소개
`ply` 프로젝트는 토큰과 문법을 파이썬 `docstring` 문법을 사용해 표현합니다.
`ply` 홈페이지에서 볼 수 있는 예제 코드를 살펴보겠습니다.

```python ply-lexer
# ------------------------------------------------------------
# calclex.py
#
# tokenizer for a simple expression evaluator for
# numbers and +,-,*,/
# ------------------------------------------------------------
import ply.lex as lex
 
# List of token names.   This is always required
tokens = (
   'NUMBER',
   'PLUS',
   'MINUS',
   'TIMES',
   'DIVIDE',
   'LPAREN',
   'RPAREN',
)
 
# Regular expression rules for simple tokens  <<-- ply-simple-tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
 
# A regular expression rule with some action code  <<-- ply-token-with-action
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)    
    return t

# Define a rule so we can track line numbers  <<-- ply-new-line
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# A string containing ignored characters (spaces and tabs)  <<-- ply-ignored
t_ignore  = ' \t'

# Error handling rule
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

# Build the lexer  <<-- ply-lexer
lexer = lex.lex()
```
코드 `code{ply-lexer}`

`ply` 에서는 사용할 토큰을 `tokens` 리스트로 정의하고 각 토큰 이름 앞에 `t_` 접두어를 붙여 표시합니다. 
각 토큰을 구성하는 정규표현식을 변수의 값으로 지정하거나 함수의 `docstring` 으로 표현할 수 있습니다.

토큰으로 분리한 문자열을 사칙연산 문법에 맞는지 파싱하는 예제 코드를 살펴보겠습니다.

```python ply-yacc
import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from calclex import tokens

def p_expression_plus(p):  <<-- yacc-expression-plus
    'expression : expression PLUS term'
    p[0] = p[1] + p[3]

def p_expression_minus(p):
    'expression : expression MINUS term'
    p[0] = p[1] - p[3]

def p_expression_term(p):
    'expression : term'
    p[0] = p[1]

def p_term_times(p):
    'term : term TIMES factor'
    p[0] = p[1] * p[3]

def p_term_div(p):
    'term : term DIVIDE factor'
    p[0] = p[1] / p[3]

def p_term_factor(p):
    'term : factor'
    p[0] = p[1]

def p_factor_num(p):
    'factor : NUMBER'
    p[0] = p[1]

def p_factor_expr(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]

# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")

# Build the parser
parser = yacc.yacc()

while True:
   try:
       s = raw_input('calc > ')
   except EOFError:
       break
   if not s: continue
   result = parser.parse(s)
   print(result)
```
코드 `code{ply-yacc}`

토큰을 정의할 때와 동일한 방법으로 함수 `docstring` 안에 해당 함수에서 처리할 문법을 정의합니다.

```python ply-yacc
def p_expression_plus(p):  <<-- yacc-expression-plus
    'expression : expression PLUS term'
    p[0] = p[1] + p[3]

def p_expression_minus(p):
    'expression : expression MINUS term'
    p[0] = p[1] - p[3]
```

코드 `code{ply-yacc}` 에서 `line{yacc-expression-plus}` 번째 줄에 `PLUS` 토큰을 처리하는 함수를 정의하였습니다. 왼쪽 `expression` 은 오른쪽에 있는 `expression` 과 `term` 의 합으로 도출되는데, 이 때 실제 값에 접근하기 위해서 `p[1]`, `p[3]` 등의 인덱스를 사용합니다.

`David Beazley` 는 1998년에 발표된 [Compiling Little Languages in Python](https://legacy.python.org/workshops/1998-11/proceedings/papers/aycock-little/aycock-little.html) 논문에서 `docstring` 을 이용해 문법을 코드 안에 내장한 컨셉을 그대로 가져와 2001년에 `ply` 프로젝트를 개발할 때 사용했다고 얘기했었습니다.
https://youtu.be/zJ9z6Ge-vXs?t=557

`lex` & `yacc` 를 사용해 문법을 정의할 때에는 해당 문법을 정의한 파일을 별도로 작성하는 것이 일반적입니다. 하지만 `docstring` 을 활용해 코드 안에 문법을 내장하는 방법은 별도의 파일을 필요로하지 않고 모든 내용을 하나의 파일에서 참조할 수 있어 매우 간편한 방법입니다.
하지만, 최근에 파이썬 코드를 사용하는 방법과는 거리가 있는 프로젝트였기 때문에 이를 개선한 프로젝트가 다시 개발되었습니다.

## sly 소개
`ply` 프로젝트에서 오래되거나 이상한 형태로 사용했던 파이썬 코드를 개선한 프로젝트가 `sly` 입니다. `docstring` 을 이용해 문법을 정의하던 방식을 버리고 `데코레이터` 를 이용해 좀 더 간결하게 문법을 정의할 수 있도록 개선하였습니다. 클래스 형태로 `Lexer` 와 `Parser` 가 지원되기 때문에 전체적인 코드를 깔끔하게 작성할 수 있었습니다.

`ply` 를 이용한 것과 동일하게 사칙연산을 토큰으로 분리하는 `lexer` 를 살펴보겠습니다.

```python sly-lexer
# calclex.py

from sly import Lexer

class CalcLexer(Lexer):  <<-- sly-lexer-class
    # Set of token names.   This is always required
    tokens = { ID, NUMBER, PLUS, MINUS, TIMES,
               DIVIDE, ASSIGN, LPAREN, RPAREN }

    # String containing ignored characters between tokens
    ignore = ' \t'

    # Regular expression rules for tokens
    ID      = r'[a-zA-Z_][a-zA-Z0-9_]*'
    NUMBER  = r'\d+'
    PLUS    = r'\+'
    MINUS   = r'-'
    TIMES   = r'\*'
    DIVIDE  = r'/'
    ASSIGN  = r'='
    LPAREN  = r'\('
    RPAREN  = r'\)'

    def NUMBER(self, t):  <<-- sly-lexer-number
        t.value = int(t.value)   # Convert to a numeric value
        return t
    
if __name__ == '__main__':
    data = 'x = 3 + 42 * (s - t)'
    lexer = CalcLexer()
    for tok in lexer.tokenize(data):
        print('type=%r, value=%r' % (tok.type, tok.value))
```
코드 `code{sly-lexer}`

`sly` 에서는 `Lexer` 클래스를 제공하기 때문에 이를 상속한 새로운 클래스를 정의해 쉽게 사용하는 것이 가능합니다.

```python sly-lexer
class CalcLexer(Lexer):  <<-- sly-lexer-class
    # Set of token names.   This is always required
    tokens = { ID, NUMBER, PLUS, MINUS, TIMES,
               DIVIDE, ASSIGN, LPAREN, RPAREN }

    # String containing ignored characters between tokens
    ignore = ' \t'
```

기존에 `ply` 에서 정의한 것과 동일하게 `tokens` 속성을 정의하고 무시할 문자를 `ignore` 속성에 넣어서 사용할 수 있습니다.

```python sly-lexer
    LPAREN  = r'\('
    RPAREN  = r'\)'

    def NUMBER(self, t):  <<-- sly-lexer-number
        t.value = int(t.value)   # Convert to a numeric value
        return t
```

토큰을 분리하고 추가적인 작업이 필요하다면 위에 토큰과 동일한 이름으로 `NUMBER()` 멤버 함수를 정의하고 그 안에 필요한 작업을 구현합니다.

분리한 토큰을 문법에 맞도록 분리하고 필요한 작업을 구현한 `Parser` 코드를 살펴보겠습니다.

```python sly-yacc
from sly import Parser
from calclex import CalcLexer

class CalcParser(Parser):
    # Get the token list from the lexer (required)
    tokens = CalcLexer.tokens  <<-- sly-yacc-tokens

    # Grammar rules and actions
    @_('expr PLUS term')  <<-- sly-yacc-expr
    def expr(self, p):
        return p.expr + p.term

    @_('expr MINUS term')
    def expr(self, p):
        return p.expr - p.term

    @_('term')
    def expr(self, p):
        return p.term

    @_('term TIMES factor')
    def term(self, p):
        return p.term * p.factor

    @_('term DIVIDE factor')
    def term(self, p):
        return p.term / p.factor

    @_('factor')
    def term(self, p):
        return p.factor

    @_('NUMBER')
    def factor(self, p):
        return p.NUMBER

    @_('LPAREN expr RPAREN')
    def factor(self, p):
        return p.expr

if __name__ == '__main__':  <<-- sly-yacc-main
    lexer = CalcLexer()
    parser = CalcParser()

    while True:
        try:
            text = input('calc > ')
            result = parser.parse(lexer.tokenize(text))
            print(result)
        except EOFError:
            break
```
코드 `code{sly-yacc}`

`CalcParser` 클래스는 `CalcLexer` 클래스에서 분리한 토큰을 이용해 문법에 맞는지 구문 분석 과정을 수행합니다. `Parser` 에서 사용할 토큰 목록을 `CalcLexer` 클래스에서 가져와서 사용합니다. 그리고 개별 구문을 처리할 규칙을 멤버 함수와 데코레이터를 이용해 정의합니다.

```python sly-yacc
class CalcParser(Parser):
    # Get the token list from the lexer (required)
    tokens = CalcLexer.tokens  <<-- sly-yacc-tokens

    # Grammar rules and actions
    @_('expr PLUS term')  <<-- sly-yacc-expr
    def expr(self, p):
        return p.expr + p.term

    @_('expr MINUS term')
    def expr(self, p):
        return p.expr - p.term
```

`CalcParser` 클래스 코드 `code{sly-yacc}` 에서 `line{sly-yacc-expr}` 번째 줄에 정의된 구문을 살펴보겠습니다.

```
expr : expr PLUS term
```

정의한 함수 이름이 가장 왼쪽에 위치한 심볼(symbol)을 나타내고 데코레이터 안에 기록한 내용으로 해당 심볼을 정의합니다. 오른쪽에 위치한 토큰 혹은 심볼의 값에 접근하기 위해서 `p.expr` 이나 `p.term` 처럼 이름을 직접 사용해 가져오는 것이 가능합니다. 물론 동시에 여러 개의 구문을 한 함수에서 정의하고 처리하는 것도 지원합니다.

```python sly-yacc-multi
@_('expr PLUS term',
   'expr MINUS term')
def expr(self, p):
    return (p[1], p.expr, p.term)
```
코드 `code{sly-yacc-multi}`

여러 구문을 동시에 선언한 경우에 중복되는 심볼이나 토큰은 `p.expr` 같은 형태로 값을 가져올 수 있고, 같은 위치에 서로 다른 심볼이나 토큰이 나타날 경우에는 인덱스를 이용한 `p[1]` 같은 형태로 값을 가져올 수 있습니다.

`sly` 를 이용해 문자열에서 토큰을 분리하고 구문을 분석하는 `main` 함수 부분은 다음과 같은 형태로 구성합니다.

```python sly-yacc
if __name__ == '__main__':  <<-- sly-yacc-main
    lexer = CalcLexer()
    parser = CalcParser()

    while True:
        try:
            text = input('calc > ')
            result = parser.parse(lexer.tokenize(text))
            print(result)
        except EOFError:
            break
```

`lexer.tokenize()` 함수에 문자열을 넘겨 토큰을 분리해 `parser.parse()` 함수에 전달하면 정의된 규칙에 따라 파싱 과정을 진행합니다.
최종 결과는 `result` 변수에 기록되어 화면에 출력합니다.

## Lexing States
`Lexer` 를 이용해 토큰을 분리할 때, 상태에 기반해 토큰의 의미가 달라지는 경우가 있습니다. 예를 들어, 코드 블럭을 열고 닫는 태그는 동일한 **\`\`\`** 태그를 사용하지만 나오는 위치에 따라 역할이 달라집니다. 일반적인 문장이 나오고 **\`\`\`** 태그를 만나면 코드 블럭을 시작하는 의미가 되고, 이미 코드 블럭을 만나서 코드를 라인 단위로 읽다가 다시 **\`\`\`** 태그를 만나면 코드 블럭을 닫고 다시 일반 문장을 읽어나가도록 처리해야 합니다.

기존 `ply` 에서는 `states` 튜플에 사용하고자 하는 상태 정보를 미리 정의하고 `lexer.begin()` 함수를 이용해 상태를 변경하였습니다. `sly` 에서는 상태 별로 토큰을 정의한 `Lexer` 클래스를 구현하고 상황에 맞는 클래스를 `self.begin()` 함수 인자에 넘겨 상태를 변경합니다.

# 구현 클래스 소개
## MarkdownLexer 클래스
`MarkdownLexer` 는 마크다운의 일반적인 요소와 참조 태그 그리고 코드 블럭의 시작 태그를 토큰으로 분리합니다. 코드 블럭 안에서 토큰을 분리하는 작업은 별도로 정의한 `CodeblockLexer` 클래스에서 진행하기 때문에 그와 관련된 태그는 `MarkdownLexer` 안에 정의하지 않았습니다.

```python markdown-lexer
class MarkdownLexer(Lexer):
    tokens = [  <<-- markdown-lexer-tokens
        "TITLE", "WORD", "NEW_LINE",
        "CODE_BEGIN", "CODE_BEGIN_WITH_LANGUAGE",
        "REF_CODE", "REF_LINE", "REF_FIGURE", "REF_TABLE", "REF_CHAPTER",
    ]

    TITLE = r'(?m)^\# .+\n'  <<-- markdown-lexer-regex
    CODE_BEGIN = r'(?m)^```\s+'
    CODE_BEGIN_WITH_LANGUAGE = r'```\w+\s'
    REF_CODE = r'[`"\']?code\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_LINE = r'[`"\']?line\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_FIGURE = r'[`"\']?figure\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_TABLE = r'[`"\']?table\{[\w\-_\+=\/ ]+\}[`"\']?'
    REF_CHAPTER = r'[`"\']?chapter\{[\w\-_\+=\/ ]+\}[`"\']?'
    WORD = r'[\w\d\.,"\'`\?\!\+-=/\*\#\&<>\[\]\(\)\{\}\|]+'
    NEW_LINE = r'\n'
    ignore = ' '

    def TITLE(self, t):
        return t

    def CODE_BEGIN(self, t):  <<-- markdown-lexer-code-begin
        self.begin(CodeblockLexer)
        return t

    def CODE_BEGIN_WITH_LANGUAGE(self, t):
        self.begin(CodeblockLexer)
        return t

    def NEW_LINE(self, t):
        self.lineno += t.value.count('\n')
        return t
```
코드 `code{markdown-lexer}` 

`MarkdownLexer` 클래스 안에 `tokens` 속성에 리스트로 분리할 토큰을 먼저 정의합니다. `TITLE`, `WORD`, `NEW_LINE` 은 마크다운에서 코드 블럭 바깥에 작성된 문장을 나타내는 목적으로 사용합니다. `CODE_BEGIN`, `CODE_BEGIN_WITH_LANGUAGE` 토큰은 코드 블럭 시작 태그를 분리하기 위해 정의해 두었습니다. 마지막 줄에 있는 `REF_CODE`, `REF_LINE`, `REF_FIGURE`, `REF_TABLE`, `REF_CHAPTER` 토큰은 정규표현식을 이용해 일정한 규칙에 따라 대상 문자열을 추출합니다.

```python markdown-lexer
    TITLE = r'(?m)^\# .+\n'  <<-- markdown-lexer-regex
    CODE_BEGIN = r'(?m)^```\s+'
    CODE_BEGIN_WITH_LANGUAGE = r'```\w+\s'
    REF_CODE = r'[`"\']?code\{[\w\-_\+= ]+\}[`"\']?'
    REF_LINE = r'[`"\']?line\{[\w\-_\+= ]+\}[`"\']?'
    REF_FIGURE = r'[`"\']?figure\{[\w\-_\+= ]+\}[`"\']?'
    REF_TABLE = r'[`"\']?table\{[\w\-_\+= ]+\}[`"\']?'
    REF_CHAPTER = r'[`"\']?chapter\{[\w\-_\+= ]+\}[`"\']?'
    WORD = r'[\w\d\.,"\'`\?\!\+-=/\*\#\&<>\[\]\(\)\{\}\|]+'
    NEW_LINE = r'\n'
    ignore = ' '
```

코드 `code{markdown-lexer}` 안에 `line{markdown-lexer-regex}` 번째 줄에서 각 토큰을 구분하기 위한 정규표현식이 정의되어 있는 것을 볼 수 있습니다. 만약 문자열의 앞(`^`)이나 끝(`$`)에 위치한 문자열 패턴을 사용하고 싶다면, `(?m)` 문자열로 정규표현식을 구성하는 것이 필요합니다. 그리고 무시하려는 문자는 `ignore` 속성에 추가해둡니다. 여기서는 (`' '`) 공백 문자만 무시하도록 정의하였습니다.

```python markdown-lexer
    def CODE_BEGIN(self, t):  <<-- markdown-lexer-code-begin
        self.begin(CodeblockLexer)
        return t

    def CODE_BEGIN_WITH_LANGUAGE(self, t):
        self.begin(CodeblockLexer)
        return t
```

코드 `code{markdown-lexer}` 의 `line{markdown-lexer-code-begin}` 줄에서 코드 블럭을 시작한 이후에 토큰을 분리하는 작업을 `CodeblockLexer` 로 넘기는 것을 확인할 수 있습니다. `CodeblockLexer` 클래스에는 코드 블럭 안에서 코드 블럭이 끝나는 토큰을 찾는 역할을 수행하도록 토큰을 정의하고 있습니다.

## CodeblockLexer 클래스
`CodeblockLexer` 클래스에서는 코드 블럭 안에서 코드 레이블과 닫는 코드 블럭 태그를 토큰으로 분리하는 역할을 수행합니다.

```python codeblock-lexer
class CodeblockLexer(Lexer):
    tokens = [
        "CODE_END", "CODE_LABEL", "CODE_LINE",
    ]

    CODE_END = r'```\n'
    CODE_LABEL = r'[\w\-\_]+\n'
    CODE_LINE = r'.*\n'

    def CODE_END(self, t):  <<-- codeblock-lexer-code-end
        self.begin(MarkdownLexer)
        return t

    def CODE_LABEL(self, t):
        return t

    def CODE_LINE(self, t):
        return t
```
코드 `code{codeblock-lexer}`

`MarkdownLexer` 에서 코드 블럭 태그를 만나면 `CodeblockLexer` 클래스로 토큰을 생성하는 역할을 넘겨받아 코드 블럭을 닫는 태그와 코드 레이블 토큰을 추출합니다. 코드 `code{codeblock-lexer}` 에서 `line{codeblock-lexer-code-end}` 번째 `CODE_END()` 함수를 살펴보면, 코드 블럭을 닫는 태그를 만나면 `self.begin(MarkdownLexer)` 함수를 호출해 토큰 생성 역할을 다시 `MarkdownLexer` 클래스로 넘겨 계속 이어가도록 합니다.

## MarkdownParser 클래스
`MarkdownParser` 클래스는 `MarkdownLexer` 에서 추출한 토큰과 `CodeblockLexer` 에서 추출한 토큰을 모아서 문법에 맞춰 파싱하는 역할을 담당합니다. 코드 `code{기술 문서 작성을 위한 마크다운 파서 개발/markdown-bnf}` 에서 정의한 BNF 문법을 함수 단위로 분리해서 구현합니다.

### 마크다운 구문 분석 규칙
```python markdown-parser-doc
class MarkdownParser(Parser):
    tokens = MarkdownLexer.tokens + CodeblockLexer.tokens
    debugfile = "markdown_parser.out"

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
```
코드 `code{markdown-parser-doc}`

`MarkdownParser` 클래스에서 `doc` 구문을 분석하기 위해 총 네 개의 함수를 구현하고 있습니다. 각 함수에서는 `doc : doc para` 등의 규칙에 따라 오른쪽에 있는 문장들을 그대로 더해 합쳐진 문장을 생성합니다.

```python markdown-parser-title
    @_('TITLE')
    def para(self, p):
        self.enhancer.add_chapter(p.TITLE)
        return p.TITLE

    @_('sentence_list')
    def para(self, p):
        return p.sentence_list

    @_('sentence_list sentence')
    def sentence_list(self, p):  <<-- markdown-parser-title-sentence-list
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
```
코드 `code{markdown-parser-title}`

이어서 `para : TITLE`, `para : sentence_list` 문법 규칙을 정의합니다. `para` 규칙은 `TITLE` 한 문장을 가지거나 `sentence_list` 로 구성되는데, `sentence_list` 는 여러 개의 `sentence` 를 가질 수 있습니다.

`line{markdown-parser-title-sentence-list}` 번째 정의된 `sentence_list(self, p)` 함수는 `sentence_list : sentence_list sentence` 규칙을 구현합니다. `sentence_list` 와 `sentence` 문장 사이에 공백을 넣어서 더하는 작업을 수행합니다. 만약 `sentence_list` 문자열의 가장 마지막에 개행문자(`'\n'`)를 가지고 있다면 새로운 줄이 시작된 것으로 판단하고 공백을 더하지 않고 그냥 두 문장을 더해 완성합니다.

### 참조 태그 추출 규칙

```python markdown-parser-ref
    @_('REF_CODE')
    def sentence(self, p):
        chapter, reference, prefix, postfix = self.enhancer.find_ref_name(p.REF_CODE, "code{")
        code_index = self.enhancer.find_code_label(chapter, reference)  <<-- markdown-parser-ref-enhancer

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
```
코드 `code{markdown-parser-ref}`

`sentence : REF_CODE` 등의 규칙을 코드 블럭 이름이나 라인 이름, 그림 등과 같은 참조 태그를 만나면 `MarkdownEnhancer` 클래스를 이용해 참조하는 대상을 찾아 인덱스 정보를 `01` 혹은 `01-01` 과 같은 형태로 치환해 돌려주도록 구현하였습니다.

`find_ref_name()` 함수는 참조 태그 문자열과 태그의 앞 부분 문자열을 인자로 받아 실제 참조하는 대상을 찾아서 반환합니다. 예를 들어 `find_ref_name('code{markdown-bnf}', 'code{')` 함수를 호출하면 현재 챕터 정보를 담고 있는 객체와 `markdown-bnf` 문자열을 얻을 수 있습니다.
`find_code_label()` 함수에 챕터 정보와 `markdown-bnf` 문자열을 인자로 호출하면, `01-01` 과 같은 형태의 인덱스 정보를 얻을 수 있습니다.

### 코드 블럭 추출 규칙
```python markdown-parser-codeblock
    @_('CODE_BEGIN code_block CODE_END',
       'CODE_BEGIN_WITH_LANGUAGE code_block CODE_END')
    def code(self, p):  <<-- markdown-parser-codeblock-code
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
```
코드 `code{markdown-parser-codeblock}`

코드 블럭을 추출하기 위해 `CODE_BEGIN` 토큰과 `CODE_END` 토큰을 이용해 규칙을 정의합니다. 마크다운에서 일반적으로 사용하는 코드 블럭은 단순하게 "\`\`\`" 태그로 시작하는 경우와 "\`\`\`python" 등과 같은 형태로 내부 코드의 언어를 정의하는 경우가 있습니다. 코드 블럭 내부 언어를 정의하는 토큰은 "\`\`\`python" 같은 형태로 코드 블럭 시작 토큰에 이어서 바로 언어가 나타납니다. `line{markdown-parser-codeblock-code}`  번에 정의된 `code()` 함수에서 이 두 가지 토큰 조합을 모두 인식해 변경 없이 그대로 반환합니다.

`CODE_LABEL` 토큰은 코드 블럭 시작 태그 이후에 한 칸의 공백 다음에 위치합니다. `CODE_LABEL` 토큰을 가진 코드 블럭인 경우에는 `enhancer.add_codeblock()` 함수를 호출해 해당 레이블과 코드 자체를 등록합니다. 그리고 줄 번호가 추가된 코드를 얻게 되어 이렇게 변경된 코드 블럭 내용을 반환합니다.

### 문법 오류 처리
```python markdown-parser-error
    def error(self, p):
        if p:
            print(f"Syntax error at token {p.type} {p.value}")
            return self.errok()
        else:
            print("Syntax error at EOF")
```
코드 `code{markdown-parser-error}`

문법 규칙에 따라 파싱하는 데 실패하면 `error()` 함수가 호출되어 어떤 토큰을 만나 오류가 발생하게된 토큰을 출력하고 이어서 다음 토큰을 이용해 파싱을 계속 진행하도록 `self.errok()` 함수 값을 반환합니다.

## ChapterContent 클래스
챕터별로 저장해야할 정보가 많아 챕터 단위 정보를 `ChapterContent` 데이터클래스로 분리해 저장하도록 구현하였습니다.

```python chapter-content
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
```
코드 `code{chapter-content}` 

코드 블럭 안에 저장된 코드 혹은 참조 대상이 되는 데이터는 파싱 단계에서 `MarkdownEnhancer` 클래스를 통해 `ChapterContent` 데이터클래스 안에 저장됩니다.

## MarkdownEnhancer 클래스

코드 블럭에 줄 번호를 추가하거나 참조할 대상을 찾아 인덱스 정보를 반환하는 모든 작업은 실제로 `MarkdownEnhancer` 클래스를 통해서 이루어집니다. `MarkdownEnhancer` 클래스 안에는 챕터별 정보를 저장하고 코드 블럭을 변환하거나 참조 대상을 찾는 함수를 구현하고 있습니다.

```python markdown-enhancer-init
class MarkdownEnhancer:
    chapter_number: int
    chapter_name_map: Dict[str, ChapterContent]
    chapter_number_map: Dict[int, ChapterContent]
    line_label_indicator: str

    def __init__(self, line_label_indicator="<--"):
        self.chapter_number = 0
        self.chapter_name_map = {}  # chapter_name -> ChapterContent
        self.chapter_number_map = {}  # chapter_number -> ChapterContent
        self.line_label_indicator = line_label_indicator
```
코드 `code{markdown-enhancer-init}`

### 챕터 추가 및 검색

`MarkdownEnhancer` 클래스에는 챕터별 정보를 저장하는 `ChapterContent` 를 이름이나 챕터 번호로 찾을 수 있게 `Dict` 구조체 안에 저장하고 있습니다. `ChapterContent` 데이터클래스는 새로운 `TITLE` 토큰을 만날 때마다 생성되어 추가됩니다.

```python markdown-enhancer-add-chapter
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
```
코드 `code{markdown-enhancer-add-chapter}` 

`MarkdownParser` 에서 새로운 `TITLE` 토큰을 만나면 `add_chapter()` 함수를 호출해 새로운 챕터 데이터클래스를 생성합니다. 참조하는 태그를 만나면 현재 챕터 정보를 얻기 위해 `find_chapter()` 함수를 호출해 챕터 정보를 얻고 그 안에서 원하는 참조 대상을 검색합니다.

### 레이블을 가진 코드 블럭 처리

```python markdown-enhancer-add-codeblock
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
```
코드 `code{markdown-enhancer-add-codeblock}`

코드 레이블을 가지고 있는 코드 블럭  `add_codeblock()` 함수에 레이블과 코드를 인자로 넘겨 챕터에 등록합니다. 이 때 이미 존재하는 코드 레이블을 사용할 경우에는 `ref_codeblock()` 함수를 호출해 저장되어 있는 코드 내용을 바로 반환합니다. 새로운 코드 레이블을 가지고 있다면, 코드를 챕터 안에 등록하고 줄 번호를 붙인 코드 블럭을 생성합니다.

```python markdown-enhancer-make-numbered-codes
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

```
코드 `code{markdown-enhancer-make-numbered-codes}`

`make_numbered_codes()` 함수는 코드를 한 줄씩 읽어서 줄 번호를 맨 앞에 붙여 새로운 코드를 생성합니다. 동시에 레이블을 가지고 있는 라인을 찾기 위해서 `extract_line_label()` 함수를 호출합니다. 만약에 레이블을 가지고 있는 라인이 존재한다면 해당 레이블과 라인 번호를 챕터 안에 기록해둡니다.

만약에 이미 존재하는 코드 블럭을 다시 만난 상황이라면 `ref_codeblock()` 함수가 호출됩니다.

```python markdown-enhancer-ref-codeblock
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
```
코드 `code{markdown-enhancer-ref-codeblock}`

`ref_codeblock()` 함수에서는 이미 존재하는 코드 블럭을 바로 출력하지 않고 라인 레이블을 가지고 있는지 여부를 확인합니다. 아무 레이블도 가지고 있지 않다면 줄 번호를 1번부터 시작해 붙여서 반환합니다. 만약 이미 등록된 라인 레이블을 찾았다면 해당 레이블이 가지고 있었던 줄 번호를 참조해 코드 블럭의 시작 줄 번호를 조정합니다. 결과적으로 라인 레이블이 존재하는 코드 블럭은 위와 아래에 얼마나 많은 코드가 존재하는지에 상관없이 동일한 줄 번호를 출력하게 됩니다.

### 참조 대상 검색

```python markdown-enhancer-find-code
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
```
코드 `code{markdown-enhancer-find-code}`

코드 레이블이나 라인 레이블을 이용해 참조하는 대상을 지정하면 `find_code_label()` 함수 혹은 `find_line_label()` 함수가 호출됩니다. `find_code_label()` 함수는 참조하는 대상 코드가 챕터에서 몇 번째 인덱스를 가지고 있는지 찾아서 반환합니다. `find_line_label()` 함수는 참조하는 라인이 몇 번째 라인에 위치하는지 찾아서 반환합니다.

```python markdown-enhancer-find-figure
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
```
코드 `code{markdown-enhancer-find-figure}`

마크다운 문서 내에서 그림이나 표 혹은 챕터 이름을 참조하는 경우에는 각각의 함수가 호출되어 인덱스를 반환합니다. 그림과 표 레이블은 처음 검색을 시도할 때 챕터에 등록되고 이후에는 인덱스를 반환하는 역할만 수행합니다.

# 참고 자료
* [PLY (Python Lex-Yacc)](https://www.dabeaz.com/ply/)
* [SLY (Sly Lex Yacc)](https://sly.readthedocs.io/en/latest/sly.html)
* [Backus–Naur form - Wikipedia](https://en.wikipedia.org/wiki/Backus%E2%80%93Naur_form)
* [Daring Fireball: Markdown](https://daringfireball.net/projects/markdown/)
* [코마 마크다운파서](https://navilera.com/%EC%BD%94%EB%A7%88/2022-06-19-coma-val)
