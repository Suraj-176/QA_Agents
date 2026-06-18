import base64
from io import BytesIO
from PIL import Image
import openai
import anthropic
import google.generativeai as genai

class LLMAdapter:
    @staticmethod
    async def generate_text(provider: str, model: str, api_key: str, prompt: str) -> str:
        """Helper to dynamically invoke the correct LLM library for text generation."""
        provider = provider.lower().strip()
        
        if provider == "gemini":
            genai.configure(api_key=api_key)
            model_name = model if model else "gemini-1.5-flash"
            model_instance = genai.GenerativeModel(model_name)
            response = await model_instance.generate_content_async(prompt)
            return response.text

        elif provider == "openai":
            client = openai.AsyncOpenAI(api_key=api_key)
            model_name = model if model else "gpt-4o-mini"
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content

        elif provider == "anthropic":
            client = anthropic.AsyncAnthropic(api_key=api_key)
            model_name = model if model else "claude-3-5-sonnet-20241022"
            response = await client.messages.create(
                model=model_name,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    @staticmethod
    async def analyze_image(provider: str, model: str, api_key: str, prompt: str, image_bytes: bytes) -> str:
        """Helper to dynamically invoke the correct LLM library for multi-modal Vision queries."""
        provider = provider.lower().strip()
        
        if provider == "gemini":
            genai.configure(api_key=api_key)
            model_name = model if model else "gemini-1.5-flash"
            model_instance = genai.GenerativeModel(model_name)
            
            # Convert bytes to PIL Image for Gemini SDK compatibility
            img = Image.open(BytesIO(image_bytes))
            response = await model_instance.generate_content_async([prompt, img])
            return response.text

        elif provider == "openai":
            client = openai.AsyncOpenAI(api_key=api_key)
            model_name = model if model else "gpt-4o"
            
            # Encode image to Base64 data url
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = await client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2
            )
            return response.choices[0].message.content

        elif provider == "anthropic":
            client = anthropic.AsyncAnthropic(api_key=api_key)
            model_name = model if model else "claude-3-5-sonnet-20241022"
            
            # Encode image to Base64
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = await client.messages.create(
                model=model_name,
                max_tokens=4000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            },
                            {"type": "text", "text": prompt}
                        ]
                    }
                ],
                temperature=0.2
            )
            return response.content[0].text

        else:
            raise ValueError(f"Unsupported vision LLM provider: {provider}")
