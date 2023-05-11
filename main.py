import re
import time

from deep_translator import GoogleTranslator

en_constants = ['y', 'd', 'h', 'm', 's', 'ms']
ru_constants = ['г', 'д', 'ч', 'м', 'с', 'мс']
between = True
FILE = 'example.txt'
TO = 'ru'
FROM = 'en'


def get_string(text):
    pos1, pos2 = -1, -1
    c = ''
    for i in range(len(text)):
        if text[i] == '\'' or text[i] == '\"':
            pos1 = i
            c = text[i]
            break
    if pos1 == -1:
        return None
    for i in range(len(text) - 1, pos1, -1):
        if text[i] == c:
            pos2 = i
            break
    if pos2 == -1:
        return None
    if len(text[pos1 + 1:pos2]) == 0:
        return None
    return text[pos1 + 1:pos2]


def check_string(line):
    pos1, pos2 = -1, -1
    line += ' '
    for j in range(len(line)):
        if (line[j] == '\'' or line[j] == '\"') and (
                line[j - 1] == ' ' or line[j - 1] == '='
                or line[j - 1] == ':'):
            pos1 = j
            break
    for j in range(len(line) - 1, pos1, -1):
        if (line[j] == '\'' or line[j] == '\"') and (
                line[j - 1] in [' ', '.', '!', '?', ']', '}', ')', '"']
                or '\n' in line[j + 1] or ' ' in line[j + 1]):
            pos2 = j
            break
    return pos1, pos2


def check_is_word(text, index):
    text = '  ' + text + '   '
    index += 2
    if (text[index - 1] == ' '
        or text[index - 1] == '%'
        or text[index - 3] == '&') and (
            text[index + 1] == ' '
            or text[index + 1] == '%' or text[index + 2] == '&'):
        return True
    return False


def get_translate(text):
    text = text.strip()
    temp = ''
    i = 0
    for i in range(len(text)):
        if text[i] in en_constants:
            if check_is_word(text, i):
                temp += ru_constants[en_constants.index(text[i])]
                continue
        temp += text[i]
    text = temp
    if has_english(text):
        return GoogleTranslator(source=FROM, target=TO).translate(text)
    return text


def replace_substring(TEXT_TR, match_tr, match):
    if any(symbol in match_tr for symbol in '&{}[]-'):
        match_tr = f'%{match_tr}%'
    return TEXT_TR.replace(match_tr, match)


def has_russian(text):
    pattern = re.compile("[а-яА-ЯёЁ]+")
    return bool(pattern.search(text))


def has_english(text):
    pattern = re.compile("[a-zA-Z]+")
    return bool(pattern.search(text))


start_time = time.time()
with open(FILE, encoding='utf-8') as f:
    lines = f.readlines()
lines_formatted = []
translated_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    flag = False
    pos1, pos2 = check_string(line)
    j = 0
    if pos2 == -1 and pos1 != -1:
        for j in range(1, 11):
            if i + j > len(lines) - 1:
                break
            line += lines[i + j].strip()
            line = line.replace("\n", " ")
            poss1, poss2 = check_string(line)
            if poss1 != -1 and poss2 != -1:
                flag = True
                break
    if not flag:
        lines_formatted.append(lines[i])
        i += 1
        continue
    else:
        i += j
    lines_formatted.append(line + '\n')
    i += 1
lines = lines_formatted
comment_block = False
block_index = -1
for count in range(len(lines)):
    if count % 5 == 0:
        print(format(count * 100 / len(lines), '.1f'), '%', sep='')
    text = get_string(lines[count])
    if (comment_block or text is not None
        or ': |' in lines[count]) and lines[count] != '\n' and all(
        tag not in str(text) for tag
        in ['<div class=', '<span style=', '<p>', '</p>']):
        if comment_block:
            lines[count] += ' '
            if re.search(r'\S', lines[count]).start() < block_index:
                comment_block = False
                if text is None:
                    translated_lines.append(lines[count])
                    continue
            else:
                text = str(lines[count][re.search(r'\S', lines[count]).start():])
        if ': |' in str(lines[count]):
            comment_block = True
            block_index = re.search(r"\S", lines[count + 1]).start()
            translated_lines.append(lines[count])
            continue
        text = str(text).strip()
        original = text
        temp = ''
        mapping = {'{': '%{', '}': '}%', '[': '%[', ']': ']%'}
        temp = ""
        i = 0
        flag = False
        DEF = ''
        while i < len(text):
            if text[i] in mapping:
                if not flag:
                    temp += mapping[text[i]]
                    flag = True
                    DEF = text[i]
                else:
                    if text[i] == list(mapping.keys())[list(mapping.keys()).index(DEF) + 1]:
                        flag = False
                        temp += list(mapping.values())[list(mapping.keys()).index(DEF) + 1]
                    else:
                        temp += text[i]
            elif text[i] == '&' and not flag:
                temp += '%&' + text[i + 1] + '%'
                i += 1
            elif text[i] == '-' and not flag:
                temp += '%-%'
            else:
                temp += text[i]
            i += 1
        text = temp
        matches = re.findall(r"%([^%]*)%", text)
        TEXT_TR = str(get_translate(text))
        TEXT_TR = TEXT_TR.replace('%%%', '%%')
        matches_tr = list(re.findall(r"%([^%]*)%", TEXT_TR))

        for match_tr, match in zip(matches_tr, matches):
            if not has_russian(match_tr):
                match = match_tr
            TEXT_TR = replace_substring(TEXT_TR, match_tr, match)
        if between:
            results = re.findall(r'\$([^$]*)\$', TEXT_TR)
            for result in results:
                RESULT = str(get_translate(result))
                if not ' ' in result:
                    RESULT = RESULT.replace(' ', '_')
                TEXT_TR = TEXT_TR.replace('$' + result + '$', '$' + RESULT + '$')
        lines[count] = lines[count].replace(original, TEXT_TR)
    translated_lines.append(lines[count])
with open(FILE, 'w', encoding='utf-8') as f:
    f.writelines(translated_lines)
end_time = time.time()
elapsed_time = end_time - start_time

minutes, seconds = divmod(elapsed_time, 60)
seconds, milliseconds = divmod(seconds, 1)

print(
    f"Функция выполнилась за {int(minutes):02d} минут {int(seconds):02d} секунд {int(milliseconds * 1000):03d} миллисекунд")
