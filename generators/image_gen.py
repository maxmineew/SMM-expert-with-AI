from generators.gigachat_client import generate_image_file


class ImageGenerator:
    def generate_image(self, prompt):
        return generate_image_file(prompt)
