import argparse
from mlx_lm.server import APIHandler, load_model
from http.server import HTTPServer
import json

# Wrapper to make mlx_lm server behave like OpenAI
# mlx-lm has a built-in server in recent versions!
# We can just run: python -m mlx_lm.server --model models/softskill-llama3.2-3b

if __name__ == "__main__":
    print("Please run this server using the command:")
    print("python -m mlx_lm.server --model models/softskill-llama3.2-3b --port 8080")
