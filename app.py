from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import dotenv_values
import gpt4all
import requests
import base64
import os

config = dotenv_values(".env")
api_host = config["API_HOST"]
api_key = config["STABE_DIFFUSION_API_KEY"]
engine_id = config["ENGINE_ID"]

app = Flask(__name__)
CORS(app)


@app.route("/generate", methods=["GET"])
def generate():

    # This will download gpt4all-j v1.3 groovy model, which is ~3.7GB
    gptj = gpt4all.GPT4All("ggml-gpt4all-j-v1.3-groovy")

    request_text = request.args.get("prompt")

    # We create 2 prompts, one for the description and then another one for the name of the product
    prompt_description = 'You are a business consultant. Please write a short description for a product idea for an online shop inspired by the following concept: "' + \
        request_text + '"'
    messages_description = [{"role": "user", "content": prompt_description}]
    description = gptj.chat_completion(messages_description)[
        'choices'][0]['message']['content']

    prompt_name = 'You are a business consultant. Please write a name of maximum 5 words for a product with the following description: "' + request_text + '"'
    messages_name = [{"role": "user", "content": prompt_name}]
    short_description = gptj.chat_completion(
        messages_name
    )['choices'][0]['message']['content']

    print(short_description)

    image_path = generate_image(short_description)
    result = {
        "name": short_description,
        "description": description,
        "image": image_path
    }

    return jsonify(result)


# Calls the Stable Diffusion API and generates an image for a product name
def generate_image(product_name):
    prompt = "Please generate a featured image for the following product idea: " + product_name + \
        ". The product must be showcased in full size at the center of the image, with minimum distractive elements, and a simple monochromatic background."
    url = f"{api_host}/v1/generation/{engine_id}/text-to-image"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {}
    payload['text_prompts'] = [{"text": f"{prompt}"}]
    payload['cfg_scale'] = 7
    payload['clip_guidance_preset'] = 'FAST_BLUE'
    payload['height'] = 512
    payload['width'] = 512
    payload['samples'] = 1
    payload['steps'] = 50
    print("request to stable duffusion")
    response = requests.post(url, headers=headers, json=payload)
    print("response from stable duffusion")
    print(response.status_code)
    filenamestring = product_name.replace(" ", "_")+".png"
    filename = check_and_create_filename(filenamestring)
    image_path = ""

    # Processing the response
    if response.status_code == 200:
        data = response.json()
        for i, image in enumerate(data["artifacts"]):
            with open(f"{filename}", "wb") as f:
                f.write(base64.b64decode(image["base64"]))
                image_path = f"/{filename}"

    return image_path

# Creates a new filename in case it already exists


def check_and_create_filename(filename):
    base_name, extension = os.path.splitext(filename)
    counter = 1
    new_filename = f"static/{filename}"

    while os.path.exists(new_filename):
        new_filename = f"static/{base_name}_{counter}{extension}"
        counter += 1

    return new_filename

# Start an http server and expose the api endpoint


def main():
    app.run(host="localhost", port=8000)
    print("Server running on  port 8000")


if __name__ == "__main__":
    main()
