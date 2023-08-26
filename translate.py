import openai
import os
import tiktoken
import re


PATH = '/Users/timurkusainov/Desktop/Machine_Learning/translate/test'
MODEL_NAME = 'gpt-3.5-turbo'
MODEL_LIMIT = 1000
MODEL_TEMP = 0.9
MODEL_TIMEOUT = 10
LIMIT = 500
BY_LINE = True
COUNT = 1
ADD_SEP = True
OUTPUT_RESULT = True

openai.api_key = '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'
os.chdir(PATH)
encoding = tiktoken.encoding_for_model(MODEL_NAME)


def get_path_to_file(ext:str='vtt') -> list[str]:
    paths = list()
    for dir in os.walk('.'):
        current_dir = os.path.basename(dir[0])
        if current_dir == 'temp': continue
        for file in dir[2]:
            if file.endswith('.' + ext):
                paths.append(os.path.abspath(os.path.join(dir[0], file)))
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
        max_tokens=MODEL_LIMIT,
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


def split_text(text:str, limit=1200, by_line=False, count=1) -> list[str]:
    if by_line:
        list_batches = re.split(r'\n', text)
        if count > 1:
            buffer = []
            while list_batches:
                buffer.append('\n'.join([list_batches.pop(0) for _ in range(count) if list_batches]))
            list_batches = buffer
    else:
        split_text = re.split(r'(?<=\n)', text)
        batch = ''
        list_batches = []
        for line in split_text:
            batch += line
            if get_token_size(batch) >= limit:
                batch = re.sub(r'\n$', '', batch)
                list_batches.append(batch)
                batch = ''
        if batch:
            batch = re.sub(r'\n$', '', batch)
            list_batches.append(batch)
    return list_batches

def save_text(path, text):
    with open(path, 'w') as file:
        file.write(text)


def split_by_procentage(line, count_words:list[int]):
    total_words = sum(count_words)
    total_subtitles = len(count_words)
    words_line = re.findall(r'[^\s]+', line)
    symbols_line = sum(len(word) for word in words_line)
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
    subtitles = 'WEBVTT\n'
    for number, timestamp, subtitle in list_subtitles:
        buffer = f'\n{number}\n{timestamp}\n'
        line = ''
        for word in re.findall(r'[^\s]+', subtitle):
            line = line + (' ' if line else '') + word
            if len(line) > 35:
                buffer += (line + '\n')
                line = ''
        if line:
            buffer += (line + '\n')
        subtitles += buffer
    return subtitles


def text_timestamp_split(text:str) -> tuple[str, list[list[str]], list[list[int]]]:
    timestamp = r'(\d{2}:\d{2}:\d{2}.\d{3} --> \d{2}:\d{2}:\d{2}.\d{3})' 
    text = re.sub(r'^[\s\nWEBVT]*|\n*$', '', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'^\d+\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n', ' ', text)
    timestamps = re.findall(timestamp, text)
    text = re.sub(timestamp, '\n', text)
    text = re.sub(r'^\s*|\s$', '', text, flags=re.MULTILINE)
    list_lines = list(zip(timestamps, text.split('\n')))
    list_timestamp_lines = []
    list_count_words = []
    buffer = ''
    text = ''
    for timestamp, line in list_lines:
        split_line = re.split(r'(?<=[!?.])(?=$|\s)', line)
        for next_n, line in enumerate(split_line, 1):
            line = line.strip(' ')
            if buffer: 
                buffer = buffer + ' ' + line
            else:
                buffer += line
                list_timestamp_lines.append([])
                list_count_words.append([])
            words = re.split(r'\s+', line)
            list_count_words[-1].append(len(words))
            list_timestamp_lines[-1].append(timestamp)
            try:
                next = split_line[next_n]
            except IndexError:
                pass
            else:
                text = text + ('\n|| ' if text else '|| ') + buffer
                buffer = ''
                if not next: break
    return text, list_timestamp_lines, list_count_words


def text_timestamp_joint(text:str, list_timestamp_lines: list[list[str]], 
                         list_count_words: list[list[int]]) -> str:
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n+', '', text)
    text = re.sub(r'^[|\s]+', '', text)
    text_list = re.split(r'\|\|\s*', text)    
    if len(text_list) != len(list_timestamp_lines):
        raise Exception('The length doesn\'t match')
    last_timestamp = ''
    count = 0
    list_subtitles = []
    for i in range(len(text_list)):
        timestamps = list_timestamp_lines[i]
        line = text_list[i]
        captions = split_by_procentage(line, list_count_words[i])
        for k in range(len(timestamps)):
            timestamp = timestamps[k]
            caption = captions[k]
            if timestamp != last_timestamp:
                count += 1
                list_subtitles.append([count, timestamp, caption])
            else:
                last_caption = list_subtitles[-1][-1]
                list_subtitles[-1][-1] = last_caption + ' ' + caption
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
        text = get_text(path)
        text, list_timestamp_lines, list_count_words = text_timestamp_split(text)
        list_batches = split_text(text, LIMIT, BY_LINE, COUNT) 
        translated_text = ''
        for n, batch_text in enumerate(list_batches, 1):
            trying = 1
            while True:
                try:
                    print(f'Start translate {n} of {len(list_batches)} bathces')
                    if OUTPUT_RESULT: print(batch_text)
                    translated_batch_text = translate_text(batch_text)
                except Exception as e:
                    print(e)
                    if trying == 3:
                        exit(1)
                    trying += 1
                    print(f'Trying #{trying}')
                else:
                    if OUTPUT_RESULT: print(translated_batch_text)
                    if BY_LINE:
                        translated_batch_text = re.sub(r'^[|\s\n]*|[|\s\n]*$', '', translated_batch_text)
                        translated_batch_text = re.sub(r'\s*\n+\s*', ' ', translated_batch_text)
                        translated_batch_text = re.sub(r'^', '|| ', translated_batch_text)
                    elif ADD_SEP:
                        translated_batch_text = re.sub(r'^[|\s]*', '|| ', translated_batch_text, re.MULTILINE)
                    if OUTPUT_RESULT: print(translated_batch_text)
                    translated_text += (('\n' if translated_text else '') + translated_batch_text)
                    break
        text = text_timestamp_joint(translated_text, list_timestamp_lines, list_count_words)
        os.rename(path, temp_file_path)
        save_text(path, text)

if __name__ == '__main__':
    main()
