import os, shutil
import argparse
import zipfile

def zip_folder(folder_path, output_path):
    """
    将指定文件夹压缩为.zip文件

    :param folder_path: 要压缩的文件夹路径
    :param output_path: 压缩后的.zip文件路径
    """
    # 确保输出路径的文件扩展名为.zip
    if not output_path.endswith('.zip'):
        output_path += '.zip'

    # 创建一个ZipFile对象
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历文件夹中的所有文件和子文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 获取文件的完整路径
                file_path = os.path.join(root, file)
                # 获取文件在压缩包中的相对路径
                relative_path = os.path.relpath(file_path, folder_path)
                # 将文件添加到压缩包中
                zipf.write(file_path, "dist/"+relative_path)

parser = argparse.ArgumentParser(description='Build script for frontend')
parser.add_argument('--pre', action='store_true', help='pre handle')
parser.add_argument('--end', action='store_true', help='end handle')
args = parser.parse_args()

if args.pre:
    # del default url in frontend
    with open("frontend/src/main.js") as f:
        char  =f.read()

    with open("frontend/src/main.js", "w") as f:
        f.write(char.replace("axios.defaults.baseURL = 'http://127.0.0.1:8000'", 
                             "// axios.defaults.baseURL = 'http://127.0.0.1:8000'"))


elif args.end:

    file_lst = os.listdir('frontend/dist/assets')
    os.makedirs('frontend/dist/src')
    os.makedirs('frontend/dist/src/assets')
    for file in file_lst:
        if file.endswith('.png') and file.startswith('suzume'):
            new_file = file[:file.rfind('-')]+".png"
            shutil.copyfile('frontend/dist/assets/' + file, 'frontend/dist/src/assets/' + new_file)
    zip_folder('frontend/dist', 'frontend/dist.zip')
    # add default url in frontend
    with open("frontend/src/main.js", "r") as f:
        char  =f.read()

    with open("frontend/src/main.js", "w") as f:
        f.write(char.replace("// axios.defaults.baseURL = 'http://127.0.0.1:8000'", 
                             "axios.defaults.baseURL = 'http://127.0.0.1:8000'"))