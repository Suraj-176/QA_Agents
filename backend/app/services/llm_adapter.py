import os
import base64
import urllib.request
import httpx
from io import BytesIO
from PIL import Image
import openai
import anthropic
import google.generativeai as genai

class LLMAdapter:
    @staticmethod
    async def generate_text(
        provider: str, 
        model: str, 
        api_key: str, 
        prompt: str,
        azure_endpoint: str = None,
        azure_api_version: str = None
    ) -> str:
        """Helper to dynamically invoke the correct LLM library for text generation."""
        provider = provider.lower().strip()
        
        if provider == "gemini":
            genai.configure(api_key=api_key)
            model_name = model if model else "gemini-1.5-flash"
            
            # Configure safety settings to BLOCK_NONE to prevent false-positive blocks on mock test passwords
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Unblock Gemini's full output token limits to prevent truncation on large 5-file scaffolds!
            generation_config = {
                "max_output_tokens": 8192,
                "temperature": 0.2
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings,
                generation_config=generation_config
            )
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

        elif provider == "azure":
            # Support Azure OpenAI natively using standard synchronous clients to prevent win32 asyncio getaddrinfo DNS resolution failures!
            api_key_clean = api_key.strip()
            azure_key = api_key_clean
            
            final_endpoint = azure_endpoint if azure_endpoint else os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            final_api_version = azure_api_version if azure_api_version else os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

            # Backward-compatibility parsing
            if ";" in api_key_clean:
                parts = api_key_clean.split(";")
                for part in parts:
                    if "=" in part:
                        k, v = part.split("=", 2)
                        k_clean = k.strip().lower()
                        v_clean = v.strip()
                        if k_clean in ["apikey", "key"]:
                            azure_key = v_clean
                        elif k_clean in ["endpoint", "url"]:
                            final_endpoint = v_clean
                        elif k_clean in ["apiversion", "version"]:
                            final_api_version = v_clean

            # Automatically extract Windows system proxy registry configurations to bypass corporate firewalls!
            proxies = urllib.request.getproxies()
            http_client = httpx.Client(proxies=proxies) if proxies else None

            client = openai.AzureOpenAI(
                api_key=azure_key,
                azure_endpoint=final_endpoint,
                api_version=final_api_version,
                http_client=http_client
            )
            model_name = model if model else "gpt-4o-mini"
            response = client.chat.completions.create(
                model=model_name, # Maps to Azure deployment name!
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content

        elif provider == "groq":
            # Groq is 100% compatible with OpenAI SDK via base_url overrides!
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            model_name = model if model else "llama-3.3-70b-versatile"
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content

        elif provider == "grok":
            # xAI Grok is 100% compatible with OpenAI SDK via base_url overrides!
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            model_name = model if model else "grok-2-1212"
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content

        elif provider == "openrouter":
            # OpenRouter is 100% compatible with OpenAI SDK via base_url overrides!
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://qa-ai-platform.local",
                    "X-Title": "QA.AI Platform"
                }
            )
            model_name = model if model else "meta-llama/llama-3.3-70b-instruct"
            response = client.chat.completions.create(
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
    async def analyze_image(
        provider: str, 
        model: str, 
        api_key: str, 
        prompt: str, 
        image_bytes: bytes,
        azure_endpoint: str = None,
        azure_api_version: str = None
    ) -> str:
        """Helper to dynamically invoke the correct LLM library for multi-modal Vision queries."""
        provider = provider.lower().strip()
        
        if provider == "gemini":
            genai.configure(api_key=api_key)
            model_name = model if model else "gemini-1.5-flash"
            
            # Configure safety settings to BLOCK_NONE to prevent false-positive blocks on UI screenshot analysis
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            model_instance = genai.GenerativeModel(
                model_name=model_name,
                safety_settings=safety_settings
            )
            
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

        elif provider == "azure":
            # Support Azure OpenAI Vision natively using synchronous client and Windows registry proxy loader!
            api_key_clean = api_key.strip()
            azure_key = api_key_clean
            
            final_endpoint = azure_endpoint if azure_endpoint else os.environ.get("AZURE_OPENAI_ENDPOINT", "")
            final_api_version = azure_api_version if azure_api_version else os.environ.get("AZURE_OPENAI_API_VERSION", "2023-05-15")

            if ";" in api_key_clean:
                parts = api_key_clean.split(";")
                for part in parts:
                    if "=" in part:
                        k, v = part.split("=", 2)
                        k_clean = k.strip().lower()
                        v_clean = v.strip()
                        if k_clean in ["apikey", "key"]:
                            azure_key = v_clean
                        elif k_clean in ["endpoint", "url"]:
                            final_endpoint = v_clean
                        elif k_clean in ["apiversion", "version"]:
                            final_api_version = v_clean

            # Automatically extract Windows system proxy registry configurations to bypass corporate firewalls!
            proxies = urllib.request.getproxies()
            http_client = httpx.Client(proxies=proxies) if proxies else None

            client = openai.AzureOpenAI(
                api_key=azure_key,
                azure_endpoint=final_endpoint,
                api_version=final_api_version,
                http_client=http_client
            )
            model_name = model if model else "gpt-4o"
            
            # Encode image to Base64
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = client.chat.completions.create(
                model=model_name, # Maps to Azure vision deployment name!
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

        elif provider == "groq":
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            model_name = model if model else "llama-3.2-11b-vision-preview"
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = client.chat.completions.create(
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

        elif provider == "grok":
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.x.ai/v1"
            )
            model_name = model if model else "grok-2-vision-1212"
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = client.chat.completions.create(
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

        elif provider == "openrouter":
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={
                    "HTTP-Referer": "https://qa-ai-platform.local",
                    "X-Title": "QA.AI Platform"
                }
            )
            model_name = model if model else "google/gemini-2.5-flash"
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            response = client.chat.completions.create(
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
