from exif_utils import extract_exif, get_exif_summary
 

exif = extract_exif('data/raw/exif_samples/IMG_0332.jpg')
for key, val in exif.items():
    print(f'{key}: {val}')
 
# Concise summary
summary = get_exif_summary('data/raw/exif_samples/IMG_0332.jpg')
import json
print(json.dumps(summary, indent=2, default=str))
