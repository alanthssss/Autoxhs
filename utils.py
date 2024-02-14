import json
import os
import re
import os
import time

def create_directory_for_post(save_path ="data/posts"):
    save_path = os.path.join(save_path,time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime()))
    os.mkdir(save_path)
    return save_path

def save_post_to_file(post_data, directory):
    """
    保存贴文数据到JSON文件中。
    
    :param post_data: 包含贴文信息的字典。
    :param directory: 保存贴文的目录路径，默认为"data/posts"。
    """

    filename = f"post.md"
    filepath = os.path.join(directory, filename)
    
    # 将贴文数据以JSON格式写入文件
    with open(filepath, 'w', encoding='utf-8') as file:
        json.dump(post_data, file, ensure_ascii=False, indent=4)
        
    print(f"贴文已保存到文件：{filepath}")

def remove_hash_and_asterisk(input_string):
    cleaned_string = re.sub(r'#{2,}', '', input_string)
    cleaned_string = cleaned_string.replace("*", "")
    return cleaned_string

def beauty_print(data: dict):
    print(json.dumps(data, ensure_ascii=False, indent=2))

def trans_into_md(note_data):
    # 构建Markdown字符串
    markdown_content = """
    <div align="center">{title}</div>
    {description}
    """.format(title=note_data["title"], description=note_data["description"])
    
    return markdown_content

def trans_into_html(note_data):
    # 构建HTML字符串，注意这里使用了<div>来实现居中等样式
    html_content = f"""
    <div style="text-align: center;"><h2>{note_data["title"]}</h2></div>
    <p>{note_data["description"]}</p>
    <p><b>主题标签：</b>{note_data["topics"]}</p>
    """
    return html_content
