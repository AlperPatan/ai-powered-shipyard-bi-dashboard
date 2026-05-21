import google.generativeai as genai

# API anahtarını buraya yapıştır (sadece test için)
API_KEY = "AIzaSyCZA8UzesMimf-6wctCZjAU9nQlWdxG75E"
genai.configure(api_key=API_KEY)

print("Kullanılabilir Modeller Aranıyor...\n")

try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print("Kullanılabilir Model:", m.name)
except Exception as e:
    print("Bir hata oluştu:", e)