import argparse
import os
from transformers import CLIPProcessor, CLIPModel, ViTImageProcessor, ViTModel


def download(model_name: str, cache_dir: str):
    os.makedirs(cache_dir, exist_ok=True)
    print(f"Downloading model and processor for {model_name} into {cache_dir} ...")

    if "clip" in model_name.lower():
        _ = CLIPModel.from_pretrained(model_name, cache_dir=cache_dir)
        _ = CLIPProcessor.from_pretrained(model_name, cache_dir=cache_dir)
    else:
        _ = ViTModel.from_pretrained(model_name, cache_dir=cache_dir)
        _ = ViTImageProcessor.from_pretrained(model_name, cache_dir=cache_dir)

    print("Download complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.environ.get("MODEL_NAME", "google/vit-base-patch16-224"))
    parser.add_argument("--cache-dir", default=os.environ.get("TRANSFORMERS_CACHE", "/models"))
    args = parser.parse_args()
    download(args.model, args.cache_dir)
