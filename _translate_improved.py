import os
import shutil
from openai import OpenAI
from dotenv import load_dotenv
import hashlib
import yaml

load_dotenv()
client = OpenAI()
languages = [
    {"name": "arabic", "code": "ar"},
    {"name": "italian", "code": "it"},
    {"name": "russian", "code": "ru"},
    {"name": "chinese", "code": "zh"},
    {"name": "french", "code": "fr"},
    {"name": "greek", "code": "gr"},
    {"name": "hebrew", "code": "he"},
    {"name": "portuguese", "code": "pt"},
    {"name": "spanish", "code": "es"},
]

def translate(text, target_language):
    """Translate text to target language using OpenAI's GPT"""
    # if text is empty, return empty
    if not text:
        return ""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text to {target_language}: {text}",
            },
        ]
    )
    return response.choices[0].message.content.strip()

def calculate_file_hash(file_path):
    """Calculate MD5 hash for a given file"""
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5(f.read()).hexdigest()
    return file_hash

def scan_directory_for_files(directory, file_filter=None):
    """
    Scan directory for files matching optional filter
    file_filter: function that takes filename and returns boolean
    """
    files_info = []
    if os.path.exists(directory):
        for root, _, files in os.walk(directory):
            for file in files:
                if file_filter is None or file_filter(file):
                    file_path = os.path.join(root, file)
                    hash = calculate_file_hash(file_path)
                    if file.endswith("-en.md"):
                        target_path_template = file_path.replace("-en.md", "-__LANG_CODE__.md")
                    else:
                        target_path_template = file_path.replace("/en/", f"/__LANG_CODE__/")
                    files_info.append({
                        "path": file_path,
                        "hash": hash,
                        "target_path_template": target_path_template
                    })
    return files_info

def get_source_hash_from_file(file_path):
    """
    Extract source_hash from either markdown frontmatter or yaml file
    Returns None if source_hash is not found
    """
    if not os.path.exists(file_path):
        return None
        
    if file_path.endswith('.md'):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for frontmatter between --- markers
            if content.startswith('---'):
                try:
                    # Find the second --- that closes frontmatter
                    end_idx = content.index('---', 3)
                    frontmatter = content[3:end_idx]
                    # Parse frontmatter as YAML
                    metadata = yaml.safe_load(frontmatter)
                    return metadata.get('source_hash')
                except:
                    return None
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                data = yaml.safe_load(f)
                return data.get('source_hash')
            except:
                return None
    
    return None

def translate_markdown_file(source_filepath, source_hash, target_filepath, language, language_code):
    """Translate a markdown file"""
    print(f"\nProcessing markdown file: {source_filepath}")
    
    with open(source_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the content into frontmatter and body
    parts = content.split("---")
    if len(parts) < 3:
        print(f"⚠️  Skipping {source_filepath} - Invalid frontmatter format")
        return

    frontmatter = parts[1]
    body = parts[2]

    # Translate frontmatter values
    translated_frontmatter = []
    for line in frontmatter.splitlines():
        if line.startswith(("  title:", "  subtitle:", "title:", "subtitle:", "alt:")):
            key, value = line.split(": ", 1)
            translated_value = translate(value.strip(), language)
            translated_frontmatter.append(f"{key}: {translated_value}")
        elif line.startswith(("lang:", "lang:")):
            translated_frontmatter.append(f"lang: {language_code}")
        else:
            translated_frontmatter.append(line)
    
    translated_frontmatter.append(f"source_hash: {source_hash}")
    translated_frontmatter = "\n".join(translated_frontmatter)

    translated_body = translate(body.strip(), language)

    # Combine translated frontmatter and body
    translated_content = f"---\n{translated_frontmatter}\n---\n{translated_body}"

    print(f"✅ Writing translated content to {target_filepath}")
    # Write the translated content back to the file
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(translated_content)

def translate_yaml_file(source_filepath, source_hash, target_filepath, language, language_code):
    """Translate a yaml file"""
    print(f"\nProcessing yaml file: {source_filepath}")
    with open(source_filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Translate the content
    translated_content = translate(content, language)
    
    # add source_hash and lang to the content
    translated_content = f"source_hash: {source_hash}\n{translated_content}"
    
    # Ensure target directory exists
    target_dir = os.path.join("_data", language_code)
    os.makedirs(target_dir, exist_ok=True)
    
    # Write the translated content back to the file
    print(f"✅ Writing translated content to {target_filepath}")
    with open(target_filepath, "w", encoding="utf-8") as f:
        f.write(translated_content)

def get_english_files_hashes():
    """Get hashes for all English content files"""
    translations = []
    
    # Scan _collections for -en.md files
    collections_files = scan_directory_for_files(
        "_collections", 
        lambda f: f.endswith("-en.md")
    )
    translations.extend(collections_files)
    
    # Scan _data/en for all files
    data_en_files = scan_directory_for_files(
        os.path.join("_data", "en")
    )
    translations.extend(data_en_files)
    
    # for every target language
    for lang in languages:
        # for every translation
        for translation in translations:
           # create target file path
           target_path = translation["target_path_template"].replace("__LANG_CODE__", lang["code"])
           # if the file exists and its content contains the hash, skip the file
           if os.path.exists(target_path) and translation["hash"] in open(target_path, "r", encoding="utf-8").read():
               print(f"⏭️  Skipping {target_path} - Already up to date")
               continue
           else:
               # if the file is a markdown file, translate it
               if translation["path"].endswith(".md"):
                   translate_markdown_file(translation["path"], translation["hash"], target_path, lang["name"], lang["code"])
               # if the file is a yaml file, translate it
               elif translation["path"].endswith(".yml") or translation["path"].endswith(".yaml"):
                   translate_yaml_file(translation["path"], translation["hash"], target_path, lang["name"], lang["code"])
           
    return translations

get_english_files_hashes()
