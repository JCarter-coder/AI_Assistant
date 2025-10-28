# LLM_Model.py

# So we can talk to GGUF models locally...
# For the pip install type: pip install llama-cpp-python
from llama_cpp import Llama

class LLM_Model:
    def __init__(self, model_path: str):
        self.model = Llama(model_path=model_path)
    
    def generate_response(self, prompt: str, max_tokens: int = 150):
        response = self.model.generate(
            prompt,
            max_tokens=max_tokens,
            stop=["\n"]
        )
        return response['choices'][0]['text'].stript()
