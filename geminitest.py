import google.generativeai as genai

# Gemini Credentials
genai.configure(api_key="AIzaSyACJoyvGdD4XSe_DX4smQWzUQ9seMpc898")
model = genai.GenerativeModel("gemini-1.5-flash")
text: str = 'essay on flowers'
response = model.generate_content(text)
print(response.text)