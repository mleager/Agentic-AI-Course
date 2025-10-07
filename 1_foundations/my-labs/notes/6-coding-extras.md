# Coding Patterns and Implementations used in this Section

## Using globals() to get a Function name and call it with Arguments

Original Code from: 4_lab4.ipynb

```python
def handle_tool_calls(tool_calls):
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        tool = globals().get(tool_name)
        result = tool(**arguments) if tool else {}
        
        results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
    return results
```

This only works because the functions are global

- record_user_details & record_unknown_question


Normally these would be class methods, so calling globals() wouldn't work

### Option 1: Create a Dictionary of { ToolName: Function }

```python
def handle_tool_calls(tool_calls):

    tool_methods = {
        "record_user_details": self.class.record_user_details,
        "record_unknown_question": self.class.record_unknown_question
    }

    # ...omitted for brevity...

    tool_name = tool_call.function.name

    tool_method = tool_methods.get(tool_name, None)
    if tool_method:
        tool = tool_name(**arguments)
```

### Option 2: Use the hasattr() to confirm the Class has the attribute (or method)

```python
def handle_tool_calls(tools_list):
    
    # ...omitted for brevity...

    tool_name = tool_call.function.name

    if hasattr(self.class, tool_name):
        tool = getattr(self.class, tool_name)
        result = tool(**arguments)
```
