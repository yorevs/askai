from clitt.core.tui.line_input.line_input import line_input
from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_openai import ChatOpenAI

from askai.core.features.agent.list_tool import ListTool
from askai.core.features.agent.open_tool import OpenTool
from askai.core.features.agent.output_checker_tool import OutputCheckerTool
from askai.core.features.agent.terminal_tool import TerminalTool
from askai.core.features.agent.termination_tool import TerminationTool
from askai.core.features.agent.unintelligible_tool import UnintelligibleTool

if __name__ == '__main__':
    llm = ChatOpenAI(
        temperature=0,
        model_name='gpt-3.5-turbo'
    )
    conversational_memory = ConversationBufferWindowMemory(
        memory_key='chat_history', k=5, return_messages=True)
    tools = [
        TerminationTool(), UnintelligibleTool(), OutputCheckerTool(),
        TerminalTool(), ListTool(), OpenTool()
    ]
    prompt = hub.pull("hwchase17/structured-chat-agent")
    re_agent = create_structured_chat_agent(llm, tools, prompt)
    agent = AgentExecutor(
        agent=re_agent, tools=tools, verbose=True,
        max_iteraction=3, memory=conversational_memory,
        handle_parsing_errors=True)

    while (query := line_input('> ')) != 'q':
        resp = agent.invoke({"input": query})
        print(resp)
