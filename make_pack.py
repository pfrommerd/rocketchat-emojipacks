#!/usr/bin/env python3
import json
import yaml
import sys

if len(sys.argv) < 3:
    print("Usage: make_pack.py emojis.json emojis.yaml")
    sys.exit(1)

with open(sys.argv[1]) as f:
    emojis_raw = json.load(f)["emoji"]


emojis_formatted = {}
for emoji_name, url in emojis_raw.items():
    if not url.startswith('alias:'):
        emojis_formatted[emoji_name] = {
            "name": emoji_name,
            "src": url
        }

aliased_emojis = { name: url[len('alias:'):] for name, url in emojis_raw.items() if url.startswith('alias:') }
while aliased_emojis:
    for name, alias in dict(aliased_emojis).items():
        if alias in emojis_formatted:
            if not 'aliases' in emojis_formatted[alias]:
                emojis_formatted[alias]['aliases'] = []
            emojis_formatted[alias]['aliases'].append(name)
        else:
            print("unable to resolve alias for {} to {}".format(name, alias))
        del aliased_emojis[name]

result = {}
result["title"] = "per"
result["emojis"] = [emoji for emoji in emojis_formatted.values()]

with open(sys.argv[2], "w") as f:
    yaml.dump(result, f)
