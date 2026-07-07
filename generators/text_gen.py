from generators.gigachat_client import chat_completion


class PostGenerator:
    def __init__(self, tone, topic):
        self.tone = tone
        self.topic = topic

    def generate_post(self):
        return chat_completion(
            "Ты высококвалифицированный SMM специалист, который будет помогать "
            "в генерации текста для постов с заданной тематикой и заданным тоном.",
            f"Сгенерируй пост для соцсетей с темой {self.topic}, используя тон: {self.tone}",
        )

    def generate_post_image_description(self):
        return chat_completion(
            "Ты ассистент, который составит промпт для нейросети, "
            "которая будет генерировать изображения. Ты должен составлять промпт на заданную тематику.",
            f"Сгенерируй описание изображения для соцсетей с темой {self.topic}",
        )
