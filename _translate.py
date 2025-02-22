import os
import shutil
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
languages = [
    {"name": "arabic", "code": "ar"},
    {"name": "italian", "code": "it"},
    {"name": "russian", "code": "ru"},
    {"name": "chinese", "code": "zh"},
    {"name": "french", "code": "fr"},
    {"name": "greek", "code": "gr"},
    {"name": "hebrew", "code": "he"}    
]

# Set your OpenAI API key on the terminal or in here
# openai.api_key = "your_openai_api_key"
# export OPENAI_API_KEY="your_api_key_here"


# Function to translate text using OpenAI's GPT-4
def translate(text, target_language):
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


# Navigate to the _collections directory
os.chdir("_collections")

# Calculate total work across all languages
total_languages = len(languages)
total_files = sum(1 for root, _, files in os.walk(".") 
                 for file in files if file.endswith("-en.md"))
total_work = total_languages * total_files * 2  # *2 because we copy and translate
overall_processed = 0

# Process each language
for lang_index, language in enumerate(languages, 1):
    print(f"\nProcessing translations for {language['name']} ({lang_index}/{total_languages})...")
    
    # Get total number of files to process
    print(f"Found {total_files} English files to process")

    processed_files = 0

    # First, remove any existing target language files
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(f"-{language['code']}.md"):
                filepath = os.path.join(root, file)
                os.remove(filepath)

    # Duplicate all files ending with -en.md to -{language_code}.md
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith("-en.md"):
                en_filepath = os.path.join(root, file)
                target_filepath = os.path.join(
                    root, file.replace("-en.md", f"-{language['code']}.md")
                )
                print(f"Copying {en_filepath} to {target_filepath}")
                shutil.copy(en_filepath, target_filepath)
                processed_files += 1
                overall_processed += 1
                lang_progress = (processed_files / total_files) * 100
                total_progress = (overall_processed / total_work) * 100
                print(f"Language Progress: {lang_progress:.1f}% ({processed_files}/{total_files})")
                print(f"Overall Progress: {total_progress:.1f}% ({overall_processed}/{total_work})")

    print(f"\nStarting translation process for {language['name']}...")
    # Reset counter for translation phase
    processed_files = 0
    total_translation_files = sum(1 for root, _, files in os.walk(".")
                                for file in files if file.endswith(f"-{language['code']}.md"))

    # Find all markdown files ending with -{language_code}.md and process them
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(f"-{language['code']}.md"):
                filepath = os.path.join(root, file)
                print(f"\nProcessing {filepath}")
                
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # Split the content into frontmatter and body
                parts = content.split("---")
                if len(parts) < 3:
                    print(f"Skipping {filepath} - Invalid frontmatter format")
                    continue

                print("Translating frontmatter...")
                frontmatter = parts[1]
                body = parts[2]

                # Translate frontmatter values
                translated_frontmatter = []
                for line in frontmatter.splitlines():
                    if line.startswith(
                        ("  title:", "  subtitle:", "title:", "subtitle:", "alt:")
                    ):
                        key, value = line.split(": ", 1)
                        translated_value = translate(value.strip(), language['name'])
                        translated_frontmatter.append(f"{key}: {translated_value}")
                    # if line starts with "lang:" change the whole line for "lang: {language_code}"
                    elif line.startswith("lang:"):
                        translated_frontmatter.append(f"lang: {language['code']}")
                    else:
                        translated_frontmatter.append(line)
                translated_frontmatter = "\n".join(translated_frontmatter)

                print("Translating body content...")
                translated_body = translate(body.strip(), language['name'])

                # Combine translated frontmatter and body
                translated_content = (
                    f"---\n{translated_frontmatter}\n---\n{translated_body}"
                )

                # Write the translated content back to the file
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(translated_content)

                processed_files += 1
                overall_processed += 1
                lang_progress = (processed_files / total_translation_files) * 100
                total_progress = (overall_processed / total_work) * 100
                print(f"Language Progress: {lang_progress:.1f}% ({processed_files}/{total_translation_files})")
                print(f"Overall Progress: {total_progress:.1f}% ({overall_processed}/{total_work})")

    print(f"\nTranslation completed for {language['name']}!")

print("\nAll translations completed successfully!")

# Return to parent directory to process sitetext.yml
print("\nProcessing sitetext.yml files...")
os.chdir("..")

# Process sitetext.yml for each language
for language in languages:
    print(f"\nProcessing sitetext.yml for {language['name']}...")
    
    # Ensure target directory exists
    target_dir = os.path.join("_data", language['code'])
    os.makedirs(target_dir, exist_ok=True)
    
    # Read English sitetext.yml
    with open(os.path.join("_data", "en", "sitetext.yml"), 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create translation prompt
    prompt = f"""translate every value of this yaml file to {language['name']}, except for those with a key called: section, internal-url, url, icon, and except for "languages. Do not wrap the response in markdown. Just return the resulting text".

{content}"""

    # Get translation
    translated_content = translate(prompt, language['name'])
    
    # Write translated YAML
    target_file = os.path.join(target_dir, "sitetext.yml")
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(translated_content)
    
    print(f"Completed sitetext.yml translation for {language['name']}")

print("\nAll translations completed successfully!")
