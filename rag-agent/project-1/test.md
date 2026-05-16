# Single tool — calculator
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is 15% of 8500?"}'

  # Two tools — weather + calculator
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather in Jakarta, and if humidity is above 80% what is 80% of the current temperature?"}'

  # Knowledge search
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is ReAct and how does it relate to LangChain?"}'


  # List available tools
curl http://localhost:8000/tools