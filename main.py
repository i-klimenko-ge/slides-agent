from langchain_core.messages import HumanMessage, AIMessage
from colorama import init, Fore, Style, Back
from graph import graph

if __name__ == '__main__':
    conversation = {"messages": [], "current_slide": None}
    print("Чем могу помочь?")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ('exit', 'quit'):
            print("Goodbye!")
            break

        first_human_message = HumanMessage(content=user_input)
        # Add the user's message as a HumanMessage
        conversation["messages"].append(first_human_message)

        # Stream through the agent
        stream = graph.stream(conversation, stream_mode="values")

        # Collect assistant messages
        for step in stream:
            msg = step["messages"][-1]
            try:
                # TODO: for first and last message. Maybe it shold made another way
                if msg in conversation["messages"]:
                    continue

                if isinstance(msg, AIMessage):
                    print(f"{Fore.YELLOW}{msg.content}{Style.RESET_ALL}")
                else:
                    msg.pretty_print()
                conversation["messages"].append(msg)
                if step.get("current_slide") is not None:
                    conversation["current_slide"] = step["current_slide"]
            except AttributeError:                print(msg)
