import os
from typing import List


PATH = '/Users/timurkusainov/Desktop/Machine_Learning/translate/courses/ai_for_all'
os.chdir(PATH)


def get_path_to_file(ext:str='vtt') -> List[str]:
    paths = list()
    for dir in os.walk('.'):   
        folder = os.path.basename(dir[0])
        if folder == 'temp':
            for file in dir[2]:
                if file.endswith('.' + ext):
                    paths.append(os.path.abspath(os.path.join(dir[0], file)))
    print(f'Found {len(paths)} files')
    return paths


def main():
    paths = get_path_to_file()
    for path_file_temp in paths:
        path_temp, file_name = os.path.split(path_file_temp)
        path_file, _ = os.path.split(path_temp)
        path_file = os.path.join(path_file, file_name)
        os.remove(path_file)
        os.rename(path_file_temp, path_file)

        
if __name__ == '__main__':
    main()
