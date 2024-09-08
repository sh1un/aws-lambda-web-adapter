async function generateAIResponse() {
  // Get input values from the form
  const model = document.getElementById("model").value;
  const system = document.getElementById("system").value;
  const userMessage = document.getElementById("user-message").value;
  const maxTokens = document.getElementById("max-tokens").value;
  const temperature = document.getElementById("temperature").value;

  if (userMessage.trim().length === 0) {
    return;
  }

  const storyOutput = document.getElementById("story-output");
  storyOutput.innerText = "Thinking...";

  try {
    // Create request payload
    const requestBody = {
      model: model,
      system: system,
      messages: [{
        role: 'user',
        content: userMessage
      }],
      max_tokens: parseInt(maxTokens),
      temperature: parseFloat(temperature),
      stream: true
    };

    // Use Fetch API to send a POST request for response streaming
    const response = await fetch("/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestBody)
    });

    storyOutput.innerText = "";

    // Response Body is a ReadableStream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    // Process the chunks from the stream
    while (true) {
      const {
        done,
        value
      } = await reader.read();
      if (done) {
        break;
      }
      const text = decoder.decode(value);
      storyOutput.innerText += text;
    }

  } catch (error) {
    storyOutput.innerText = `Sorry, an error happened. Please try again later. \n\n ${error}`;
  }
}

document.getElementById("generate-response").addEventListener("click", generateAIResponse);
document.getElementById('user-message').addEventListener('keydown', function (e) {
  if (e.code === 'Enter') {
    generateAIResponse();
  }
});