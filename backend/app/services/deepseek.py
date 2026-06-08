import json
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger("app.services.deepseek")


class DeepSeekService:
    @staticmethod
    async def generate_reviews(commerce_name: str, tags: list[str]) -> list[str]:
        # If API key is not configured, trigger fallback immediately
        if not settings.DEEPSEEK_API_KEY:
            logger.warning("DeepSeek API key is not configured. Using fallback reviews.")
            return DeepSeekService._get_fallback_reviews(tags)

        tags_str = ", ".join(tags)
        prompt = (
            f"Eres un cliente escribiendo una reseña de Google Maps para el comercio '{commerce_name}'. "
            f"Calificación: 5 estrellas. Puntos destacados a incluir: {tags_str}. "
            f"Genera 5 opciones de reseña (Corta, Detallada, Entusiasta, Formal, Casual) en español de España. "
            f"Responde ÚNICAMENTE con un objeto JSON con el siguiente formato exacto, sin bloques de código markdown, sin explicaciones ni textos adicionales:\n"
            f'{{"opciones": ["reseña1", "reseña2", "reseña3", "reseña4", "reseña5"]}}'
        )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}"
        }

        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Eres un redactor de reseñas profesionales. Respondes únicamente en formato JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    "https://api.deepseek.com/chat/completions",
                    headers=headers,
                    json=data
                )
                if response.status_code == 200:
                    res_json = response.json()
                    content = res_json["choices"][0]["message"]["content"]
                    
                    # Clean markdown if returned in text
                    content_clean = content.strip()
                    if content_clean.startswith("```json"):
                        content_clean = content_clean[7:]
                    if content_clean.endswith("```"):
                        content_clean = content_clean[:-3]
                    content_clean = content_clean.strip()

                    parsed = json.loads(content_clean)
                    if isinstance(parsed, dict) and "opciones" in parsed:
                        opciones = parsed["opciones"]
                        if isinstance(opciones, list) and len(opciones) > 0:
                            # Clean and return exactly 5 options
                            return [str(opt).strip() for opt in opciones[:5]]
                else:
                    logger.error(f"DeepSeek API returned status code {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Exception calling DeepSeek API: {e}")

        # If anything fails, return fallback templates
        return DeepSeekService._get_fallback_reviews(tags)

    @staticmethod
    def _get_fallback_reviews(tags: list[str]) -> list[str]:
        tags_lower = [t.lower() for t in tags]
        tags_str = ", ".join(tags_lower) if tags_lower else "todo en general"
        
        return [
            f"Excelente atención y {tags_str}. Totalmente recomendado.",
            f"Me encantó el lugar, especialmente por {tags_str}. Volveremos seguro.",
            f"Un sitio increíble en la zona. Destaco {tags_str}. 10/10.",
            f"Muy buena experiencia. Destaco {tags_str}, hicieron que valiera la pena.",
            f"Todo perfecto, desde el trato hasta {tags_str}. Sitio de referencia."
        ]
