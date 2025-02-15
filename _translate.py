import os
from openai import OpenAI

client = OpenAI()
target_language = "arabic"
language_code = "ar"

# Set your OpenAI API key on the terminal or in here
# openai.api_key = "your_openai_api_key"
# export OPENAI_API_KEY="your_api_key_here"


# Function to translate text using OpenAI's GPT-4
def translate(text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"Translate the following text to {target_language}: {text}",
            },
        ],
        max_tokens=1000,
    )
    return response.choices[0].message.content.strip()


# Navigate to the _collections directory
os.chdir("_collections")

# Duplicate all files ending with -en.md to -{language_code}.md
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith("-en.md"):
            en_filepath = os.path.join(root, file)
            target_filepath = os.path.join(
                root, file.replace("-en.md", f"-{language_code}.md")
            )
            shutil.copy(en_filepath, target_filepath)


# Find all markdown files ending with -{language_code}.md and process them
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(f"-{language_code}.md"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            # Split the content into frontmatter and body
            parts = content.split("---")
            if len(parts) < 3:
                continue  # Skip files that don't have proper frontmatter

            frontmatter = parts[1]
            body = parts[2]

            # Translate frontmatter values
            translated_frontmatter = []
            for line in frontmatter.splitlines():
                if line.startswith(
                    ("  title:", "  subtitle:", "title:", "subtitle:", "alt:")
                ):
                    key, value = line.split(": ", 1)
                    translated_value = translate(value.strip())
                    translated_frontmatter.append(f"{key}: {translated_value}")
                # if line starts with "lang:" change the whole line for "lang: {language_code}"
                elif line.startswith("lang:"):
                    translated_frontmatter.append(f"lang: {language_code}")
                else:
                    translated_frontmatter.append(line)
            translated_frontmatter = "\n".join(translated_frontmatter)

            # Translate the body content
            translated_body = translate(body.strip())

            # Combine translated frontmatter and body
            translated_content = (
                f"---\n{translated_frontmatter}\n---\n{translated_body}"
            )

            # Write the translated content back to the file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(translated_content)
