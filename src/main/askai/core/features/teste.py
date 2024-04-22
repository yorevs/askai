import logging as log

from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.tools.commons import log_init
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.features.actions import features
from askai.core.support.langchain_support import lc_llm
from askai.core.support.shared_instances import shared

if __name__ == "__main__":
    human_prompt = "{input}\n\n{agent_scratchpad}\n (reminder to respond in a JSON blob no matter what)"
    log_init("/Users/hjunior/.config/hhs/log/agent.log", level=log.INFO)
    cache.read_query_history()
    shared.create_engine(engine_name="openai", model_name="gpt-3.5-turbo")
    shared.create_context(4000)
    template: PromptTemplate = PromptTemplate(input_variables=[
        "os_type", "user"
    ], template=prompt.read_prompt("router.txt"))
    system_prompt: str = template.format(
        os_type=prompt.os_type, user=prompt.user
    )
    router_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", human_prompt),
        ]
    )
    llm = lc_llm.create_chat_model()

    conversational_memory = ConversationBufferWindowMemory(memory_key="chat_history", k=5, return_messages=True)

    re_agent = create_structured_chat_agent(llm, features.agent_tools(), router_prompt)
    agent = AgentExecutor(
        agent=re_agent,
        tools=features.agent_tools(),
        verbose=True,
        max_iteraction=3,
        memory=conversational_memory,
        handle_parsing_errors=True,
    )

    while (query := line_input("> ")) not in ["", "q"]:
        resp = agent.invoke({"input": query})
        print(resp)

    cache.save_query_history()
