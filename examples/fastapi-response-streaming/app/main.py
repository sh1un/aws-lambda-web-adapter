import json
import os
from typing import List, Optional

import boto3
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

app.mount("/demo", StaticFiles(directory="static", html=True))


@app.get("/")
async def root():
    return RedirectResponse(url="/demo/")


class Message(BaseModel):
    role: str  # Role can be 'system', 'user', or 'assistant'
    content: str  # The content of the message


class ChatRequest(BaseModel):
    model: str  # Model name provided by the client
    messages: List[Message]  # List of messages with roles and content
    temperature: Optional[float] = 0.5  # Optional, default temperature is 0.5
    stream: Optional[bool] = True  # Enable streaming by default


@app.post("/api/v1/chat/completions")
def api_chat_completion(chat_request: ChatRequest):
    if not chat_request.messages:
        return {"error": "Messages are required"}

    # Construct the payload including required fields like max_tokens and anthropic_version
    body = {
        "max_tokens": 1024,  # Required by Bedrock API
        "anthropic_version": "bedrock-2023-05-31",  # Required by Bedrock API
        "messages": [
            {"role": msg.role, "content": msg.content} for msg in chat_request.messages
        ],
        "temperature": chat_request.temperature,
    }

    return StreamingResponse(
        bedrock_stream(chat_request.model, body), media_type="text/html"
    )


bedrock = boto3.client("bedrock-runtime")


async def bedrock_stream(model_id: str, body: dict):
    # Convert the dictionary into a JSON string
    body_str = json.dumps(body)

    # Send the model ID from the request and the body to Bedrock
    response = bedrock.invoke_model_with_response_stream(
        modelId=model_id,  # Model name provided in the request body
        body=body_str,
    )

    stream = response.get("body")
    if stream:
        for event in stream:
            chunk = event.get("chunk")
            if chunk:
                message = json.loads(chunk.get("bytes").decode())
                if message["type"] == "content_block_delta":
                    # Stream the content back to the client
                    yield message["delta"]["text"] or ""
                elif message["type"] == "message_stop":
                    # Indicate the end of the message
                    yield "\n"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
