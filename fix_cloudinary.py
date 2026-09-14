import json
import os
import re

with open(os.path.expanduser('~/.cloudinary-cli/config.json'), 'r') as f:
    config = json.load(f)

default_env = config.get('__default__')
url = config.get(default_env)

# Parse URL
match = re.match(r'cloudinary://(.*)\?oauth_token=(.*)&refresh_token=.*', url)
cloud_name = match.group(1)
oauth_token = match.group(2)

def update_env_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    lines = content.split('\n')
    updated_lines = []
    found_url = False
    found_cloud = False
    found_token = False

    for line in lines:
        if line.startswith('CLOUDINARY_URL='):
            updated_lines.append(f'CLOUDINARY_URL="{url}"')
            found_url = True
        elif line.startswith('CLOUDINARY_CLOUD_NAME='):
            updated_lines.append(f'CLOUDINARY_CLOUD_NAME="{cloud_name}"')
            found_cloud = True
        elif line.startswith('CLOUDINARY_OAUTH_TOKEN='):
            updated_lines.append(f'CLOUDINARY_OAUTH_TOKEN="{oauth_token}"')
            found_token = True
        else:
            updated_lines.append(line)

    if not found_url:
        updated_lines.append(f'CLOUDINARY_URL="{url}"')
    if not found_cloud:
        updated_lines.append(f'CLOUDINARY_CLOUD_NAME="{cloud_name}"')
    if not found_token:
        updated_lines.append(f'CLOUDINARY_OAUTH_TOKEN="{oauth_token}"')

    with open(filepath, 'w') as f:
        f.write('\n'.join(updated_lines))

update_env_file('/workspaces/Zolexora_TMS/.env')
update_env_file('/workspaces/Zolexora_TMS/apps/tms-api/.env')
print("Successfully injected Cloudinary credentials")
