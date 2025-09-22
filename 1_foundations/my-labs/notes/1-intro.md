# Foundations: Lab 1

This is a basic intro to:

    1. setup OpenAI imports
    2. send a message to the model
    3. receive and save the response
    4. output the response
    5. use the repsonse in another prompt


## OpenAI Compatibility

Each major LLM has its own Library


But since most are built from OpenAI

    - the OpenAI library can be used for many other models


Most LLM's also follow the OpenAI API standard


## OpenAI API Standardization

To send messasges to a Model, it needs to be formatted

    - dict{"role": <role>, "content": <content>}


Roles include:

    - system
    - user
    - assistant


System Role:

    - For setting how the Model will behave

    - Example: "You are a Python coding instructor. Please answer any questions concisely."


User Role:

    - The prompt to send the Model

    - Example: "Can you please write a bash script to restart NetworkManager?"


Assistant Role:

    - The previous AI responses from the conversation

    - Allows a complete conversation history

    - Example: assistant_response = response.choices[0].message.content


## Example of LLM Interaction

```python
# initial empty list of messages
conversation = []


# create user role content
user_input = "Tell me a joke"
conversation.append(user_input)


# send user's content to model
response = openai.chat.completions.create(
    model="gemma3:12b",
    messages=conversation
)


# save the model's answer & append to message list
assistant_response = response.choices[0].message.content
conversations.append({"role": "assistant", "content": assistant_response})


# output current conversation history
print("Conversation so far:")
for msg in conversation:
    print(f"{msg['role']}: {msg['content']}")


# user follows up
user_input2 = "Tell me another one"
conversation.append({"role": "user", "content": user_input2})


# another API call - now the AI remembers the previous joke
response2 = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=conversation  # Includes the full history
)
```

