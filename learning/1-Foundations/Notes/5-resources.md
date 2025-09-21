# Resources vs Tools

## Resources

You can provide a Model with Resources to improve it's expertise

    - give extra relevant data inside of the prompt


It's not feasible to always send large prompts with all relevant data

    - techniques like RAG streamline it and allow the model to choose


__RAG:__

    Retrieval Augmented Generation

    - Model has access to a VectorDB
    - The VectorDB contains information in a multi-dimensional array
    - The Model will pick relevant info to your prompt from the VectorDB
    - Uses identifiers on the data to know what info is relevant


## Tools

Give an LLM the power to use a Tool at its own discretion

    - make a SQL call to a database
    - send a call to another LLM do perform a particular task

