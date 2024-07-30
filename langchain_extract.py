from typing import Optional

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama

# ===== Import list of characteristics =====

charlist = []
with open('char_lists/list_followup.txt', 'r') as fp:
    charlist = fp.read().split(',')

# ===== Define schema =====

# class Species(BaseModel):
#     """Characteristics listed in the description of a plant species."""

#     characteristics: dict[str,str] = Field(
#         default = None, description = "Key-value pairs of the name of each characteristic as the key and the corresponding trait value as the value"
#     )

class Person(BaseModel):
    """Information about a person."""

    # ^ Doc-string for the entity Person.
    # This doc-string is sent to the LLM as the description of the schema Person,
    # and it can help to improve extraction results.

    # Note that:
    # 1. Each field is an `optional` -- this allows the model to decline to extract it!
    # 2. Each field has a `description` -- this description is used by the LLM.
    # Having a good description can help improve extraction results.
    name: Optional[str] = Field(default=None, description="The name of the person")
    hair_color: Optional[str] = Field(
        default=None, description="The color of the person's hair if known"
    )
    height_in_meters: Optional[str] = Field(
        default=None, description="Height measured in meters"
    )

# ===== Define custom prompt =====

# prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
# """
# You are a diligent robot assistant made by a botanist. You have expert knowledge of botanical terminology.
# Your goal is to transcribe the given botanical description of plant characteristics.
# Specifically, you must extract information about the following characteristics:
# fruit color, fruit shape, fruit size
# You must use the names of characteristics exactly as given in the list above.
# If a characteristics is not mentioned in the description, return null.
# """,
#         ),
#         # Please see the how-to about improving performance with
#         # reference examples.
#         # MessagesPlaceholder('examples'),
#         ("human", "{text}"),
#     ]
# )

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert extraction algorithm. "
            "Only extract relevant information from the text. "
            "If you do not know the value of an attribute asked to extract, "
            "return null for the attribute's value.",
        ),
        # Please see the how-to about improving performance with
        # reference examples.
        # MessagesPlaceholder('examples'),
        ("human", "{text}"),
    ]
)

# ===== Extract info with Ollama running on HPC =====

llm = ChatOllama(model = "llama3", temperature = 0)
struct_llm = llm.with_structured_output(schema = Person)
print(struct_llm.invoke("Alan Smith is 6 feet tall and has blond hair."))


runnable = prompt | llm.with_structured_output(schema = Person, include_raw = True)
print(runnable)

text = "Alan Smith is 6 feet tall and has blond hair."
print(runnable.invoke({"text": text}))