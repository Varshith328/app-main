import os
import google.generativeai as genai

# Load API key from env
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print('GEMINI_API_KEY not found in environment')
    raise SystemExit(1)

genai.configure(api_key=api_key)

print('Listing models available to this key:')
models = genai.list_models()
for m in models:
    # print model id and supported methods if available
    print('---')
    print('id:', getattr(m, 'name', m.get('name') if isinstance(m, dict) else str(m)))
    try:
        # some responses may include metadata
        print('raw:', m)
    except Exception:
        pass

print('Done')
