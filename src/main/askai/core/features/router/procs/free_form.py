from typing import Optional

from hspylib.core.config.path_object import PathObject
from hspylib.core.metaclass.singleton import Singleton
from langchain_core.prompts import PromptTemplate

from askai.core.askai_events import AskAiEvents
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.engine.openai.temperature import Temperature
from askai.core.support.langchain_support import lc_llm
from askai.core.support.utilities import find_file


class FreeForm(metaclass=Singleton):
    """Processor to provide a answers from custom prompts (free-form)."""

    INSTANCE: "FreeForm"

    DEFAULT_PROMPT: str = f"{prompt.PROMPT_DIR}/taius/taius-non-interactive"

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Process the user question to retrieve the final response.
        :param question: The user question to process.
        """
        context: str | None = kwargs["context"] if "context" in kwargs else "No context has been provided"
        query_prompt: str | None = find_file(kwargs["query_prompt"]) if "query_prompt" in kwargs else None

        dir_name, file_name = PathObject.split(query_prompt or self.DEFAULT_PROMPT)
        template = PromptTemplate(
            input_variables=["context", "question"], template=prompt.read_prompt(file_name, dir_name))
        final_prompt: str =  template.format(context=context, question=question)
        llm = lc_llm.create_chat_model(Temperature.CREATIVE_WRITING.temp)

        if output := llm.invoke(final_prompt):
            AskAiEvents.ASKAI_BUS.events.reply.emit(message=output.content)
            cache.save_query_history()

        return output


assert (free_form := FreeForm().INSTANCE) is not None
