import openai
import os
import tiktoken
import re


PATH = '/Users/timurkusainov/Desktop/Machine_Learning/translate/courses/ai_for_all'
MODEL_NAME = 'gpt-3.5-turbo'
MODEL_TEMP = 0.85
MODEL_TIMEOUT = 10
MODEL_TOKEN_LIMIT = 1000

openai.api_key = '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'
os.chdir(PATH)
os.system('clear')
encoding = tiktoken.encoding_for_model(MODEL_NAME)


def get_path_to_file(ext:str='vtt') -> list[str]:
    paths = list()
    for dir in os.walk('.'):
        current_dir = os.path.basename(dir[0])
        if current_dir == 'temp': continue
        for file in dir[2]:
            if file.endswith('.' + ext):
                paths.append(os.path.join(dir[0], file))
    print(f'Found {len(paths)} files')
    return paths


def translate_text(text, source_language='English', target_language='Russian'):
    prompt = f"Translate text from {source_language} to {target_language}:\n{text}"
    response = openai.ChatCompletion.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "You are a interpreter."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=MODEL_TOKEN_LIMIT,
        n=1,
        stop=None,
        temperature=MODEL_TEMP,
        request_timeout=MODEL_TIMEOUT,
    )
    translation = response.choices[0].message.content.strip()
    return translation


def get_token_size(text):
    return len(encoding.encode(text))


def get_text(path):
    with open(path) as file:
        text = ''.join(file.readlines()) 
    return text


def split_text(text:str) -> list[str]:
    list_lines = re.split(r'\n', text)
    return list_lines


def save_text(path, text):
    with open(path, 'w') as file:
        file.write(text)


def split_by_procentage(line, count_words:list[int]):
    total_words = sum(count_words)
    total_subtitles = len(count_words)
    words_line = re.findall(r'[^\s]+', line)
    list_lines = []
    for n in range(total_subtitles):
        percent = count_words[n] / total_words
        limit = len(words_line) * percent
        line = ''
        use_words = 1
        while words_line and (use_words <= limit or total_subtitles == (n + 1)):
            use_words += 1
            line = line + (' ' if line else '') + words_line.pop(0)
        total_words -= count_words[n]
        list_lines.append(line)
    return list_lines


def create_subtitle(list_subtitles) -> str:
    subtitles = 'WEBVTT'
    for number, timestamp, subtitle in list_subtitles:
        buffer = f'\n\n{number}\n{timestamp}'
        line = ''
        for word in re.findall(r'[^\s]+', subtitle):
            line = line + (' ' if line else '') + word
            if len(line) > 35:
                buffer += ('\n' + line)
                line = ''
        if line:
            buffer += ('\n' + line)
        subtitles += buffer
    return subtitles



def text_split_by_line(text:str) -> tuple[list[str], list[list[str]], list[list[int]]]:
    timestamp = r'(\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3})' 
    text = re.sub(r'^[\s\nWEBVT]*', '', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'^\d+\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n', ' ', text)
    timestamps = re.findall(timestamp, text)
    text = re.sub(timestamp, '\n', text)
    text = re.sub(r'^\s*|\s$', '', text, flags=re.MULTILINE)
    list_line_subtitles = list(zip(timestamps, text.split('\n')))
    list_line_timestamps = []
    list_count_words = []
    buffer = ''
    list_lines = []
    for timestamp, line in list_line_subtitles:
        split_line = re.split(r'(?<=[!?.])(?=$|\s)', line)
        for n, line in enumerate(split_line):
            line = line.strip(' ')
            if buffer: 
                buffer = buffer + ' ' + line
            else:
                buffer += line
                list_line_timestamps.append([])
                list_count_words.append([])
            words = re.split(r'\s+', line)
            list_count_words[-1].append(len(words))
            list_line_timestamps[-1].append(timestamp)
            if n+1 < len(split_line):
                next_line = split_line[n+1]
                list_lines.append(buffer)
                buffer = ''
                if not next_line: break
    return list_lines, list_line_timestamps, list_count_words


def text_timestamp_joint(list_translated_lines:list[str], 
                         list_line_timestamps: list[list[str]], 
                         list_count_words: list[list[int]]) -> str:
    last_timestamp = ''
    count = 0
    list_subtitles = []
    for line, timestamps, count_words in zip(list_translated_lines, list_line_timestamps, list_count_words):
        line = re.sub(r'^\s+|\s+$', '', line)
        line = re.sub(r'[\n\s]+', ' ', line)
        captions = split_by_procentage(line, count_words)
        for timestamp, caption in zip(timestamps, captions):
            if timestamp != last_timestamp:
                count += 1
                list_subtitles.append([count, timestamp, caption])
            else:
                list_subtitles[-1][-1] = list_subtitles[-1][-1] + ' ' + caption
            last_timestamp = timestamp    
    subtitles = create_subtitle(list_subtitles)
    return subtitles


def main():
    paths = get_path_to_file('vtt')
    for n_path, path in enumerate(paths, 1):
        print(f'Start translate {n_path} of {len(paths)} files')
        dir_path = os.path.dirname(path)
        file_name = os.path.basename(path)
        temp_path = os.path.join(dir_path, 'temp')
        if not os.path.exists(temp_path): os.mkdir(temp_path)
        temp_file_path = os.path.join(temp_path, file_name)
        if os.path.exists(temp_file_path): continue
        subtitles = get_text(path)
        list_lines, list_line_timestamps, list_count_words = text_split_by_line(subtitles)
        list_translated_lines = []
        for n, line in enumerate(list_lines, 1):
            status_string = f'Translating "{path}" file #{n_path} of {len(paths)}, line #{n} of {len(list_lines)} '
            print(status_string)
            for trying in range(1, 4):
                try:
                    translated_line = translate_text(line)
                except Exception as e:
                    print(f'Timeout {trying} time')
                else:
                    list_translated_lines.append(translated_line)
                    break
        subtitles_translated = text_timestamp_joint(list_translated_lines, list_line_timestamps, list_count_words)
        os.rename(path, temp_file_path)
        save_text(path, subtitles_translated)

if __name__ == '__main__':
    main()
