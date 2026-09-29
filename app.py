"""Entry point for Hugging Face Spaces (Gradio SDK).

Spaces runs `python app.py` and serves whatever listens on port 7860,
so this starts the FastAPI app there. A tiny Gradio page is mounted at
/gradio because Gradio Spaces expect Gradio to be in use.
"""

import os

# Spaces turns on Gradio's server-side rendering, which starts a Node
# server on port 7860 and blocks uvicorn. FitBuddy doesn't need it.
os.environ["GRADIO_SSR_MODE"] = "False"

import gradio as gr
import uvicorn

from app.main import app

# ZeroGPU hardware refuses to start unless some function requests the GPU.
# FitBuddy doesn't need one, so this placeholder is never called.
try:
    import spaces

    @spaces.GPU
    def _gpu_placeholder():
        pass

    # ZeroGPU registers GPU functions when Gradio's launch() runs. We start
    # uvicorn ourselves instead, so run that registration step directly.
    import spaces.zero

    if hasattr(spaces.zero, "startup"):
        spaces.zero.startup()
except ImportError:
    pass

with gr.Blocks(title="FitBuddy") as status_page:
    gr.Markdown("FitBuddy is running. Open the [home page](/) to use it.")

app = gr.mount_gradio_app(app, status_page, path="/gradio", ssr_mode=False)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860, proxy_headers=True, forwarded_allow_ips="*")
